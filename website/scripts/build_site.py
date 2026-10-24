"""Build brooklinefuture.org as a static site in website/dist/.

Sources:
  website/src/pages/*.html     hand-written pages (home, about, forecast landing);
                               a leading <!-- title/description/image --> block sets the head
  website/src/posts/           the blog posts imported from Wix (scripts/import_wix.py)
  docs/*.html                  the forecast pages, built by their own scripts
                               (build_reference_doc.py, build_dashboard.py; forecast_2040_page
                               and expense_driver_tree_page are hand-edited HTML)
  land-value-map/dist/         the parcel maps (land-value-map/scripts/build_site.py)
  Brookline_Fiscal_Model.xlsx  the Excel model (scripts/build_excel_model.py)

The forecast pages were written to be published as claude.ai Artifacts, which wrap a
page in a document skeleton with a small CSS reset. This script supplies the same
skeleton so they render identically, adds the site bar and share metadata, and
rewrites links between pages from Artifact URLs to site paths. A link to an Artifact
that is not on the site is turned into plain text, so the public site never links to
a private page; every such link is reported.

URLs are kept from the Wix site (/about-ben-chostner, /brookline-insights, /post/<slug>),
so links already shared keep working.

Run:     python3 website/scripts/build_site.py
Preview: python3 -m http.server -d website/dist 8000   (clean URLs need the .html; or use `vercel dev`)
Deploy:  vercel deploy --prod website/dist --scope <team>   (dist/.vercel is preserved across builds)
"""
import html
import json
import re
import shutil
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

WEB = Path(__file__).resolve().parent.parent
ROOT = WEB.parent
SRC = WEB / "src"
DIST = WEB / "dist"
DOCS = ROOT / "docs"
MAPS = ROOT / "land-value-map" / "dist"
# The school seats map's shareable build (school-seats-map/build_public.py), embedded in its post
SEATS_MAP = ROOT / "school-seats-map" / "public" / "school_seats_map_public.html"
EXCEL = ROOT / "Brookline_Forecast_Model.xlsx"   # mirrors the Explorer (scripts/build_explorer_workbook.py)
SITE = "https://www.brooklinefuture.org"

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@'
         '0,6..72,400;0,6..72,500;0,6..72,600;0,6..72,700;1,6..72,400;1,6..72,500'
         '&family=Public+Sans:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap">')

# The reset the Artifact viewer puts around every page; the forecast pages were designed on top of it.
ARTIFACT_RESET = ("<style>:root{color-scheme:light;box-sizing:border-box;padding-top:env(safe-area-inset-top,0px);"
                  "padding-bottom:env(safe-area-inset-bottom,0px)}html{scroll-padding-top:env(safe-area-inset-top,0px)}"
                  "body{margin:0;padding:0;font:14px -apple-system,BlinkMacSystemFont,sans-serif;background:#faf9f5;color:#141413}"
                  "img{max-width:100%}[hidden]:not([hidden=until-found i]){display:none!important}</style>")

# Forecast pages: site path -> (built file, section of the site bar to highlight)
FORECAST_PAGES = {
    "forecast/article": DOCS / "article.html",
    "forecast/explorer": DOCS / "forecast_dashboard.html",
    "forecast/new-growth": DOCS / "new_growth.html",
}
# Retired 2026-10-08 (Ben): the reference document, the 2040 page and the spending history were
# split into the short reads and topic pages. Their old addresses redirect (see vercel.json).
RETIRED = {"/forecast/reference": "/forecast#full-detail", "/forecast/2040": "/forecast/base-case",
           "/forecast/spending-history": "/forecast/spending"}
# The reorganized pages, built by scripts/build_pages.py from docs/site/pages. Their
# description for search and link previews is the page's question.
def _new_pages():
    out, desc = {}, {}
    for f in sorted((DOCS / "site" / "pages").glob("*.md")):
        head = dict(re.findall(r"^(slug|path|question|status): (.*)$", f.read_text().split("\n---\n", 1)[0], re.M))
        out[head["path"]] = DOCS / "site" / "build" / f"{head['slug']}.html"
        desc[head["path"]] = head.get("question", "")
    return out, desc
NEW_PAGES, _NEW_DESC = _new_pages()

DESCRIPTIONS = {
    "forecast/article": "Brookline has asked voters for an override five times since 2005. What would actually have to change for that to stop?",
    "forecast/explorer": "Move the assumptions behind Brookline's General Fund forecast and watch revenue and spending through 2040.",
    "forecast/2040": "Brookline's General Fund to FY2040: the base case, the four decisions that matter most, and how it compares with the Town's plan.",
    "forecast/new-growth": "With enrollment falling and police and fire staffing flat, what a new home costs Brookline between now and 2040, and the choice that decides it.",
    "forecast/reference": "The full reference document behind the Brookline forecast: how the money works, FY2005 to 2025, what kind of growth pays for itself, and where this leads.",
    "forecast/spending-history": "Every dollar of growth in Brookline's annual General Fund spending from FY2011 to FY2025, assigned to one of nine causes.",
}
DESCRIPTIONS.update(_NEW_DESC)

# Forecast pieces listed alongside the essays on the Writing page and the home page:
# path -> (kind, title, first published)
FORECAST_LISTING = {
    "forecast/new-growth": ("Forecast", "New homes and Brookline's budget", "2026-10-06"),
    "forecast/explorer": ("Interactive", "Brookline Forecast Explorer", "2026-10-04"),
    "forecast/article": ("Essay", "Will Brookline need a sixth override?", "2026-09-07"),
}

# Artifact IDs of pages that are on the site, and where they now live
ARTIFACT_PATHS = {
    "602f2ce6-a7ae-4790-a589-502817946ca9": "/forecast/reference",
    "2cb282ea-1583-4ba7-965f-dd97db8e3162": "/forecast/article",
    "F2xNYNAacBGnbeLh2HiMhB": "/forecast/explorer",
    "1wMzohkoNEz5usndRabXSi": "/forecast/2040",
    "5e8m3o1PtZyaHM1cLYNxAA": "/forecast/new-growth",
    "L6PGA6xiabFrrQjAyM389c": "/forecast/spending-history",
}
OTHER_REWRITES = {
    "https://brookline-land-value.vercel.app/": "/maps/",
    "https://brookline-land-value.vercel.app": "/maps",
    "https://www.brooklinefuture.org/": "/",
}
ARTIFACT_LINK = re.compile(r'<a\b[^>]*href="https://claude\.ai/(?:code/)?artifact/([A-Za-z0-9-]+)[^"]*"[^>]*>(.*?)</a>', re.S)

REVEAL_JS = """<script>
document.querySelectorAll("button.reveal[data-user]").forEach(function (b) {
  b.addEventListener("click", function () {
    var a = document.createElement("a"), e = [b.dataset.user, b.dataset.domain].join("@");
    a.href = "mailto:" + e; a.textContent = e; b.replaceWith(a);
  });
});
</script>"""

unlinked = []


def front_matter(text):
    m = re.match(r"\s*<!--(.*?)-->\s*", text, re.S)
    meta = {}
    if m:
        for line in m.group(1).strip().splitlines():
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip()
        text = text[m.end():]
    return meta, text


def head_meta(title, desc, path, image=None, kind="website"):
    url = SITE + ("/" + path if path else "/")
    tags = [
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">',
        f'<meta name="description" content="{html.escape(desc, quote=True)}">',
        f'<link rel="canonical" href="{url}">',
        f'<meta property="og:type" content="{kind}">',
        f'<meta property="og:site_name" content="brooklinefuture.org">',
        f'<meta property="og:title" content="{html.escape(title, quote=True)}">',
        f'<meta property="og:description" content="{html.escape(desc, quote=True)}">',
        f'<meta property="og:url" content="{url}">',
        '<meta name="twitter:card" content="summary_large_image">',
        '<link rel="icon" href="/favicon.svg" type="image/svg+xml">',
    ]
    if image:
        tags.append(f'<meta property="og:image" content="{SITE}/{image.lstrip("/")}">')
    return "\n".join(tags)


def nav(section):
    bar = (SRC / "nav.html").read_text()
    if section:
        bar = bar.replace(f'data-sec="{section}"', f'data-sec="{section}" aria-current="page"')
    return bar


# Draft notice under the site bar on every forecast page, until the forecast is final.
# Self-contained like the site bar, since the forecast pages bring their own CSS.
DRAFT_NOTICE = """<style>
#bf-draft { --d-bg: #f6eed9; --d-ink: #1c1c1a; --d-tag: #7a4b00; border-bottom: 1px solid var(--d-ink);
  background: var(--d-bg); color: var(--d-ink); font: 400 14px/1.4 "Public Sans", -apple-system, "Segoe UI", Helvetica, Arial, sans-serif; }
@media (prefers-color-scheme: dark) { #bf-draft { --d-bg: #2a2416; --d-ink: #e8e6e1; --d-tag: #e3b25c; } }
#bf-draft .bf-in { max-width: 62rem; margin: 0 auto; padding: 0.5rem 1.25rem; }
#bf-draft strong { color: var(--d-tag); font-weight: 700; letter-spacing: 0.12em; margin-right: 0.6rem; }
</style>
<aside id="bf-draft" aria-label="Draft notice"><div class="bf-in"><strong>DRAFT</strong>This forecast is a work in progress and not final. Figures and wording may change.</div></aside>"""


# The short reads are chapters in one story, read in this order (Ben, 2026-10-08). Each gets a
# footer with the previous and next chapter and a link back to the list on /forecast. Like the
# draft notice it is self-contained, since the forecast pages bring their own CSS.
SERIES = json.loads((DOCS / "site" / "series.json").read_text())
SERIES_CSS = """<style>
.bf-series { --s-ink: #1c1c1a; --s-muted: #4f4f4a; --s-link: #1f3a5f; --s-rule: #dcdbd5; --s-card: #ffffff;
  max-width: 40rem; width: calc(100% - 32px); box-sizing: border-box; margin: 48px auto 32px; padding: 16px 20px; border: 1px solid var(--s-rule); border-radius: 6px;
  background: var(--s-card); color: var(--s-ink); font: 400 15px/1.5 "Public Sans", -apple-system, "Segoe UI", Helvetica, Arial, sans-serif; }
@media (prefers-color-scheme: dark) { .bf-series { --s-ink: #e8e6e1; --s-muted: #b9b7b0; --s-link: #8fb0d8; --s-rule: #2f3236; --s-card: #1c1f22; } }
@media print { .bf-series { display: none; } }
.bf-series .bf-s-label { margin: 0 0 10px; font-size: 12px; letter-spacing: .08em; text-transform: uppercase; color: var(--s-muted); font-weight: 600; }
.bf-series .bf-s-row { display: flex; justify-content: space-between; gap: 16px; flex-wrap: wrap; }
.bf-series a { color: var(--s-link); text-underline-offset: .15em; }
.bf-series .bf-s-next { margin-left: auto; text-align: right; }
.bf-series .bf-s-all { display: inline-block; margin-top: 10px; }
</style>"""


# A compact version of the levers chart for the landing page (Ben, 2026-10-08: "yes, but
# simplified", then: make clear which way each one moves the budget). It shows where the FY2040
# balance of revenue over spending lands if one decision goes the other way: two turn the base
# case's room into a shortfall, two widen it. Static SVG from the same model output as the full chart.
LEVERS = [("pay_up1", "Staff pay grows 1 point a year faster"), ("premiums_high", "Health benefits grow 10% a year, not 8%"),
          ("pension_kept", "Freed pension money kept in the budget"), ("staff_follow", "School staff shrink with enrollment")]


def levers_chart():
    data = json.loads((ROOT / "output" / "site_data.json").read_text())
    dec = {d["key"]: d for d in data["decisions"]}
    room = dict((y, v) for y, v in data["room"])[2040]
    rows = [("Base case", room, "base")] + [(label, room + dec[k]["fy40"], "neg" if dec[k]["fy40"] < 0 else "pos")
                                            for k, label in LEVERS]
    # HTML bars rather than SVG, so the text keeps its size on a phone. Bars use the middle 70% of
    # each track; the 15% on either side holds the values.
    lo, hi = min(v for _, v, _ in rows), max(v for _, v, _ in rows)
    pct = lambda v: 15 + (v - lo) / (hi - lo) * 70
    zero = pct(0)
    out = [f'<div class="lv-row lv-head" aria-hidden="true"><span></span><span class="lv-track">'
           f'<span class="lv-hint lv-hint-l" style="right:{100 - zero:.1f}%">&larr; shortfall</span>'
           f'<span class="lv-hint" style="left:{zero:.1f}%">room &rarr;</span></span></div>']
    for label, v, kind in rows:
        left, width = (zero, pct(v) - zero) if v >= 0 else (pct(v), zero - pct(v))
        val = ("+" if v >= 0 else "&minus;") + f"${abs(v):.1f}M"
        pos = f"left:calc({left + width:.1f}% + 6px)" if v >= 0 else f"right:calc({100 - left:.1f}% + 6px)"
        out.append(f'<div class="lv-row{" lv-first" if kind == "base" else ""}"><span class="lv-l">{html.escape(label)}</span>'
                   f'<span class="lv-track"><span class="lv-zero" style="left:{zero:.1f}%"></span>'
                   f'<span class="lv-bar lv-{kind}" style="left:{left:.1f}%;width:{max(width, 0.4):.1f}%"></span>'
                   f'<span class="lv-v" style="{pos}">{val}</span></span></div>')
    word = lambda v: f"${v:.1f} million of room" if v >= 0 else f"a ${-v:.1f} million shortfall"
    desc = (f"Bar chart of the FY2040 balance of revenue over spending. Base case: {word(room)}. "
            + "; ".join(f"{l}: {word(v)}" for l, v, _ in rows[1:]) + ".")
    table = "".join(f"<tr><th scope=\"row\">{html.escape(l)}</th><td>{'+' if v >= 0 else '&minus;'}${abs(v):.1f}M</td></tr>"
                    for l, v, _ in rows)
    return (f'<figure class="levers"><figcaption><strong>One decision can flip the budget.</strong> In the base case, '
            f'revenue runs ${room:.1f} million ahead of spending in FY2040. Staff pay or health benefits growing faster '
            f'would each turn that into a shortfall; keeping the freed pension money would widen it several times over, '
            f'and letting school staff shrink with enrollment would widen it by more than half. '
            f'<a href="/forecast/budget-to-2040#what-could-use-up-the-room">The full chart</a> has every assumption.</figcaption>'
            f'<div class="lv-chart" role="img" aria-label="{html.escape(desc)}">{"".join(out)}</div>'
            f'<details><summary>Show the numbers</summary><table><thead><tr><th scope="col">If</th>'
            f'<th scope="col">Revenue minus spending, FY2040</th></tr></thead><tbody>{table}</tbody></table></details></figure>')


# Site search (Pagefind, agreed 2026-10-07): a static index built from the forecast pages at
# build time; searching happens in the reader's browser. Writing posts are not indexed.
NO_SEARCH = {"forecast/explorer", "forecast/changes"}
PAGEFIND = "pagefind@1.3.0"


def series_nav(path):
    paths = [c["path"] for c in SERIES]
    if path not in paths:
        return ""
    i = paths.index(path)
    links = []
    if i > 0:
        links.append(f'<a class="bf-s-prev" rel="prev" href="/{SERIES[i - 1]["path"]}">&larr; Previous: {html.escape(SERIES[i - 1]["title"])}</a>')
    if i < len(SERIES) - 1:
        links.append(f'<a class="bf-s-next" rel="next" href="/{SERIES[i + 1]["path"]}">Next: {html.escape(SERIES[i + 1]["title"])} &rarr;</a>')
    return (f'{SERIES_CSS}<nav class="bf-series" aria-label="Short reads" data-pagefind-ignore>'
            f'<p class="bf-s-label">Short read {i + 1} of {len(SERIES)}</p><div class="bf-s-row">{"".join(links)}</div>'
            f'<a class="bf-s-all" href="/forecast#findings">All five findings</a></nav>')


# Print styles for the forecast pages (added 2026-10-07). Printing always uses the page's
# own light palette, whatever mode the reader is in: each page's light color tokens (its
# first top-level :root block) are restated for print with a selector that outranks the
# dark-mode blocks. Then charts, stat rows and table rows are kept whole, table headers
# repeat across pages, wide tables wrap instead of scrolling, and on-screen-only controls
# (buttons, tooltips, the Explorer's room bar) are left out.
def light_tokens(css_text):
    """Custom-property declarations from top-level :root blocks (not inside a dark @media)."""
    out, depth, media_stack, i = [], 0, [], 0
    import re as _re
    tok = _re.compile(r"@media[^{]*\{|:root\s*\{|\{|\}")
    for m in tok.finditer(css_text):
        t = m.group(0)
        if t.startswith("@media"):
            media_stack.append(depth); depth += 1
            if "dark" in t: media_stack[-1] = ("dark", depth - 1)
        elif t.startswith(":root"):
            end = css_text.find("}", m.end())
            in_dark = any(isinstance(x, tuple) for x in media_stack)
            body = css_text[m.end():end]
            if not in_dark and "--" in body:
                out.append(" ".join(l.strip() for l in body.splitlines() if l.strip()))
        elif t == "{":
            depth += 1
        else:
            depth -= 1
            if media_stack and (media_stack[-1] if not isinstance(media_stack[-1], tuple) else media_stack[-1][1]) == depth:
                media_stack.pop()
    return " ".join(out)


PRINT_RULES = """
  @page { margin: 14mm 13mm; }
  :root:not(#bf-print) { color-scheme: light; %s }
  #bf-bar { --bf-bg: #fff !important; --bf-ink: #1c1c1a !important; --bf-muted: #4f4f4a !important; --bf-accent: #1f3a5f !important; }
  #bf-draft { --d-bg: #fff !important; --d-ink: #1c1c1a !important; --d-tag: #7a4b00 !important; }
  html, body { background: #fff !important; }
  #bf-bar nav, button, .tooltip, .tip, .dock, .toggle-table-btn, .reset, .presets { display: none !important; }
  .tor-bar, .tor-zero, .b-bar, .b-zero, .sw, .sq, .legend-swatch, .tag, .tor-track {
    -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  .chart-block, .chart-row, svg, .stat-row, .stat, .finding, .callout, .note, .wf-stat, figure, .fig, .b-row,
  .tor-row, tr, blockquote, .ctl { break-inside: avoid; page-break-inside: avoid; }
  h1, h2, h3, h4, .chart-head { break-after: avoid; page-break-after: avoid; }
  thead { display: table-header-group; }
  .prose-table-wrap, .data-table-wrap, .table-card, .tablewrap { overflow: visible !important; }
  table th, table td { white-space: normal !important; }
  a { color: inherit !important; }
"""


def print_css(page_css):
    return "<style>@media print {" + (PRINT_RULES % light_tokens(page_css)) + "}</style>"


MAP_BAR_FIX = """<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,700&family=Public+Sans:wght@400;600;700&display=swap">\n<style>body > #map, body > #panel { top: var(--bf-h, 44px) !important; }\n:root { --accent: #8fb0d8 !important; }\nbody, #panel { font-family: "Public Sans", -apple-system, "Segoe UI", sans-serif !important; }\n#panel h1 { font-family: "Newsreader", Georgia, serif !important; font-weight: 700; }</style>
<script>
(function () {
  function fit() {
    var h = document.getElementById("bf-bar").offsetHeight;
    document.documentElement.style.setProperty("--bf-h", h + "px");
    if (window.map && window.map.resize) window.map.resize();
  }
  fit(); window.addEventListener("resize", fit);
})();
</script>"""


FOOTER = """<footer class="site-foot"><div class="page"><p>brooklinefuture.org &middot; Ben Chostner, Town Meeting Member, Brookline Precinct 9 &middot; Brookline, MA</p></div></footer>
<style>.site-foot{border-top:1px solid var(--rule);color:var(--ink-faint);font-size:.85rem;padding-block:1.5rem 2.5rem}.site-foot p{margin:0}</style>"""


def page(title, desc, path, body, section=None, image=None, kind="website"):
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{html.escape(title)}</title>
{head_meta(title, desc, path, image, kind)}
{FONTS}
<link rel="stylesheet" href="/site.css">
{print_css((SRC / "site.css").read_text()) if section == "forecast" else ""}
</head>
<body>
{nav(section)}{DRAFT_NOTICE if section == "forecast" else ""}
<main class="page">
{body}
</main>
{FOOTER}
{REVEAL_JS}
</body>
</html>
"""


def rewrite_links(text, where):
    for a, b in OTHER_REWRITES.items():
        text = text.replace(f'href="{a}', f'href="{b}')

    def sub(m):
        aid, label = m.group(1), m.group(2)
        if aid in ARTIFACT_PATHS:
            return m.group(0).replace(re.search(r'href="[^"]*"', m.group(0)).group(0), f'href="{ARTIFACT_PATHS[aid]}"')
        unlinked.append((where, aid, re.sub(r"<[^>]+>", "", label)))
        return label
    return ARTIFACT_LINK.sub(sub, text)


def wrap_forecast_page(path, src):
    text = src.read_text()
    # leading head-only material: meta, title, link, style, and script tags that load a src
    head_re = re.compile(r'\s*(<meta\b[^>]*>|<title>.*?</title>|<link\b[^>]*>|<style\b[^>]*>.*?</style>|<script\b[^>]*src=[^>]*>\s*</script>)', re.S)
    pos, parts = 0, []
    while True:
        m = head_re.match(text, pos)
        if not m:
            break
        parts.append(m.group(1)); pos = m.end()
    head, body = "\n".join(p for p in parts if not p.startswith("<meta charset")), text[pos:]
    title = re.search(r"<title>(.*?)</title>", head, re.S).group(1).strip()
    # internal build notes in the document footers are not for the public site
    body = re.sub(r"<p>Generated from <code>docs/[^<]*</code>[^<]*</p>",
                  '<p>Part of <a href="/forecast">Brookline\'s finances to 2040</a>, an independent analysis by '
                  '<a href="/about-ben-chostner">Ben Chostner</a>.</p>', body)
    body = re.sub(r"<p>Reference document for the Brookline Town Finances project\.[^<]*<code>[^<]*</code>[^<]*</p>",
                  '<p>Part of <a href="/forecast">Brookline\'s finances to 2040</a>, an independent analysis by '
                  '<a href="/about-ben-chostner">Ben Chostner</a>.</p>', body)
    body = rewrite_links(body, path)
    # every page gets a main landmark for screen readers; some built pages have none
    if "<main" not in body:
        body = "<main>\n" + body + "\n</main>"
    if path not in NO_SEARCH:
        body = re.sub(r"<main\b", "<main data-pagefind-body", body, count=1)
    nav_html = series_nav(path)
    if nav_html and "<!--series-nav-->" in body:
        body = body.replace("<!--series-nav-->", nav_html, 1)
    elif nav_html:
        k = body.rfind("</main>")
        body = body[:k] + nav_html + "\n" + body[k:]
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
{ARTIFACT_RESET}
{head_meta(html.unescape(title), DESCRIPTIONS[path], path, "img/whitepaper-chart.png", "article")}
{head}
{print_css(text)}
</head>
<body>
{nav("forecast")}
{DRAFT_NOTICE}
{body}
</body>
</html>
"""


def post_pages(posts):
    items = []
    for p in sorted(posts, key=lambda p: p["published"], reverse=True):
        src = SRC / "posts" / (p["slug"] + ".html")
        if not src.exists():   # the public GitHub copy leaves out posts that name projects
            print(f"post {p['slug']}: source not found, skipped")
            continue
        body = src.read_text()
        words = len(re.sub(r"<[^>]+>", " ", body).split())
        d = datetime.fromisoformat(p["published"].replace("Z", "+00:00")).date()
        when = d.strftime("%B %-d, %Y")
        mins = max(1, round(words / 230))
        first_img = re.search(r'<img src="(img/[^"]+)"', body)
        head = (f'<header class="masthead"><p class="eyebrow">Brookline Insights</p>'
                f'<h1 class="title">{html.escape(p["title"])}</h1>'
                f'<p class="meta">Ben Chostner &middot; {when} &middot; {mins} min read</p></header>')
        out = page(p["title"], p["description"], "post/" + p["slug"],
                   head + f'<article class="prose">\n{rewrite_links(body, "post/" + p["slug"])}</article>',
                   "writing", "post/" + first_img.group(1) if first_img else "img/whitepaper-chart.png", "article")
        (DIST / "post").mkdir(exist_ok=True)
        (DIST / "post" / (p["slug"] + ".html")).write_text(out)
        items.append(dict(kind="Essay", href="/post/" + p["slug"], title=p["title"], date=d,
                          length=f"{mins} min read", desc=p["description"]))
    return items


def reading_minutes(path):
    t = re.sub(r"(?s)<(script|style)[^>]*>.*?</\1>", " ", path.read_text())
    return round(len(re.sub(r"<[^>]+>", " ", t).split()) / 230)


def listing(posts_items):
    """Essays and forecast pieces together, newest first."""
    items = list(posts_items)
    for path, (kind, title, when) in FORECAST_LISTING.items():
        mins = reading_minutes(FORECAST_PAGES[path])
        length = ("interactive" if kind == "Interactive"
                  else f"about {round(mins / 60)} hours" if mins >= 90 else f"{max(mins, 1)} min read")
        items.append(dict(kind=kind, href="/" + path, title=title, date=date.fromisoformat(when),
                          length=length, desc=DESCRIPTIONS[path]))
    items.sort(key=lambda i: i["date"], reverse=True)
    rows = [f'<li><p class="kind">{i["kind"]}</p><a class="t" href="{i["href"]}">{html.escape(i["title"])}</a>'
            f'<p class="meta">{i["date"].strftime("%B %-d, %Y")} &middot; {i["length"]}</p>'
            f'<p>{html.escape(i["desc"])}</p></li>' for i in items]
    return '<ul class="posts">\n' + "\n".join(rows) + "\n</ul>"


def copy_images(src_dir, dest_dir, max_px=2000):
    dest_dir.mkdir(parents=True, exist_ok=True)
    for f in sorted(src_dir.iterdir()):
        if f.suffix.lower() not in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"):
            continue
        d = dest_dir / f.name
        shutil.copy2(f, d)
        if f.suffix.lower() in (".png", ".jpg", ".jpeg"):
            subprocess.run(["sips", "-Z", str(max_px), str(d)], capture_output=True)


def maps():
    dest = DIST / "maps"
    if not MAPS.exists():   # the public GitHub copy leaves the maps out (they carry owner names)
        print("maps: land-value-map/dist not found, skipped")
        return
    shutil.copytree(MAPS, dest, ignore=shutil.ignore_patterns(".vercel", "vercel.json"))
    # the map pages use relative paths; under /maps (no trailing slash) those would
    # resolve to the site root, so make them absolute
    for f in dest.glob("*.html"):
        t = f.read_text()
        t = re.sub(r"(['\"])data/", r"\1/maps/data/", t)
        t = re.sub(r'href="([a-z_]+)\.html"', r'href="/maps/\1"', t)
        t = t.replace('href="index.html"', 'href="/maps"')
        # site bar: the map and its side panel are absolutely positioned from the top of
        # the page, so push both down by the bar's measured height
        bar = nav("maps") + MAP_BAR_FIX
        t = re.sub(r"<body([^>]*)>", lambda m: m.group(0) + "\n" + bar, t, count=1)
        f.write_text(t)


def seats_map():
    """The school seats map as its own page, for the post's iframe; written as an Artifact, so it gets the skeleton."""
    if not SEATS_MAP.exists():   # not in the public GitHub copy
        print("seats map: school-seats-map/public not found, skipped")
        return
    (DIST / "embed").mkdir(exist_ok=True)
    (DIST / "embed" / "school-seats-map.html").write_text(
        '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        f'<link rel="canonical" href="{SITE}/post/school-seats-map">\n{ARTIFACT_RESET}\n</head>\n<body>\n'
        + SEATS_MAP.read_text() + "\n</body>\n</html>\n")


def main():
    vercel = DIST / ".vercel"
    keep = None
    if vercel.exists():
        keep = WEB / ".vercel-keep"
        shutil.rmtree(keep, ignore_errors=True); shutil.copytree(vercel, keep)
    shutil.rmtree(DIST, ignore_errors=True)
    DIST.mkdir()
    if keep:
        shutil.copytree(keep, vercel); shutil.rmtree(keep)

    shutil.copy2(SRC / "site.css", DIST / "site.css")
    (DIST / "favicon.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="3" fill="#1f3a5f"/>'
        '<text x="16" y="22.5" text-anchor="middle" font-family="Georgia,serif" font-size="21" font-weight="700" fill="#fbfbf8">b</text></svg>')
    copy_images(SRC / "img", DIST / "img", 1600)
    copy_images(SRC / "posts" / "img", DIST / "post" / "img", 2000)

    posts = json.loads((SRC / "posts" / "posts.json").read_text())
    post_list = listing(post_pages(posts))

    for name, path, section in [("home", "", None), ("about", "about-ben-chostner", "about"), ("forecast", "forecast", "forecast"),
                                ("search", "forecast/search", "forecast")]:
        meta, body = front_matter((SRC / "pages" / f"{name}.html").read_text())
        body = body.replace("{{posts}}", post_list)
        facts = json.loads((ROOT / "output" / "site_facts.json").read_text()) if (ROOT / "output" / "site_facts.json").exists() else {}
        def _fact(m):
            if m.group(1) not in facts:
                raise SystemExit(f"{name}.html: unknown fact {m.group(1)}")
            return facts[m.group(1)]
        body = re.sub(r"\{\{fact:([a-z0-9_]+)\}\}", _fact, body)
        body = body.replace("{{levers_chart}}", levers_chart())
        out = page(meta["title"], meta["description"], path, rewrite_links(body, name), section, meta.get("image"))
        (DIST / ((path or "index") + ".html")).parent.mkdir(parents=True, exist_ok=True)
        (DIST / ((path or "index") + ".html")).write_text(out)

    insights = page("Brookline Insights", "Essays and analyses on Brookline's finances and future by Ben Chostner.",
                    "brookline-insights",
                    '<header class="masthead"><p class="eyebrow">Writing</p><h1 class="title">Brookline Insights</h1>'
                    '<p class="standfirst">Essays and analyses on how Brookline got here, the state of things today, '
                    'and how we might chart a sustainable and thriving future.</p></header>' + post_list,
                    "writing", "img/whitepaper-chart.png")
    (DIST / "brookline-insights.html").write_text(insights)

    (DIST / "forecast").mkdir(exist_ok=True)
    for path, src in FORECAST_PAGES.items():
        (DIST / (path + ".html")).write_text(wrap_forecast_page(path, src))
    # the reorganized pages (docs/site, scripts/build_pages.py)
    for path, src in NEW_PAGES.items():
        (DIST / path).parent.mkdir(parents=True, exist_ok=True)
        (DIST / (path + ".html")).write_text(wrap_forecast_page(path, src))
    shutil.copy2(EXCEL, DIST / "forecast" / EXCEL.name)
    shutil.copy2(ROOT / "Brookline_Enrollment_Explained.xlsx", DIST / "forecast" / "Brookline_Enrollment_Explained.xlsx")

    maps()
    seats_map()

    # search index over the pages marked data-pagefind-body
    subprocess.run(["npx", "-y", PAGEFIND, "--site", str(DIST)], check=True,
                   stdout=subprocess.DEVNULL)

    notfound = page("Page not found", "This page does not exist.", "404",
                    '<header class="masthead"><h1 class="title">Page not found</h1>'
                    '<p class="standfirst">That page is not here. Try the <a href="/">home page</a> or '
                    'the <a href="/forecast">forecast</a>.</p></header>')
    (DIST / "404.html").write_text(notfound)

    urls = [""] + ["about-ben-chostner", "brookline-insights", "forecast"] + list(FORECAST_PAGES) + \
           ["post/" + p["slug"] for p in posts] + ["maps"]
    (DIST / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
        "".join(f"  <url><loc>{SITE}/{u}</loc></url>\n" for u in urls) + "</urlset>\n")
    (DIST / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n")
    (DIST / "vercel.json").write_text(json.dumps({
        "cleanUrls": True,
        "trailingSlash": False,
        "redirects": [
            {"source": "/inquiry-services-page", "destination": "/about-ben-chostner", "permanent": True},
            {"source": "/blog", "destination": "/brookline-insights", "permanent": True},
            {"source": "/maps/index", "destination": "/maps", "permanent": True},
            {"source": "/forecast/what-decides", "destination": "/forecast/base-case", "permanent": True},
            {"source": "/forecast/what-drives", "destination": "/forecast/base-case", "permanent": True},
            *({"source": k, "destination": v, "permanent": True} for k, v in RETIRED.items()),
            {"source": "/forecast/Brookline_Fiscal_Model.xlsx", "destination": "/forecast/Brookline_Forecast_Model.xlsx", "permanent": True},
        ],
        "rewrites": [{"source": "/maps", "destination": "/maps/index.html"}],
        "headers": [{"source": "/maps/data/(.*)", "headers": [{"key": "Cache-Control", "value": "public, max-age=86400"}]}],
    }, indent=2))

    # Vercel Web Analytics (enabled 2026-10-15): page views only, no cookies. Added to every built
    # page, including the maps and the docs pages, so no page family can be missed.
    analytics = ('<script>window.va = window.va || function () { (window.vaq = window.vaq || []).push(arguments); };</script>\n'
                 '<script defer src="/_vercel/insights/script.js"></script>\n')
    for f in DIST.rglob("*.html"):
        html = f.read_text()
        if "/_vercel/insights/script.js" not in html and "</head>" in html:
            f.write_text(html.replace("</head>", analytics + "</head>", 1))

    n = sum(1 for _ in DIST.rglob("*.html"))
    size = sum(f.stat().st_size for f in DIST.rglob("*") if f.is_file()) / 1e6
    print(f"Built {DIST}: {n} pages, {size:.1f} MB")
    if unlinked:
        print("Links to Artifacts not on the site, turned into plain text:")
        for where, aid, label in unlinked:
            print(f"  {where}: {aid}  '{label.strip()[:60]}'")


if __name__ == "__main__":
    sys.exit(main())
