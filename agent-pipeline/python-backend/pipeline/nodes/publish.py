"""
Node: publish
Pushes newsletter to GitHub Pages via REST API + sends via Gmail MCP.
"""
import os, base64, time
from datetime import datetime, timezone
from state import emit
import httpx


def publish_node(state: dict) -> dict:
    run_id     = state["run_id"]
    newsletter = state["newsletter"]

    trigger = state.get("trigger", "manual")
    url = None

    if trigger == "cron":
        emit(run_id, {
            "type": "step", "step": "publish", "status": "in_progress",
            "message": "🚀 Skipping GitHub Pages publishing (Cron Run)...",
        })
    else:
        emit(run_id, {
            "type": "step", "step": "publish", "status": "in_progress",
            "message": "🚀 Publishing to GitHub Pages...",
        })

        owner    = os.environ.get("GITHUB_OWNER", "your-username")
        repo     = os.environ.get("GITHUB_REPO", "ai-pulse-newsletter")
        
        import hashlib, re
        
        topic = state.get("topic", "Newsletter")
        date_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        links_str = "".join(sorted(state.get("selected_links", [])))
        links_hash = hashlib.md5(links_str.encode()).hexdigest()[:6]
        topic_slug = re.sub(r'[^a-z0-9]+', '-', topic.lower()).strip("-") or "newsletter"
        
        filename = f"{topic_slug}-{date_str}-{links_hash}.md"
        token    = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN")

        if not token:
            emit(run_id, {
                "type": "error", "tool": "GitHub Pages", "status": "error",
                "message": "No GITHUB_PERSONAL_ACCESS_TOKEN provided. Cannot publish.",
            })
            raise ValueError("No GITHUB_PERSONAL_ACCESS_TOKEN provided.")
        
        url = _push_to_github(owner, repo, filename, newsletter, token)
        now = datetime.now(timezone.utc)
        date_formatted = now.strftime(f'%B {now.day}, %Y')
        display_title = f"{topic} - {date_formatted}"
        _update_github_index(owner, repo, filename, display_title, token)
        emit(run_id, {
            "type": "mcp_call", "tool": "GitHub Pages", "status": "success",
            "detail": f"Published → {url}",
        })

    from state import pipeline_states

    emails_str = pipeline_states[run_id].get("emails", "")
    if emails_str.strip():
        emails_list = [e.strip() for e in emails_str.split(",") if e.strip()]
        gmail_user = os.environ.get("GMAIL_USER")
        gmail_pass = os.environ.get("GMAIL_APP_PASSWORD")
        if gmail_user and gmail_pass:
            import smtplib
            from email.mime.text import MIMEText
            msg = MIMEText(newsletter, "plain")
            msg["Subject"] = "AI Pulse Weekly Digest"
            msg["From"] = gmail_user
            msg["To"] = ", ".join(emails_list)
            
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(gmail_user, gmail_pass)
                server.send_message(msg)
            
            emit(run_id, {
                "type": "mcp_call", "tool": "Gmail MCP", "status": "success",
                "detail": f"Real email dispatched to {len(emails_list)} subscriber(s).",
            })
        else:
            emit(run_id, {
                "type": "error", "message": "GMAIL_USER or GMAIL_APP_PASSWORD not set. Cannot send real emails.",
            })
            raise ValueError("Gmail credentials not provided.")
    else:
        emit(run_id, {
            "type": "mcp_call", "tool": "Gmail MCP", "status": "warn",
            "detail": "No subscribed emails provided. Skipped sending emails.",
        })

    emit(run_id, {"type": "step", "step": "publish", "status": "done"})
    emit(run_id, {
        "type": "complete",
        "message": "🎉 Pipeline complete!",
        "githubUrl": url,
    })
    return {**state}


def _push_to_github(owner, repo, filename, content, token):
    api = f"https://api.github.com/repos/{owner}/{repo}/contents/newsletters/{filename}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }

    # Check if file exists and get content to compare
    sha = None
    r = httpx.get(api, headers=headers)
    if r.status_code == 200:
        data = r.json()
        sha = data.get("sha")
        try:
            existing_content = base64.b64decode(data.get("content", "")).decode("utf-8")
            if existing_content.replace("\r", "") == content.replace("\r", ""):
                # File exists and content is identical; skip pushing duplicate commit
                return f"https://{owner}.github.io/{repo}/newsletters/{filename}"
        except Exception:
            pass

    encoded = base64.b64encode(content.encode()).decode()
    body = {"message": f"📰 Auto-publish newsletter: {filename}",
            "content": encoded, "branch": "main"}
    if sha:
        body["sha"] = sha

    r = httpx.put(api, headers=headers, json=body)
    r.raise_for_status()
    return f"https://{owner}.github.io/{repo}/newsletters/{filename}"


def _update_github_index(owner, repo, filename, topic, token):
    api = f"https://api.github.com/repos/{owner}/{repo}/contents/index.html"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    
    sha = None
    r = httpx.get(api, headers=headers)
    if r.status_code == 200:
        data = r.json()
        sha = data.get("sha")
        html_content = base64.b64decode(data.get("content", "")).decode("utf-8")
    else:
        html_content = "<!DOCTYPE html>\n<html>\n<head><title>AI Pulse Newsletters</title></head>\n<body>\n<h1>AI Pulse Newsletters</h1>\n<ul>\n</ul>\n</body>\n</html>"
    
    original_html_content = html_content
    
    filename_no_ext = filename.rsplit('.', 1)[0]
    import re
    
    # Exclude the current file's line to handle reruns
    lines = html_content.splitlines()
    other_html = "\n".join([line for line in lines if f"newsletters/{filename_no_ext}" not in line])
    
    # Calculate version if this topic + date already exists
    pattern = rf'>{re.escape(topic)}(?:\s*\(Version\s*(\d+)\))?\s*</a>'
    matches = re.findall(pattern, other_html)
    if matches:
        versions = []
        for m in matches:
            if m == "":
                versions.append(1)
            else:
                versions.append(int(m))
        next_version = max(versions) + 1
        final_topic = f"{topic} (Version {next_version})"
    else:
        final_topic = topic

    # Determine the indentation and attributes of existing li elements if possible
    match = re.search(r'^([ \t]*)<li([^>]*)>', html_content, re.MULTILINE)
    if match:
        indent = match.group(1)
        li_attrs = match.group(2)
        new_link = f"{indent}<li{li_attrs}><a href=\"newsletters/{filename_no_ext}\">{final_topic}</a></li>"
    else:
        # Fallback to detecting ul's indentation or using standard 6 spaces
        match_ul = re.search(r'^([ \t]*)<ul>', html_content, re.MULTILINE)
        indent = (match_ul.group(1) + "  ") if match_ul else "      "
        new_link = f'{indent}<li class="newsletter-item"><a href="newsletters/{filename_no_ext}">{final_topic}</a></li>'

    # Check if the link already exists in index.html (matching with or without .md extension)
    existing_pattern = rf'^[ \t]*<li[^>]*><a[^>]*href=["\']newsletters/{re.escape(filename_no_ext)}(\.md)?["\'][^>]*>.*?</a></li>'
    if re.search(existing_pattern, html_content, re.MULTILINE):
        # Link exists. Replace it with the newly formatted one to correct/update it.
        html_content = re.sub(existing_pattern, new_link, html_content, flags=re.MULTILINE)
    else:
        # Link does not exist. Insert it at the top of the list.
        if "<ul>" in html_content:
            html_content = html_content.replace("<ul>", f"<ul>\n{new_link}")
        else:
            html_content += f"\n<ul>\n{new_link}\n</ul>"
        
    if html_content.replace("\r", "") == original_html_content.replace("\r", ""):
        # Content did not change (e.g. rerun with identical formatted links); skip pushing duplicate commit
        return

    encoded = base64.b64encode(html_content.encode("utf-8")).decode()
    body = {"message": f"🌐 Update index.html with {final_topic}", "content": encoded, "branch": "main"}
    if sha:
        body["sha"] = sha
        
    r = httpx.put(api, headers=headers, json=body)
    r.raise_for_status()
