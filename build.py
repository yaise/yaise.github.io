#!/usr/bin/env python3
"""
Regenerate index.html, tags.html, and tags/*.html from blog post metadata.

Post metadata is read from two <meta> tags in each blog/\*.html <head>:
  <meta name="post-date" content="YYYY-MM-DD">
  <meta name="post-tags" content="tag1,tag2">

Post title is read from the <h1 class="post-title"> element.

Run directly (`python3 build.py`) or automatically via the pre-commit hook.
"""

import glob
import os
from datetime import datetime
from html import escape
from html.parser import HTMLParser

SITE_TITLE = "Somesh Sasalatti"
GITHUB = "https://github.com/yaise"
TWITTER = "https://twitter.com/ssasalatti"

ROOT = os.path.dirname(os.path.abspath(__file__))


# ── HTML parser ───────────────────────────────────────────────────────────────

class PostParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.date = None
        self.tags = []
        self.title = None
        self._in_h1 = False
        self._h1_buf = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "meta":
            if a.get("name") == "post-date":
                self.date = a.get("content", "").strip()
            elif a.get("name") == "post-tags":
                raw = a.get("content", "")
                self.tags = [t.strip() for t in raw.split(",") if t.strip()]
        if tag == "h1" and "post-title" in a.get("class", ""):
            self._in_h1 = True

    def handle_endtag(self, tag):
        if tag == "h1" and self._in_h1:
            self._in_h1 = False
            self.title = "".join(self._h1_buf).strip()
            self._h1_buf.clear()

    def handle_data(self, data):
        if self._in_h1:
            self._h1_buf.append(data)


def parse_post(path):
    with open(path, encoding="utf-8") as fh:
        p = PostParser()
        p.feed(fh.read())
    date_str = p.date or "1970-01-01"
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    return {
        "href": f"/blog/{os.path.basename(path)}",
        "title": p.title or os.path.basename(path),
        "date": date_str,
        "date_obj": date_obj,
        "date_display": date_obj.strftime("%b %-d, %Y"),
        "tags": p.tags,
    }


# ── HTML generation helpers ───────────────────────────────────────────────────

def _sidebar(active):
    def nav_a(href, label):
        cls = ' class="active"' if label.lower() == active else ""
        return f'        <a href="{href}"{cls}>{label}</a>'

    return (
        '  <button class="menu-btn" id="menu-btn" aria-label="Toggle navigation">&#9776;</button>\n'
        '  <div class="overlay" id="overlay"></div>\n'
        '  <aside class="sidebar" id="sidebar">\n'
        '    <div class="sidebar-inner">\n'
        '      <a class="site-title" href="/">Somesh<br>Sasalatti</a>\n'
        '      <nav class="sidebar-nav">\n'
        + nav_a("/", "Home") + "\n"
        + nav_a("/about.html", "About") + "\n"
        + nav_a("/tags.html", "Tags") + "\n"
        + '      </nav>\n'
        '      <div class="sidebar-footer">\n'
        f'        <a href="{GITHUB}">GitHub</a>\n'
        f'        <a href="{TWITTER}">Twitter</a>\n'
        '      </div>\n'
        '    </div>\n'
        '  </aside>'
    )


def _page(title_tag, active, body):
    return (
        '<!DOCTYPE html>\n'
        '<html lang="en">\n'
        '<head>\n'
        '  <meta charset="utf-8">\n'
        '  <meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f'  <title>{title_tag}</title>\n'
        '  <link rel="stylesheet" href="/style.css">\n'
        '</head>\n'
        '<body data-sidebar="open">\n'
        + _sidebar(active) + "\n"
        '  <main class="main">\n'
        '    <div class="content">\n'
        + body + "\n"
        '    </div>\n'
        '  </main>\n'
        '  <script src="/sidebar.js"></script>\n'
        '</body>\n'
        '</html>\n'
    )


def _post_list_items(posts):
    lines = []
    for p in posts:
        tags_html = "".join(
            f'<a class="tag" href="/tags/{escape(t)}.html">{escape(t)}</a>'
            for t in p["tags"]
        )
        tag_span = (
            f'\n          <span class="post-tags">{tags_html}</span>'
            if tags_html else ""
        )
        lines.append(
            f'        <li>\n'
            f'          <span class="post-date">{p["date_display"]}</span>\n'
            f'          <a href="{p["href"]}">{escape(p["title"])}</a>'
            f'{tag_span}\n'
            f'        </li>'
        )
    return "\n".join(lines)


# ── Page generators ───────────────────────────────────────────────────────────

def gen_index(posts):
    items = _post_list_items(posts)
    body = (
        '      <h1 class="page-title">Writing</h1>\n'
        '      <ul class="post-list">\n'
        + items + "\n"
        '      </ul>'
    )
    return _page(SITE_TITLE, "home", body)


def gen_tags_page(tag_counts):
    items = "\n".join(
        f'        <li>\n'
        f'          <a class="tag" href="/tags/{escape(t)}.html">{escape(t)}</a>\n'
        f'          <span class="tag-count">({c})</span>\n'
        f'        </li>'
        for t, c in sorted(tag_counts.items())
    )
    body = (
        '      <h1 class="page-title">Tags</h1>\n'
        '      <ul class="tag-cloud">\n'
        + items + "\n"
        '      </ul>'
    )
    return _page(f"Tags | {SITE_TITLE}", "tags", body)


def gen_tag_page(tag, posts):
    items = _post_list_items(posts)
    body = (
        f'      <h1 class="page-title">#{escape(tag)}</h1>\n'
        '      <ul class="post-list">\n'
        + items + "\n"
        '      </ul>\n'
        '      <p class="post-nav"><a href="/tags.html">&#8592; All tags</a></p>'
    )
    return _page(f"#{escape(tag)} | {SITE_TITLE}", "tags", body)


# ── Main ──────────────────────────────────────────────────────────────────────

def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
    print(f"  wrote {os.path.relpath(path, ROOT)}")


def main():
    posts = sorted(
        [parse_post(p) for p in glob.glob(os.path.join(ROOT, "blog", "*.html"))],
        key=lambda p: p["date_obj"],
        reverse=True,
    )

    tag_counts = {}
    for p in posts:
        for t in p["tags"]:
            tag_counts[t] = tag_counts.get(t, 0) + 1

    write(os.path.join(ROOT, "index.html"), gen_index(posts))
    write(os.path.join(ROOT, "tags.html"), gen_tags_page(tag_counts))

    for tag in tag_counts:
        tagged = [p for p in posts if tag in p["tags"]]
        write(os.path.join(ROOT, "tags", f"{tag}.html"), gen_tag_page(tag, tagged))

    print(f"Done: {len(posts)} post(s), {len(tag_counts)} tag(s)")


if __name__ == "__main__":
    main()
