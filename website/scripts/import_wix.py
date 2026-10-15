"""One-time import of the Wix site's blog posts into clean HTML fragments.

Reads the rendered Wix post pages, keeps the post body (the element with
data-id="content-viewer"), and rewrites it as plain semantic HTML: paragraphs,
headings, lists, links, bold/italic, images (downloaded from static.wixstatic.com)
and YouTube embeds. Output: website/src/posts/<slug>.html plus images in
website/src/posts/img/. The text is kept exactly as published.

One-time import, already run (2026-10-06). src/posts/ is now edited by hand (e.g. the
property-tax post's spreadsheet link was corrected), so rerunning this would undo those edits.

Run:  python3 website/scripts/import_wix.py
"""
import html
import json
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "src" / "posts"
IMG = OUT / "img"
POSTS = {
    "how-does-construction-impact-brookline-s-town-finances": None,
    "brookline-property-tax-overview": None,
}
UA = {"User-Agent": "Mozilla/5.0"}

KEEP = {"p": "p", "h1": "h2", "h2": "h2", "h3": "h3", "h4": "h4", "h5": "h4", "h6": "h4",
        "ul": "ul", "ol": "ol", "li": "li", "strong": "strong", "b": "strong", "em": "em",
        "i": "em", "u": "u", "blockquote": "blockquote", "table": "table", "thead": "thead",
        "tbody": "tbody", "tr": "tr", "td": "td", "th": "th", "br": "br", "hr": "hr", "sup": "sup", "sub": "sub"}


def fetch(url):
    # curl rather than urllib: this Python build has no CA bundle configured
    return subprocess.run(["curl", "-sfL", "-A", UA["User-Agent"], url], check=True,
                          capture_output=True).stdout


class Body(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth = 0          # div depth inside the content viewer; 0 = not inside
        self.out = []
        self.stack = []         # open emitted tags, mirrored per source tag
        self.images = []
        self.videos = []
        self.skip = 0           # inside button/svg/script etc.

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if not self.depth:
            if a.get("data-id") == "content-viewer":
                self.depth = 1
            return
        if tag in ("div",):
            self.depth += 1
        yt = re.search(r"ytimg\.com/vi/([\w-]{11})/", a.get("style") or "")
        if tag == "button" and yt and yt.group(1) not in self.videos:
            # Wix renders a YouTube embed as a preview button; put the player where it was
            self.videos.append(yt.group(1))
            self.out.append('\n<figure class="video"><iframe src="https://www.youtube-nocookie.com/embed/%s" '
                            'title="Video" allowfullscreen loading="lazy"></iframe></figure>\n' % yt.group(1))
        if tag in ("button", "svg", "script", "style", "noscript"):
            self.skip += 1
        if self.skip:
            self.stack.append(None)
            return
        if tag == "span" and "font-weight:700" in (a.get("style") or "").replace(" ", ""):
            self.out.append("<strong>"); self.stack.append("strong"); return
        if tag == "span" and "font-style:italic" in (a.get("style") or "").replace(" ", ""):
            self.out.append("<em>"); self.stack.append("em"); return
        if tag == "a" and (a.get("href") or "").startswith("#viewer-"):
            # footnote and back-links inside the post; the targets keep their ids below
            self.out.append('<a href="%s">' % html.escape(a["href"], quote=True)); self.stack.append("a"); return
        if tag == "a" and a.get("href") and not a["href"].startswith("#"):
            self.out.append('<a href="%s">' % html.escape(a["href"], quote=True)); self.stack.append("a"); return
        if tag == "img":
            src = a.get("src") or a.get("data-src") or ""
            m = re.search(r"media/([^/?#]+?\.(?:png|jpe?g|gif|webp))", src)
            if m and m.group(1) not in self.images:
                self.images.append(m.group(1))
                self.out.append('\n<figure><img src="img/%s" alt="%s" loading="lazy"></figure>\n'
                                % (m.group(1).replace("~", "_"), html.escape(a.get("alt") or "", quote=True)))
            return
        if tag == "iframe" and "youtube" in (a.get("src") or ""):
            self.videos.append(a["src"]); return
        if tag in KEEP and tag not in ("br", "hr"):
            t = KEEP[tag]
            vid = a.get("id") or ""
            self.out.append('<%s id="%s">' % (t, vid) if vid.startswith("viewer-") else "<%s>" % t)
            self.stack.append(t); return
        if tag in ("div", "span") and (a.get("id") or "").startswith("viewer-") and a.get("tabindex"):
            self.out.append('<a id="%s"></a>' % a["id"])
        if tag in ("br", "hr"):
            self.out.append("<%s>" % tag); return
        if tag not in ("img", "iframe"):
            self.stack.append(None)

    def handle_endtag(self, tag):
        if not self.depth:
            return
        if tag == "div":
            self.depth -= 1
            if self.depth == 0:
                return
        if tag in ("img", "iframe", "br", "hr"):
            return
        if tag not in ("div",) and self.stack:
            t = self.stack.pop()
            if tag in ("button", "svg", "script", "style", "noscript"):
                self.skip = max(self.skip - 1, 0)
            if t and not self.skip:
                self.out.append("</%s>" % t)

    def handle_data(self, data):
        if self.depth and not self.skip:
            self.out.append(html.escape(data, quote=False))


def meta(page, prop):
    m = re.search(r'<meta[^>]+(?:property|name)="%s"[^>]+content="([^"]*)"' % re.escape(prop), page)
    return html.unescape(m.group(1)) if m else ""


def tidy(s):
    s = re.sub(r"<(strong|em|u|a[^>]*)>\s*</\1?[a-z]*>", "", s)
    s = re.sub(r"</strong>(\s*)<strong>", r"\1", s)
    s = re.sub(r"</em>(\s*)<em>", r"\1", s)
    s = re.sub(r"<p>\s*</p>", "", s)
    s = re.sub(r"(^|(?<=>))\s*(<br>\s*)+(?=<(p|h\d|ul|ol|figure|table|blockquote)[ >])", r"\1", s)
    s = re.sub(r"(<br>\s*)+$", "", s)
    s = re.sub(r"<(h\d)( id=\"[^\"]*\")?>\s*<br>\s*</\1>", "", s)
    s = re.sub(r"\s*<br>\s*</p>", "</p>", s)
    s = re.sub(r"<p>(\s*<figure>.*?</figure>\s*)</p>", r"\1", s, flags=re.S)
    s = re.sub(r"(</(p|h2|h3|h4|ul|ol|li|blockquote|table|tr|figure)>)", r"\1\n", s)
    return re.sub(r"\n{3,}", "\n\n", s).strip() + "\n"


def main():
    IMG.mkdir(parents=True, exist_ok=True)
    index = []
    for slug in POSTS:
        page = fetch("https://www.brooklinefuture.org/post/" + slug).decode("utf-8")
        p = Body(); p.feed(page)
        body = "".join(p.out)
        for name in p.images:
            dest = IMG / name.replace("~", "_")
            if not dest.exists():
                dest.write_bytes(fetch("https://static.wixstatic.com/media/" + name))
        info = dict(slug=slug, title=meta(page, "og:title"), description=meta(page, "og:description"),
                    published=meta(page, "article:published_time"), modified=meta(page, "article:modified_time"),
                    images=len(p.images), videos=len(p.videos))
        (OUT / (slug + ".html")).write_text(tidy(body))
        index.append(info)
        print(json.dumps(info))
    (OUT / "posts.json").write_text(json.dumps(index, indent=2))


if __name__ == "__main__":
    sys.exit(main())
