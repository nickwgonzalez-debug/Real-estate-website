#!/usr/bin/env python3
"""Format the daily blog approval email from a drafts folder.

Usage: python3 scripts/approval_email.py content/drafts/YYYY-MM-DD [--note "text"]
Writes approval_email.html and approval_email.txt next to the drafts and prints the subject line.
"""

import html
import os
import re
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_blog as b  # noqa: E402

STYLE = {
    "wrap": "font-family:Arial,Helvetica,sans-serif;color:#1c1f24;max-width:720px;line-height:1.55;",
    "box": "background:#f6f5f3;border-left:4px solid #b40101;padding:12px 16px;margin:12px 0;",
    "hr": "border:0;border-top:2px solid #e6e8eb;margin:32px 0;",
    "tag": "display:inline-block;background:#fbeaea;color:#b40101;font-size:12px;font-weight:bold;padding:2px 8px;border-radius:10px;",
    "table": "border-collapse:collapse;width:100%;font-size:14px;",
    "cell": "border-bottom:1px solid #e6e8eb;padding:6px 8px;text-align:left;",
}


def main():
    folder = sys.argv[1].rstrip("/")
    note = sys.argv[sys.argv.index("--note") + 1] if "--note" in sys.argv else ""
    day = date.fromisoformat(os.path.basename(folder))
    files = sorted(f for f in os.listdir(folder) if f.endswith(".md"))
    posts = [(f[:2], b.parse_post(os.path.join(folder, f))) for f in files]

    subject = f"[Blog Approval] {len(posts)} drafts for {day.strftime('%A, %B %-d, %Y')}"
    how = ("Reply to this email with one of: APPROVE ALL | APPROVE 1, 3, 7 | REJECT 4 | "
           "EDIT 2: <what to change>. Plain English works too. Approved posts go live at the next "
           "check (weekdays about 6am, noon, and 5pm Utah time).")

    # ----- HTML -----
    h = [f'<div style="{STYLE["wrap"]}">',
         f'<h2 style="margin:0 0 4px;">Blog drafts for {day.strftime("%A, %B %-d")}</h2>',
         f'<div style="{STYLE["box"]}"><strong>How to approve:</strong> {html.escape(how)}</div>']
    if note:
        h.append(f'<p><strong>Note:</strong> {html.escape(note)}</p>')
    h.append(f'<table style="{STYLE["table"]}"><tr>'
             + "".join(f'<th style="{STYLE["cell"]}">{c}</th>' for c in ("#", "Category", "Title", "Words")) + "</tr>")
    for num, p in posts:
        wc = b.words(p["body_md"]) + b.words(p["summary"])
        h.append("<tr>" + "".join(f'<td style="{STYLE["cell"]}">{c}</td>' for c in
                                  (int(num), html.escape(p["category"]), html.escape(p["title"]), wc)) + "</tr>")
    h.append("</table>")
    for num, p in posts:
        issues = b.check_post(p)
        h.append(f'<hr style="{STYLE["hr"]}">')
        h.append(f'<p><span style="{STYLE["tag"]}">#{int(num)} &middot; {html.escape(p["category"])}</span></p>')
        h.append(f'<h2 style="margin:4px 0;">{html.escape(p["title"])}</h2>')
        h.append(f'<p style="color:#5f6670;font-size:13px;margin:0;">Meta description: {html.escape(p["description"])}</p>')
        h.append(f'<div style="{STYLE["box"]}"><strong>Quick Answer:</strong> {b.inline(p["summary"])}</div>')
        body = b.md_to_html(p["body_md"])
        body = re.sub(r'<a href="(?!http)[^"]*">(.*?)</a>', r"<u>\1</u>", body)  # site-relative links don't work in email
        body = body.replace("<table>", f'<table style="{STYLE["table"]}">')
        body = re.sub(r"<(t[hd])>", lambda m: f'<{m.group(1)} style="{STYLE["cell"]}">', body)
        h.append(body)
        if issues:
            h.append("<p><strong>Format check issues:</strong></p><ul>"
                     + "".join(f"<li>{html.escape(i)}</li>" for i in issues) + "</ul>")
    h.append(f'<hr style="{STYLE["hr"]}"><p style="color:#5f6670;font-size:13px;">'
             "Sent by your blog routine. Drafts are saved in the website repository and are not public until approved.</p></div>")

    # ----- Plain text -----
    t = [subject, "", "HOW TO APPROVE", how, ""]
    if note:
        t += [f"NOTE: {note}", ""]
    t.append("DRAFTS")
    for num, p in posts:
        t.append(f"{int(num)}. [{p['category']}] {p['title']}")
    for num, p in posts:
        plain = re.sub(r"^#{2,4}\s+", "", p["body_md"], flags=re.M)
        plain = re.sub(r"\*\*(.+?)\*\*", r"\1", plain)
        plain = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", plain)
        t += ["", "-" * 60, f"#{int(num)}  {p['title']}", "",
              f"QUICK ANSWER: {b.strip_md(p['summary'])}", "", plain]

    with open(os.path.join(folder, "approval_email.html"), "w", encoding="utf-8") as f:
        f.write("\n".join(h))
    with open(os.path.join(folder, "approval_email.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(t))
    print(subject)


if __name__ == "__main__":
    main()
