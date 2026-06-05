"""
Node: link_review (HITL gate #1)
Pauses the pipeline so the user can select/deselect links before research runs.
"""
import time
import concurrent.futures
from state import emit, pipeline_states
from pipeline.nodes.research import is_youtube, is_linkedin, is_github
from pipeline.mcps.youtube import fetch_youtube_transcript
from pipeline.mcps.fetch import fetch_web_article
from pipeline.mcps.linkedin import fetch_linkedin_post
from pipeline.mcps.deepwiki import fetch_github_summary


def _extract_links_from_notes(notes: list) -> list:
    all_links = []
    seen = set()
    for note in notes:
        for link in note.get("links", []):
            if link not in seen:
                seen.add(link)
                all_links.append({
                    "url": link,
                    "source_text": note["text"][:120],
                    "date": note["date"],
                })
    return all_links


def _check_single_link(link_item: dict) -> tuple:
    url = link_item["url"]
    try:
        if is_youtube(url):
            res = fetch_youtube_transcript(url)
        elif is_linkedin(url):
            res = fetch_linkedin_post(url)
        elif is_github(url):
            res = fetch_github_summary(url)
        else:
            res = fetch_web_article(url)
        return link_item, True, res, None
    except Exception as e:
        return link_item, False, None, str(e)


def _crawl_links_in_parallel(all_links: list, run_id: str) -> dict:
    research_cache = {}
    LINK_CHECK_TIMEOUT = 30
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(all_links), 5)) as executor:
        future_to_item = {executor.submit(_check_single_link, item): item for item in all_links}
        for fut in concurrent.futures.as_completed(future_to_item, timeout=LINK_CHECK_TIMEOUT * len(all_links)):
            try:
                item, crawlable, res, err = fut.result(timeout=LINK_CHECK_TIMEOUT)
            except concurrent.futures.TimeoutError:
                item = future_to_item[fut]
                crawlable, res, err = False, None, "Timed out after 30s"
            except Exception as e:
                item = future_to_item[fut]
                crawlable, res, err = False, None, str(e)
            
            item["crawlable"] = crawlable
            if crawlable:
                research_cache[item["url"]] = res
                emit(run_id, {"type": "step", "step": "link_review", "status": "in_progress",
                              "message": f"✅ Crawled: {item['url'][:80]}"})
            else:
                item["error_message"] = err
                emit(run_id, {"type": "step", "step": "link_review", "status": "in_progress",
                               "message": f"⚠️ Uncrawlable: {item['url'][:80]} — {err[:60]}"})
    return research_cache


def _poll_user_link_selection(run_id: str, all_links: list) -> tuple:
    deadline = time.time() + 600
    while time.time() < deadline:
        s = pipeline_states.get(run_id, {})
        if s.get("cancelled"):
            emit(run_id, {"type": "error", "message": "Pipeline cancelled manually."})
            raise ValueError("Pipeline cancelled manually.")

        if not s.get("awaiting_link_selection"):
            selected = s.get("selected_links", [link["url"] for link in all_links if link.get("crawlable") != False])
            include_uncrawlable = s.get("include_uncrawlable", False)
            return selected, include_uncrawlable

        time.sleep(0.5)

    selected = [link["url"] for link in all_links if link.get("crawlable") != False]
    return selected, False


def link_review_node(state: dict) -> dict:
    run_id = state["run_id"]
    notes  = state["notes"]

    all_links = _extract_links_from_notes(notes)

    if len(all_links) == 0:
        emit(run_id, {"type": "error", "message": "Zero links obtained. Pipeline automatically cancelled."})
        raise ValueError("Zero links obtained.")

    emit(run_id, {
        "type": "step", "step": "link_review", "status": "in_progress",
        "message": f"🔗 Pre-checking crawlability for {len(all_links)} links...",
    })

    research_cache = _crawl_links_in_parallel(all_links, run_id)

    if state.get("trigger") == "cron":
        selected = [link["url"] for link in all_links if link.get("crawlable") != False]
        emit(run_id, {
            "type": "step", "step": "link_review", "status": "done",
            "detail": f"Auto-selected all {len(selected)} crawlable links (Cron Run)",
        })
        return {
            **state,
            "selected_links": selected,
            "include_uncrawlable": False,
            "uncrawlable_links": [link["url"] for link in all_links if link.get("crawlable") == False],
            "research_cache": research_cache,
        }

    emit(run_id, {
        "type": "step", "step": "link_review", "status": "awaiting",
        "message": f"🔗 {len(all_links)} links found — review and select which to research",
        "links": all_links,
    })

    s = pipeline_states[run_id]
    s["awaiting_link_selection"] = True
    s["all_links"] = all_links
    s["research_cache"] = research_cache

    selected, include_uncrawlable = _poll_user_link_selection(run_id, all_links)
    
    emit(run_id, {
        "type": "step", "step": "link_review", "status": "done",
        "detail": f"{len(selected)} links selected for research",
    })
    
    return {
        **state,
        "selected_links": selected,
        "include_uncrawlable": include_uncrawlable,
        "uncrawlable_links": [link["url"] for link in all_links if link.get("crawlable") == False],
        "research_cache": research_cache,
    }
