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
        repo     = os.environ.get("GITHUB_REPO", "sakthis-corner-newsletter")
        
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
        display_title = f"{topic} - {date_str} (Hash: {links_hash})"
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
            msg["Subject"] = "Sakthi's Corner Weekly Digest"
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
    encoded = base64.b64encode(content.encode()).decode()

    # Check if file exists (get SHA for update)
    sha = None
    r = httpx.get(api, headers=headers)
    if r.status_code == 200:
        sha = r.json().get("sha")

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
        html_content = "<!DOCTYPE html>\n<html>\n<head><title>Sakthi's Corner Newsletters</title></head>\n<body>\n<h1>Sakthi's Corner Newsletters</h1>\n<ul>\n</ul>\n</body>\n</html>"
    
    new_link = f'<li><a href="newsletters/{filename}">{topic}</a></li>'
    if f"newsletters/{filename}" in html_content:
        # File already exists in the index, no need to add duplicate link
        return
        
    if "<ul>" in html_content:
        html_content = html_content.replace("<ul>", f"<ul>\n  {new_link}")
    else:
        html_content += f"\n<ul>\n  {new_link}\n</ul>"
        
    encoded = base64.b64encode(html_content.encode("utf-8")).decode()
    body = {"message": f"🌐 Update index.html with {topic}", "content": encoded, "branch": "main"}
    if sha:
        body["sha"] = sha
        
    r = httpx.put(api, headers=headers, json=body)
    r.raise_for_status()
