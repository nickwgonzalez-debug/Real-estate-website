#!/usr/bin/env python3
"""Build the blog from Markdown sources.

Reads content/posts/*.md and writes:
  - blog/<slug>.html   one page per post (with BlogPosting, FAQPage and Breadcrumb JSON-LD)
  - blog.html          the blog index, newest first
  - llms.txt           a plain-text map of the site for AI assistants
  - sitemap.xml        only when SITE_URL is set

Usage:
  python3 scripts/build_blog.py                  build the site from content/posts/
  python3 scripts/build_blog.py --check FILE...  check drafts against the length/format rules
Standard library only.
"""

import html
import json
import os
import re
import sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS_DIR = os.path.join(ROOT, "content", "posts")
BLOG_DIR = os.path.join(ROOT, "blog")

# Set this to the live domain (e.g. "https://www.nickgonzalezrealtor.com") once the site is hosted.
# Canonical URLs and sitemap.xml are only generated when it is set.
SITE_URL = ""

AUTHOR = {
    "name": "Nick Gonzalez",
    "title": "Realtor",
    "brokerage": "Keller Williams",
    "instagram": "https://www.instagram.com/nickgonzalezrealtor/",
}
AREAS = ["Riverton", "Bluffdale", "Salt Lake County", "Utah"]

DEFAULT_IMAGES = [
    "https://images.unsplash.com/photo-1570129477492-45c003edd2be?auto=format&fit=crop&w=1200&q=70",
    "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1200&q=70",
    "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?auto=format&fit=crop&w=1200&q=70",
    "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=1200&q=70",
]

IG_ICON = ('<svg class="ig-icon" viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="3" width="18" height="18" '
           'rx="5" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="12" cy="12" r="4" fill="none" '
           'stroke="currentColor" stroke-width="2"/><circle cx="17.5" cy="6.5" r="1.2" fill="currentColor"/></svg>')


# Length and format targets for AI answer engines (ChatGPT, Perplexity, Google AI Overviews, Claude)
# and classic search. Answer engines lift short, self-contained passages, so the direct answer,
# each section, and each FAQ answer must stand on their own at these sizes.
LIMITS = {
    "title_chars": (20, 70),        # full question, fits search result titles
    "description_chars": (120, 160),
    "summary_words": (40, 60),      # the Quick Answer: the passage most likely to be quoted
    "body_words": (900, 1500),      # whole post, including takeaways and FAQ
    "takeaways": (3, 5),
    "takeaway_words": (6, 30),
    "sections": (4, 8),             # H2 sections in the body (question-style headings)
    "section_words": (60, 300),     # each section is a self-contained chunk
    "faqs": (3, 5),
    "faq_answer_words": (25, 70),
}


def words(s):
    return len(re.findall(r"[A-Za-z0-9$%][\w'$%.,-]*", strip_md(s)))


def check_post(p):
    """Return a list of rule violations for a parsed post."""
    issues = []

    def rng(label, key, val):
        lo, hi = LIMITS[key]
        if not lo <= val <= hi:
            issues.append(f"{label}: {val} (target {lo}-{hi})")

    rng("title characters", "title_chars", len(p["title"]))
    rng("description characters", "description_chars", len(p["description"]))
    rng("quick answer words", "summary_words", words(p["summary"]))
    rng("total words", "body_words", words(p["body_md"]) + words(p["summary"]))
    takeaways, faqs, body = split_sections(p["body_md"])
    rng("key takeaways", "takeaways", len(takeaways))
    for t in takeaways:
        rng(f"takeaway '{t[:40]}...' words", "takeaway_words", words(t))
    sections = re.split(r"^##\s+", body, flags=re.M)[1:]
    rng("body sections (##)", "sections", len(sections))
    for sec in sections:
        heading, _, text = sec.partition("\n")
        rng(f"section '{heading[:40]}' words", "section_words", words(text))
        if not heading.strip().endswith("?"):
            issues.append(f"section '{heading[:40]}' heading should be phrased as a question")
    rng("FAQ questions", "faqs", len(faqs))
    for q, a in faqs:
        rng(f"FAQ '{q[:40]}' answer words", "faq_answer_words", words(a))
    if "?" not in p["title"]:
        issues.append("title should be phrased as the question people ask")
    text = (p["title"] + " " + p["body_md"] + " " + p["summary"]).lower()
    for place in ("utah", "salt lake county"):
        if place not in text:
            issues.append(f"mention '{place.title()}' at least once")
    if "riverton" not in text and "bluffdale" not in text:
        issues.append("mention Riverton or Bluffdale at least once")
    for phrase in ("best realtor in", "#1 realtor", "top realtor", "number one realtor"):
        for m in re.finditer(re.escape(phrase), p["body_md"].lower()):
            issues.append(f"body contains '{phrase}': only allowed as a question/title, never as a claim")
    return issues


# ---------- Parsing ----------

def parse_post(path):
    text = open(path, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        raise ValueError(f"{path}: missing front matter")
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip().strip('"')
    for key in ("title", "slug", "description", "date", "summary"):
        if not meta.get(key):
            raise ValueError(f"{path}: front matter needs '{key}'")
    meta.setdefault("updated", meta["date"])
    meta.setdefault("category", "Real Estate")
    meta["areas"] = [a.strip() for a in meta.get("areas", ", ".join(AREAS)).split(",") if a.strip()]
    meta["body_md"] = m.group(2).strip()
    meta["source"] = path
    return meta


def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)", r"<em>\1</em>", s)

    def link(m):
        label, url = m.group(1), m.group(2)
        ext = url.startswith("http")
        attrs = ' target="_blank" rel="noopener"' if ext else ""
        return f'<a href="{html.escape(url)}"{attrs}>{label}</a>'
    return re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, s)


def md_to_html(md):
    """Small Markdown subset: ##/### headings, paragraphs, - and 1. lists, > quotes, pipe tables."""
    out, lines, i = [], md.splitlines(), 0
    while i < len(lines):
        line = lines[i].rstrip()
        if not line.strip():
            i += 1
            continue
        h = re.match(r"^(#{2,4})\s+(.*)$", line)
        if h:
            lvl = len(h.group(1))
            out.append(f"<h{lvl}>{inline(h.group(2))}</h{lvl}>")
            i += 1
            continue
        if re.match(r"^\s*[-*]\s+", line) or re.match(r"^\s*\d+\.\s+", line):
            ordered = bool(re.match(r"^\s*\d+\.", line))
            tag = "ol" if ordered else "ul"
            pat = r"^\s*\d+\.\s+" if ordered else r"^\s*[-*]\s+"
            items = []
            while i < len(lines) and re.match(pat, lines[i]):
                items.append(f"<li>{inline(re.sub(pat, '', lines[i]).strip())}</li>")
                i += 1
            out.append(f"<{tag}>" + "".join(items) + f"</{tag}>")
            continue
        if line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            rows = [r for r in rows if not all(re.match(r"^:?-{2,}:?$", c) for c in r)]
            head, body = rows[0], rows[1:]
            t = ["<div class=\"table-wrap\"><table><thead><tr>"]
            t += [f"<th>{inline(c)}</th>" for c in head]
            t.append("</tr></thead><tbody>")
            for r in body:
                t.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>")
            t.append("</tbody></table></div>")
            out.append("".join(t))
            continue
        if line.startswith(">"):
            q = []
            while i < len(lines) and lines[i].startswith(">"):
                q.append(lines[i].lstrip("> ").strip())
                i += 1
            out.append(f"<blockquote><p>{inline(' '.join(q))}</p></blockquote>")
            continue
        para = []
        while i < len(lines) and lines[i].strip() and not re.match(r"^(#{2,4}\s|\s*[-*]\s|\s*\d+\.\s|\||>)", lines[i]):
            para.append(lines[i].strip())
            i += 1
        out.append(f"<p>{inline(' '.join(para))}</p>")
    return "\n".join(out)


def split_sections(md):
    """Pull the 'Key Takeaways' and 'Frequently Asked Questions' sections out of the body."""
    takeaways, faqs, body = [], [], []
    section = None
    for line in md.splitlines():
        h2 = re.match(r"^##\s+(.*)$", line)
        if h2:
            name = h2.group(1).strip().lower()
            if name.startswith("key takeaways"):
                section = "takeaways"
                continue
            if name.startswith("frequently asked questions") or name == "faq" or name == "faqs":
                section = "faq"
                continue
            section = None
        if section == "takeaways":
            m = re.match(r"^\s*[-*]\s+(.*)$", line)
            if m:
                takeaways.append(m.group(1).strip())
        elif section == "faq":
            q = re.match(r"^###\s+(.*)$", line)
            if q:
                faqs.append([q.group(1).strip(), []])
            elif faqs and line.strip():
                faqs[-1][1].append(line.strip())
        else:
            body.append(line)
    faqs = [(q, " ".join(a)) for q, a in faqs]
    return takeaways, faqs, "\n".join(body).strip()


def strip_md(s):
    s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)
    return re.sub(r"\*\*?(.+?)\*\*?", r"\1", s)


def fmt_date(iso):
    d = date.fromisoformat(iso)
    return d.strftime("%B %-d, %Y")


def read_minutes(md):
    return max(2, round(len(md.split()) / 225))


def post_url(slug, absolute=False):
    rel = f"blog/{slug}.html"
    return f"{SITE_URL.rstrip('/')}/{rel}" if (absolute and SITE_URL) else rel


# ---------- Templates ----------

def head(title, desc, css_prefix, canonical=None, extra=""):
    canon = f'\n  <link rel="canonical" href="{canonical}">' if canonical else ""
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html.escape(title)}</title>
  <meta name="description" content="{html.escape(desc)}">{canon}
  <meta property="og:type" content="article">
  <meta property="og:title" content="{html.escape(title)}">
  <meta property="og:description" content="{html.escape(desc)}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:wght@600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{css_prefix}styles.css">{extra}
</head>
<body>
'''


def nav(r):
    return f'''
  <!-- Navigation -->
  <header class="site-header">
    <div class="container nav">
      <a href="{r}index.html" class="logo">Nick Gonzalez<span>Keller Williams</span></a>
      <input type="checkbox" id="nav-toggle" class="nav-toggle" aria-label="Toggle menu">
      <label for="nav-toggle" class="nav-toggle-label" aria-hidden="true"><span></span></label>
      <nav class="nav-links" aria-label="Main">
        <a href="{r}index.html#about">About</a>
        <a href="{r}index.html#listings">Listings</a>
        <a href="{r}index.html#testimonials">Testimonials</a>
        <a href="{r}team.html">Team</a>
        <a href="{r}blog.html" aria-current="page">Blog</a>
        <a href="{r}index.html#book">Book</a>
        <a href="{r}index.html#contact" class="btn btn-small">Contact</a>
      </nav>
    </div>
  </header>
'''


def footer(r):
    return f'''
  <!-- Call to Action -->
  <section class="section section-dark cta">
    <div class="container">
      <h2>Thinking About a Move in Riverton or Bluffdale?</h2>
      <p>Book a free consultation or send a message and I'll get back to you within 24 hours.</p>
      <div class="hero-actions cta-actions">
        <a href="{r}index.html#book" class="btn">Book a Consultation</a>
        <a href="{r}index.html#contact" class="btn btn-outline">Send a Message</a>
      </div>
    </div>
  </section>

  <footer class="site-footer">
    <div class="container footer-inner">
      <p class="footer-social"><a href="{AUTHOR['instagram']}" target="_blank" rel="noopener">{IG_ICON} @nickgonzalezrealtor</a></p>
      <p>&copy; {date.today().year} Nick Gonzalez &middot; Keller Williams Realty &middot; Utah</p>
      <p class="footer-note">Each Keller Williams office is independently owned and operated. Equal Housing Opportunity.</p>
    </div>
  </footer>

</body>
</html>
'''


def jsonld(obj):
    return ('\n  <script type="application/ld+json">\n'
            + json.dumps(obj, indent=2, ensure_ascii=False).replace("</", "<\\/")
            + "\n  </script>")


def person():
    return {
        "@type": ["Person", "RealEstateAgent"],
        "name": AUTHOR["name"],
        "jobTitle": AUTHOR["title"],
        "worksFor": {"@type": "RealEstateAgent", "name": AUTHOR["brokerage"]},
        "areaServed": [{"@type": "Place", "name": a} for a in AREAS],
        "sameAs": [AUTHOR["instagram"]],
    }


def render_post(p, image, related):
    takeaways, faqs, body_md = split_sections(p["body_md"])
    abs_url = post_url(p["slug"], absolute=True) if SITE_URL else None
    graph = [{
        "@type": "BlogPosting",
        "headline": p["title"],
        "description": p["description"],
        "abstract": p["summary"],
        "datePublished": p["date"],
        "dateModified": p["updated"],
        "articleSection": p["category"],
        "keywords": p.get("keywords", ""),
        "image": image,
        "author": person(),
        "publisher": {"@type": "Organization", "name": f"{AUTHOR['name']}, {AUTHOR['brokerage']}"},
        "about": [{"@type": "Place", "name": a} for a in p["areas"]],
        "inLanguage": "en-US",
    }]
    if abs_url:
        graph[0]["mainEntityOfPage"] = abs_url
        graph[0]["url"] = abs_url
    if faqs:
        graph.append({
            "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": q,
                            "acceptedAnswer": {"@type": "Answer", "text": strip_md(a)}} for q, a in faqs],
        })
    crumbs = [("Home", "index.html"), ("Blog", "blog.html"), (p["title"], f"blog/{p['slug']}.html")]
    graph.append({
        "@type": "BreadcrumbList",
        "itemListElement": [{"@type": "ListItem", "position": n + 1, "name": name,
                             **({"item": f"{SITE_URL.rstrip('/')}/{u}"} if SITE_URL else {})}
                            for n, (name, u) in enumerate(crumbs)],
    })
    schema = jsonld({"@context": "https://schema.org", "@graph": graph})

    mins = read_minutes(p["body_md"])
    areas = " &middot; ".join(html.escape(a) for a in p["areas"])
    tk = ""
    if takeaways:
        tk = ('\n        <aside class="key-takeaways">\n          <h2>Key Takeaways</h2>\n          <ul>'
              + "".join(f"<li>{inline(t)}</li>" for t in takeaways) + "</ul>\n        </aside>")
    faq_html = ""
    if faqs:
        faq_html = ('\n        <section class="post-faq">\n          <h2>Frequently Asked Questions</h2>\n'
                    + "\n".join(f'          <details><summary>{inline(q)}</summary><p>{inline(a)}</p></details>'
                                for q, a in faqs)
                    + "\n        </section>")
    rel = ""
    if related:
        rel = ('\n        <section class="related-posts">\n          <h2>Related Questions</h2>\n          <ul>'
               + "".join(f'<li><a href="{r["slug"]}.html">{html.escape(r["title"])}</a></li>' for r in related)
               + "</ul>\n        </section>")

    return (head(f"{p['title']} | Nick Gonzalez, Keller Williams", p["description"], "../", abs_url, schema)
            + nav("../") + f'''
  <article class="post">
    <header class="post-header">
      <div class="container post-container">
        <nav class="breadcrumbs" aria-label="Breadcrumb"><a href="../index.html">Home</a> / <a href="../blog.html">Blog</a> / <span>{html.escape(p['category'])}</span></nav>
        <p class="blog-meta"><span class="blog-tag">{html.escape(p['category'])}</span> <time datetime="{p['date']}">{fmt_date(p['date'])}</time> &middot; {mins} min read</p>
        <h1>{html.escape(p['title'])}</h1>
        <p class="post-author">By <strong>Nick Gonzalez</strong>, Realtor with Keller Williams &middot; Updated <time datetime="{p['updated']}">{fmt_date(p['updated'])}</time></p>
        <p class="post-areas">Serving {areas}</p>
      </div>
    </header>
    <div class="container post-container">
      <div class="post-image" style="background-image: url('{image}');" role="img" aria-label="{html.escape(p['title'])}"></div>
      <div class="post-body">
        <section class="quick-answer" aria-label="Quick answer">
          <p class="quick-answer-label">Quick Answer</p>
          <p>{inline(p['summary'])}</p>
        </section>{tk}
{md_to_html(body_md)}{faq_html}
        <aside class="author-box">
          <p class="author-name">About the Author</p>
          <p><strong>Nick Gonzalez</strong> is a Realtor with Keller Williams who helps move-up buyers, downsizers, and sellers in Riverton, Bluffdale, and across Salt Lake County, Utah. <a href="../index.html#book">Book a free consultation</a>.</p>
          <p class="disclaimer">This article is general information, not legal, tax, or lending advice. Market conditions change; contact Nick for current numbers on your home.</p>
        </aside>{rel}
      </div>
    </div>
  </article>
''' + footer("../"))


def render_index(posts, images):
    cards = []
    for n, p in enumerate(posts):
        cls = "blog-card blog-card-featured" if n == 0 else "blog-card"
        cards.append(f'''        <article class="{cls}">
          <a href="blog/{p['slug']}.html" class="blog-card-image" style="background-image: url('{images[p['slug']]}');" aria-hidden="true" tabindex="-1"></a>
          <div class="blog-card-body">
            <p class="blog-meta"><span class="blog-tag">{html.escape(p['category'])}</span> <time datetime="{p['date']}">{fmt_date(p['date'])}</time> &middot; {read_minutes(p['body_md'])} min read</p>
            <h2><a href="blog/{p['slug']}.html">{html.escape(p['title'])}</a></h2>
            <p>{html.escape(p['description'])}</p>
            <a href="blog/{p['slug']}.html" class="read-more">Read more &rarr;</a>
          </div>
        </article>''')
    schema = jsonld({
        "@context": "https://schema.org",
        "@type": "Blog",
        "name": "Utah Real Estate Insights by Nick Gonzalez",
        "author": person(),
        "blogPost": [{"@type": "BlogPosting", "headline": p["title"], "datePublished": p["date"],
                      "url": post_url(p["slug"], absolute=True)} for p in posts],
    })
    return (head("Blog | Riverton & Bluffdale Real Estate | Nick Gonzalez, Keller Williams",
                 "Answers to the questions Riverton, Bluffdale, and Salt Lake County move-up buyers, downsizers, and sellers ask most, from Nick Gonzalez, Keller Williams Utah.",
                 "", f"{SITE_URL.rstrip('/')}/blog.html" if SITE_URL else None, schema)
            + nav("") + f'''
  <!-- Page Banner -->
  <section class="page-banner">
    <div class="container">
      <p class="eyebrow">Blog</p>
      <h1>Riverton &amp; Bluffdale Real Estate Answers</h1>
      <p class="page-banner-sub">Straight answers for move-up buyers, downsizers, and sellers in Riverton, Bluffdale, and across Salt Lake County, Utah.</p>
    </div>
  </section>

  <!-- Posts: generated by scripts/build_blog.py from content/posts/. Do not edit by hand. -->
  <section class="section">
    <div class="container">
      <div class="blog-grid">
{chr(10).join(cards)}
      </div>
    </div>
  </section>
''' + footer(""))


def render_llms(posts):
    base = SITE_URL.rstrip("/") + "/" if SITE_URL else ""
    lines = [
        "# Nick Gonzalez, Realtor | Keller Williams Utah",
        "",
        "> Nick Gonzalez is a Realtor with Keller Williams serving Riverton, Bluffdale, and the rest of Salt Lake County, Utah. "
        "He specializes in move-up buyers, downsizers (move-down buyers), and home sellers. "
        "The blog answers the questions these clients ask most, with local context for Riverton, Bluffdale, Salt Lake County, and Utah.",
        "",
        "## Main pages",
        "",
        f"- [Home]({base}index.html): About Nick, featured listings, testimonials, booking and contact",
        f"- [Meet the Team]({base}team.html): Nick's team and roles",
        f"- [Blog]({base}blog.html): all articles, newest first",
        "",
        "## Blog articles",
        "",
    ]
    for p in posts:
        lines.append(f"- [{p['title']}]({base}{post_url(p['slug'])}): {p['summary']}")
    lines += ["", "## Contact", "", f"- Instagram: {AUTHOR['instagram']}",
              f"- Book a consultation: {base}index.html#book", ""]
    return "\n".join(lines)


def render_sitemap(posts):
    base = SITE_URL.rstrip("/")
    urls = [(f"{base}/index.html", None), (f"{base}/team.html", None), (f"{base}/blog.html", posts[0]["updated"] if posts else None)]
    urls += [(post_url(p["slug"], absolute=True), p["updated"]) for p in posts]
    items = "".join(f"  <url><loc>{u}</loc>{f'<lastmod>{d}</lastmod>' if d else ''}</url>\n" for u, d in urls)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{items}</urlset>\n'


def check(paths):
    failed = 0
    for path in paths:
        p = parse_post(path)
        issues = check_post(p)
        status = "OK" if not issues else f"{len(issues)} issue(s)"
        print(f"{os.path.relpath(path, ROOT)}: {status} ({words(p['body_md']) + words(p['summary'])} words)")
        for i in issues:
            print(f"  - {i}")
        failed += bool(issues)
    raise SystemExit(1 if failed else 0)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        check(sys.argv[2:])
    posts = [parse_post(os.path.join(POSTS_DIR, f)) for f in sorted(os.listdir(POSTS_DIR)) if f.endswith(".md")]
    slugs = [p["slug"] for p in posts]
    dupes = {s for s in slugs if slugs.count(s) > 1}
    if dupes:
        raise SystemExit(f"Duplicate slugs: {', '.join(sorted(dupes))}")
    posts.sort(key=lambda p: (p["date"], p["title"]), reverse=True)

    images = {}
    for n, p in enumerate(sorted(posts, key=lambda p: p["slug"])):
        images[p["slug"]] = p.get("image") or DEFAULT_IMAGES[n % len(DEFAULT_IMAGES)]

    os.makedirs(BLOG_DIR, exist_ok=True)
    for p in posts:
        related = [r for r in posts if r is not p and r["category"] == p["category"]][:3]
        if len(related) < 3:
            related += [r for r in posts if r is not p and r not in related][:3 - len(related)]
        with open(os.path.join(BLOG_DIR, f"{p['slug']}.html"), "w", encoding="utf-8") as f:
            f.write(render_post(p, images[p["slug"]], related))

    with open(os.path.join(ROOT, "blog.html"), "w", encoding="utf-8") as f:
        f.write(render_index(posts, images))
    with open(os.path.join(ROOT, "llms.txt"), "w", encoding="utf-8") as f:
        f.write(render_llms(posts))
    if SITE_URL:
        with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as f:
            f.write(render_sitemap(posts))

    print(f"Built {len(posts)} posts -> blog/, blog.html, llms.txt" + (", sitemap.xml" if SITE_URL else " (set SITE_URL for sitemap.xml)"))


if __name__ == "__main__":
    main()
