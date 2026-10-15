"""
Builds the reorganized forecast pages (docs/site/pages/*.md) into docs/site/build/*.html.

Each page is markdown with a short header of fields, between --- lines:

    slug: budget-to-2040          the page's id, used for links
    path: forecast/budget-to-2040  where it lives on the site
    title: Why Brookline keeps needing overrides
    layer: short                   front | short | topic | how
    question: Does the override solve Brookline's budget problem?
    answer: For now. ...           one sentence, shown in bold at the top
    summary:                       3 to 5 bullets, shown under the answer
    - ...
    related: what-drives, topic-forecast
    updated: 2026-10-07

The header becomes the same opening on every page: the layer, the title, the question, the
answer in bold, and the summary. The body then uses five markers, all checked at build time
so a broken one stops the build instead of reaching the site:

    {{fact:room_fy2040}}     a model number from output/site_facts.json (scripts/site_facts.js)
    {{chart:decisions}}      a chart from docs/_build/chart_blocks.json
    {{include:walk}}         a shared table or passage from docs/site/partials/walk.md
    [[levy limit]]           a glossary term, linked to its definition (or [[term|shown text]])
    [text](@slug#anchor)     a link to another page by its slug
    {{source:key}}           a link to an entry on the data and sources page

Usage:  python3 scripts/build_pages.py [--check]
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import build_reference_doc as brd

ROOT = Path(__file__).parent.parent
SITE = ROOT / "docs" / "site"
PAGES, PARTIALS, OUT = SITE / "pages", SITE / "partials", SITE / "build"
FACTS = ROOT / "output" / "site_facts.json"
SITE_DATA = ROOT / "output" / "site_data.json"
# Pages built elsewhere that the new pages link to by slug.
EXTERNAL = {
    "new-homes": {"slug": "new-homes", "path": "forecast/new-growth", "title": "New homes and Brookline's budget",
                  "question": "What does a new home cost the Town, now that enrollment is falling?", "layer": "topic"},
    "explorer": {"slug": "explorer", "path": "forecast/explorer", "title": "Forecast Explorer",
                 "question": "What happens to the budget under your own assumptions?", "layer": "tool"},
    "maps": {"slug": "maps", "path": "maps", "title": "Land value and growth maps",
             "question": "Where in Brookline did new growth come from?", "layer": "tool"},
}
LAYER_LABEL = {"front": "Brookline's finances to 2040", "short": "Short read", "topic": "Topic",
               "how": "How we know", "tool": "Tool"}


def parse(path):
    text = path.read_text()
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        raise SystemExit(f"{path.name}: missing header")
    head, key = {}, None
    for line in m.group(1).splitlines():
        if line.startswith("- ") and key:
            head.setdefault(key, []).append(line[2:].strip())
        elif ":" in line:
            key, val = line.split(":", 1)
            key, val = key.strip(), val.strip()
            head[key] = val if val else []
    for req in ("slug", "path", "title", "layer"):
        if req not in head:
            raise SystemExit(f"{path.name}: header needs {req}")
    head["body"] = text[m.end():]
    head["file"] = path
    return head


def slugify(term):
    # match the heading ids Markdown's toc extension writes: NFKD, then ASCII only, so "2½"
    # becomes "212" rather than "2"
    term = unicodedata.normalize("NFKD", term).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", term.lower()).strip("-")


def load_glossary(pages):
    g = next((p for p in pages.values() if p["slug"] == "glossary"), None)
    if not g:
        return None, set()
    terms = set(slugify(t) for t in re.findall(r"^### (.+)$", g["body"], re.M))
    return g, terms


def preprocess(page, pages, facts, glossary_terms, sources):
    body, errors = page["body"], []

    def include(m):
        f = PARTIALS / f"{m.group(1)}.md"
        if not f.exists():
            errors.append(f"unknown include {m.group(1)}")
            return ""
        return f.read_text()
    body = re.sub(r"\{\{include:([a-z0-9-]+)\}\}", include, body)

    def fact(m):
        k = m.group(1)
        if k not in facts:
            errors.append(f"unknown fact {k}")
            return "??"
        return facts[k]
    body = re.sub(r"\{\{fact:([a-z0-9_]+)\}\}", fact, body)

    def gloss(m):
        term, shown = m.group(1), m.group(2) or m.group(1)
        s = slugify(term)
        if glossary_terms and s not in glossary_terms:
            errors.append(f"glossary has no term {term!r}")
        return f'<a class="gloss" href="/forecast/glossary#{s}">{shown}</a>'
    body = re.sub(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]", gloss, body)

    def link(m):
        text, slug, anchor = m.group(1), m.group(2), m.group(3) or ""
        if slug not in pages:
            errors.append(f"link to unknown page {slug}")
            return text
        return f"[{text}](/{pages[slug]['path']}{anchor})"
    body = re.sub(r"\[([^\]]+)\]\(@([a-z0-9-]+)(#[a-z0-9-]+)?\)", link, body)

    def source(m):
        k = m.group(1)
        if sources is not None and k not in sources:
            errors.append(f"unknown source {k}")
        return f'<a class="src" href="/forecast/sources#{k}">source</a>'
    body = re.sub(r"\{\{source:([a-z0-9-]+)\}\}", source, body)
    return body, errors


# Pages on one subject, with the question each answers, shown as a guide near the top of each
# (Ben, 2026-10-13: the growth pages are several angles on one subject, and readers need to know
# which to open). The same box is pasted into docs/new_growth.md (built separately); update both.
GUIDES = {
    "growth": ("The growth pages", [
        ("topic-growth-links", "The town-wide view: what growth adds, what it has cost, and how much room each service has"),
        ("new-homes", "What a new home costs when its children fill open seats, school by school"),
        ("topic-growth", "When a single new home pays for itself, by type and tenure"),
        ("topic-growth-value", "Where new growth comes from, renovation above all, and what faster growth is worth"),
        ("topic-homes", "How many homes Brookline adds, counted five ways"),
    ]),
}


def guide(page, pages):
    g = GUIDES.get(page.get("guide") or "")
    if not g:
        return []
    items = []
    for slug, what in g[1]:
        p = pages[slug]
        items.append(f'<li><strong>{p["title"]}</strong> (this page): {what}</li>' if slug == page["slug"]
                     else f'<li><a href="/{p["path"]}">{p["title"]}</a>: {what}</li>')
    return [f'<nav class="page-guide" aria-label="{g[0]}"><p class="page-guide-head">{g[0]}</p><ul>',
            *items, "</ul></nav>", ""]


def opening(page, pages):
    """The standard top of every page, from its header."""
    label = LAYER_LABEL.get(page["layer"], "")
    series = [c["path"] for c in json.loads((SITE / "series.json").read_text())]
    if page.get("path") in series:
        label = f"Short read {series.index(page['path']) + 1} of {len(series)}"
    out = [f'<p class="eyebrow-layer">{label}</p>',
           f'# {page["title"]}', ""]
    if page.get("question"):
        out += [f'<p class="question">{page["question"]}</p>', ""]
    if page.get("answer"):
        out += [f'> **{page["answer"]}**', ""]
    if page.get("summary"):
        out += ['<div class="summary" markdown="1">', "", *[f"- {b}" for b in page["summary"]], "", "</div>", ""]
    out += guide(page, pages)
    return "\n".join(out)


def closing(page, pages):
    rel = [s.strip() for s in (page.get("related") or "").split(",") if s.strip()] \
        if isinstance(page.get("related"), str) else page.get("related") or []
    out = []
    if rel:
        items = []
        for s in rel:
            if s not in pages:
                raise SystemExit(f"{page['file'].name}: related page {s} unknown")
            p = pages[s]
            items.append(f'- [{p["title"]}](/{p["path"]}){": " + p["question"] if p.get("question") else ""}')
        # the chapter footer (website/scripts/build_site.py) goes here, ahead of Go deeper, so
        # readers are invited to the next chapter before the technical pages
        out += ["", "<!--series-nav-->", "", "## Go deeper", "", *items]
    if page.get("updated"):
        out += ["", f'<p class="updated">Last updated {page["updated"]}. '
                    f'<a href="/forecast/changes">What has changed</a>.</p>']
    return "\n".join(out)


PAGE_CSS = """
<style>
  .eyebrow-layer { font-family: var(--font-mono); font-size: 12px; letter-spacing: .08em;
                   text-transform: uppercase; color: var(--pine); margin: 0 0 6px; font-weight: 600; }
  .question { font-family: var(--font-display); font-style: italic; font-size: 1.2rem;
              color: var(--ink-muted); margin: -6px 0 18px; }
  .summary { background: var(--paper-card); border: 1px solid var(--paper-card-border);
             border-radius: 6px; padding: 14px 22px 4px; margin: 0 0 36px; }
  .summary ul { margin: 0 0 10px; }
  .page-guide { border-left: 3px solid var(--pine); padding: 4px 0 4px 16px; margin: -12px 0 36px; }
  .page-guide-head { font-family: var(--font-mono); font-size: 12px; letter-spacing: .06em; text-transform: uppercase;
                     color: var(--pine); margin: 0 0 6px; font-weight: 600; }
  .page-guide ul { margin: 0; padding-left: 1.1em; }
  .page-guide li { font-size: 15px; margin-bottom: 4px; color: var(--ink-muted); }
  a.gloss { text-decoration-style: dotted; text-decoration-color: var(--ink-faint); }
  a.src { font-family: var(--font-mono); font-size: 0.78em; vertical-align: 1px; }
  .wrap .prose-table-wrap { margin: 8px 0 26px; }
  .updated { font-family: var(--font-mono); font-size: 12.5px; color: var(--ink-faint); margin-top: 40px; }
  @media print { .skip-link { display: none; } }
</style>
"""


def build(check=False):
    pages = {}
    for f in sorted(PAGES.glob("*.md")):
        p = parse(f)
        if p["slug"] in pages:
            raise SystemExit(f"duplicate slug {p['slug']}")
        pages[p["slug"]] = p
    for k, v in EXTERNAL.items():
        pages.setdefault(k, dict(v, external=True, body=""))
    facts = json.loads(FACTS.read_text())
    site_data = SITE_DATA.read_text()
    _, gterms = load_glossary(pages)
    src_page = pages.get("sources")
    sources = set(re.findall(r'id="([a-z0-9-]+)"', src_page["body"])) if src_page else None
    OUT.mkdir(parents=True, exist_ok=True)
    all_errors, stale = [], []
    for slug, page in pages.items():
        if page.get("external"):
            continue
        full = dict(page, body=opening(page, pages) + "\n" + page["body"] + "\n" + closing(page, pages))
        md, errors = preprocess(full, pages, facts, gterms, sources)
        all_errors += [f"{page['file'].name}: {e}" for e in errors]
        html = brd.render({"src": page["file"], "md": md, "title": page["title"],
                           "toc": page["layer"] == "topic",
                           # long pages list their subsections and say how long they take to read
                           "toc_deep": len(page["body"].split()) > 4000,
                           "minutes": round(len(page["body"].split()) / 230 / 5) * 5 or None
                                      if len(page["body"].split()) > 4000 else None,
                           "footer": 'Part of <a href="/forecast">Brookline\'s finances to 2040</a>, an independent '
                                     'analysis by <a href="/about-ben-chostner">Ben Chostner</a>.'})
        html = html.replace("</head>", PAGE_CSS + "</head>", 1) if "</head>" in html else PAGE_CSS + html
        html = html.replace("</footer>\n", "</footer>\n<script>window.SITE_DATA = " + site_data + ";</script>\n", 1)
        out = OUT / f"{slug}.html"
        if check:
            if not out.exists() or out.read_text() != html:
                stale.append(out.name)
        else:
            out.write_text(html)
    if all_errors:
        raise SystemExit("build errors:\n  " + "\n  ".join(all_errors))
    if check and stale:
        raise SystemExit("out of date: " + ", ".join(stale))
    print(f"{'checked' if check else 'built'} {sum(1 for p in pages.values() if not p.get('external'))} page(s) into {OUT.relative_to(ROOT)}")
    return pages


if __name__ == "__main__":
    build("--check" in sys.argv)
