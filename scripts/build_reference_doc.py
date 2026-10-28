"""
Generates `docs/reference_document.html` from `docs/reference_document.md`.

Why this exists: the reference document lives in two places — a markdown
working copy and a styled web page — and on 2026-09-06 they drifted, with
the HTML carrying a correction the markdown didn't. With the document
about to grow to four parts plus an article, keeping them in sync by hand
is a losing game. **The markdown is now the single source of truth for
prose; this script produces the HTML.**

## The problem this has to solve

The page's charts are hand-written interactive SVG (five of them, ~51KB of
JavaScript) and markdown cannot express them. A naive markdown-to-HTML
conversion would destroy them. So prose and charts are kept separate and
rejoined here:

- **Prose** lives in `reference_document.md`, and is the thing anyone edits.
- **Charts** live in `docs/_build/` — `charts.js` (the drawing code, lifted
  verbatim from the hand-built page) and `chart_blocks.json` (each chart's
  surrounding HTML: heading, `<svg>`, tooltip div, data-table toggle).
- **The design system** — fonts, CSS custom properties, light/dark tokens —
  lives in `docs/_build/shell_head.html`, also lifted verbatim, so the
  generated page is visually identical to the hand-built ones.

A chart is placed in the prose with a line containing only:

    {{chart:funds-sankey}}

## What this deliberately does NOT do

It does not regenerate the charts or their data. Those are hand-built,
validated, and stable; this only re-hosts them. If a chart's numbers
change, that is still an edit to `charts.js`.

Usage:
    python3 scripts/build_reference_doc.py
    python3 scripts/build_reference_doc.py --check   # verify sync, no write
"""
import json
import re
import sys
from pathlib import Path

import markdown

ROOT = Path(__file__).parent.parent
DOCS = ROOT / "docs"
BUILD = DOCS / "_build"
# Two documents share this pipeline: the long-form reference document and the
# short article distilled from it. Both are markdown-source-of-truth, both get
# the same design-system shell and the same chart blocks. `--doc` picks one.
DOCUMENTS = {
    "reference": {
        "src": DOCS / "reference_document.md",
        "out": DOCS / "reference_document.html",
        "title": "Brookline Town Finances",
        "toc": True,
        "footer": (
            "Reference document for the Brookline Town Finances project. "
            "Generated from <code>docs/reference_document.md</code> — edit the "
            "markdown, not this file."
        ),
    },
    "article": {
        "src": DOCS / "article.md",
        "out": DOCS / "article.html",
        "title": "Will Brookline Need a Sixth Override?",
        # Too short to need one, and a TOC on a 1,500-word piece reads as
        # padding.
        "toc": False,
        "footer": (
            "Generated from <code>docs/article.md</code> — edit the markdown, "
            "not this file."
        ),
    },
    # Added 2026-10-06: what new growth is, what the base case assumes, what it
    # costs, and what faster or slower growth does. Figures from
    # scripts/new_growth_page_data.js.
    "growth": {
        "src": DOCS / "new_growth.md",
        "out": DOCS / "new_growth.html",
        "title": "New Homes and Brookline's Budget",
        "toc": False,
        # one of the short reads: gets their opening (series label, question, summary box)
        "series_path": "forecast/new-growth",
        "question": "What does a new home cost the Town, now that enrollment is falling?",   # as in build_pages.EXTERNAL
        "footer": (
            "Generated from <code>docs/new_growth.md</code> — edit the markdown, "
            "not this file."
        ),
    },
}

SRC_MD = DOCUMENTS["reference"]["src"]
OUT_HTML = DOCUMENTS["reference"]["out"]

SHELL_HEAD = BUILD / "shell_head.html"
CHART_BLOCKS = BUILD / "chart_blocks.json"
CHARTS_JS = BUILD / "charts.js"

# `{{chart:id}}` places a chart. `{{chart:id|caption}}` also replaces that
# chart's subtitle, which the article needs: the blocks were written for the
# reference document and some captions refer to "the chart above," which is
# false in a document that places only one of them.
# [ \t]*, not \s*: \s* also ate the blank line after the placeholder, so a list or paragraph
# right after a chart ran into the chart's paragraph (the decisions page, 2026-10-15).
CHART_RE = re.compile(r"^\{\{chart:([a-z0-9-]+)(?:\|([^}]*))?\}\}[ \t]*$", re.M)
SUB_RE = re.compile(r'(<p class="sub">).*?(</p>)', re.S)

# Markdown gives us bare <h2>/<p>/<table>; the hand-built pages use the
# design system's own classes. This maps one to the other so generated
# output is indistinguishable from hand-written.
# Note these must tolerate attributes: the `toc` extension stamps an
# id onto every heading, so the tags arrive as `<h2 id="...">`, not `<h2>`.
CLASS_MAP = [
    (r"<h1(\s[^>]*)?>", r'<h1 class="title"\1>'),
    (r"<h2(\s[^>]*)?>", r'<h2 class="section-title"\1>'),
    (r"<h3(\s[^>]*)?>", r'<h3 class="sub"\1>'),
    (r"<h4(\s[^>]*)?>", r'<h4 class="sub"\1>'),
    (r"<table(\s[^>]*)?>", r'<table class="data-table"\1>'),
]


def build_toc(html, deep=False, minutes=None):
    """Jump-link TOC from the h2s; with `deep`, each h2's h3s nested under it, for the long pages.
    `minutes`, when given, is shown as the reading time."""
    heads = re.findall(r'<h([23]) class="(?:section-title|sub)" id="([^"]+)">(.*?)</h\1>', html, re.S)
    if not any(lv == "2" for lv, _, _ in heads):
        return ""
    clean = lambda t: re.sub(r"<[^>]+>", "", t).strip()
    items, open_sub = [], False
    for lv, hid, title in heads:
        if lv == "2":
            if open_sub:
                items.append("        </ol></li>")
                open_sub = False
            elif items:
                items[-1] += "</li>"
            items.append(f'      <li><a href="#{hid}">{clean(title)}</a>')
        elif deep and items:
            if not open_sub:
                items.append('        <ol class="toc-sub">')
                open_sub = True
            items.append(f'          <li><a href="#{hid}">{clean(title)}</a></li>')
    items.append("        </ol></li>" if open_sub else items.pop() + "</li>")
    head = "Contents" + (f" &middot; about {minutes} minutes to read" if minutes else "")
    return (
        f'<nav class="toc">\n    <p class="toc-head">{head}</p>\n'
        "    <ol>\n" + "\n".join(items) + "\n    </ol>\n  </nav>\n"
    )


def render(doc=None):
    doc = doc or DOCUMENTS["reference"]
    src_md, title = doc["src"], doc["title"]
    if doc.get("md") is None and not src_md.exists():
        raise SystemExit(f"missing source: {src_md}")
    for required in (SHELL_HEAD, CHART_BLOCKS, CHARTS_JS):
        if not required.exists():
            raise SystemExit(
                f"missing build asset: {required}\n"
                "These are extracted from the hand-built pages; see the module docstring."
            )

    # pages built by build_pages.py arrive already preprocessed
    md_text = doc["md"] if doc.get("md") is not None else src_md.read_text()
    # model numbers come from output/site_facts.json (scripts/site_facts.js), as on the
    # short reads, so a model change updates them; an unknown fact stops the build
    _facts = json.loads((ROOT / "output" / "site_facts.json").read_text())
    def _fact(m):
        if m.group(1) not in _facts:
            raise SystemExit(f"unknown fact {m.group(1)} in {src_md}")
        return _facts[m.group(1)]
    md_text = re.sub(r"\{\{fact:([a-z0-9_]+)\}\}", _fact, md_text)
    blocks = json.loads(CHART_BLOCKS.read_text())

    # Pull chart placeholders out before markdown runs, so it can't mangle
    # them, and put the real HTML back afterwards.
    placeholders, missing = {}, []

    def stash(m):
        cid, caption = m.group(1), m.group(2)
        if cid not in blocks:
            missing.append(cid)
            return ""
        block = blocks[cid]
        if caption:
            block, n = SUB_RE.subn(rf"\g<1>{caption.strip()}\g<2>", block, count=1)
            if not n:
                raise SystemExit(
                    f"chart {cid!r} has no <p class=\"sub\"> to override"
                )
        key = f"CHARTPLACEHOLDER{len(placeholders)}X"
        placeholders[key] = block
        return key

    md_text = CHART_RE.sub(stash, md_text)
    if missing:
        raise SystemExit(
            f"unknown chart id(s): {', '.join(missing)}\n"
            f"available: {', '.join(sorted(blocks))}"
        )

    # "footnotes" added 2026-09-22 for the [^name] syntax; it is inert on any
    # document that doesn't use it, and nothing here did before that date.
    body = markdown.markdown(
        md_text,
        extensions=["tables", "toc", "attr_list", "sane_lists", "footnotes", "md_in_html"],
    )
    for pat, repl in CLASS_MAP:
        body = re.sub(pat, repl, body)

    # A document in the short-read series opens the way the short reads do (build_pages.opening):
    # "Short read N of M" above the title, the question under it, and the summary in a box.
    if doc.get("series_path"):
        series = [c["path"] for c in json.loads((DOCS / "site" / "series.json").read_text())]
        label = (f"Short read {series.index(doc['series_path']) + 1} of {len(series)}"
                 if doc["series_path"] in series else "Topic")
        body = re.sub(r'(<h1 class="title"[^>]*>.*?</h1>)',
                      lambda m: f'<p class="eyebrow-layer">{label}</p>\n{m.group(1)}'
                      + (f'\n<p class="question">{doc["question"]}</p>' if doc.get("question") else ""),
                      body, count=1, flags=re.S)
        body, n = re.subn(r'<h2 class="section-title" id="summary">Summary</h2>\s*(<ul>.*?</ul>)',
                          r'<div class="summary">\1</div>', body, count=1, flags=re.S)
        if not n:
            raise SystemExit(f"{doc['src'].name}: no '## Summary' list to box")

    # Screen readers (2026-10-08 accessibility pass): every prose table's column headers get
    # scope="col", the first cell of each body row becomes a row header, and an empty top-left
    # header cell gets hidden text so no data cell is left without a header.
    def _table_headers(m):
        t = m.group(0)
        t = re.sub(r"<th(?=[\s>])(?![^>]*scope)([^>]*)>", r'<th scope="col"\1>', t)
        t = re.sub(r'<th scope="col"([^>]*)>\s*</th>', r'<th scope="col"\1><span class="sr-only">Item</span></th>', t)
        head, sep, tail = t.partition("<tbody>")
        tail = re.sub(r"<tr>\s*<td([^>]*)>(.*?)</td>", r'<tr>\n<th scope="row"\1>\2</th>', tail, flags=re.S)
        # a row whose header cell is all bold (Brookline among its peers, a total) gets a highlight
        tail = re.sub(r'<tr>(\s*<th scope="row"[^>]*>\s*<strong>[^<]*</strong>\s*</th>)', r'<tr class="hl">\1', tail)
        # cells of three or more words are text, not numbers: align them left
        def _align(c):
            words = re.sub(r"<[^>]+>", " ", c.group(2)).split()
            if len(words) >= 3 and "style=" not in c.group(1):
                return f'<td{c.group(1)} style="text-align:left">{c.group(2)}</td>'
            return c.group(0)
        tail = re.sub(r"<td([^>]*)>(.*?)</td>", _align, tail, flags=re.S)
        return head + sep + tail
    body = re.sub(r'<table class="data-table"[^>]*>.*?</table>', _table_headers, body, flags=re.S)

    # Every prose table gets its own horizontal-scroll container. Without
    # this a single wide table pushes the whole page sideways - one wide
    # table in 3d made the entire document scroll horizontally (found
    # 2026-09-07). A table still has to be readable at the prose column's
    # width; this is the backstop, not a licence to write wide tables.
    # NOT `.data-table-wrap`: that class belongs to the chart blocks' own
    # collapsible data tables and is `display:none` until its toggle button
    # opens it, so reusing it silently hid all eleven prose tables.
    body, n_wrapped = re.subn(
        r'(<table class="data-table"[^>]*>.*?</table>)',
        r'<div class="prose-table-wrap" tabindex="0" role="region" aria-label="Table">\1</div>',
        body,
        flags=re.S,
    )

    # charts sit outside the narrow prose column, like the hand-built pages
    for key, block in placeholders.items():
        body = body.replace(
            f"<p>{key}</p>", f'</div>\n  <div class="wide">\n{block}\n  </div>\n  <div class="wrap">'
        ).replace(key, f'</div>\n  <div class="wide">\n{block}\n  </div>\n  <div class="wrap">')

    render.tables_wrapped = n_wrapped
    toc = build_toc(body, deep=doc.get("toc_deep", False), minutes=doc.get("minutes")) if doc["toc"] else ""
    head = SHELL_HEAD.read_text().replace(
        "<title>Brookline&rsquo;s Fiscal Machine</title>",
        f"<title>{title}</title>",
    ).replace(
        "<title>Brookline's Fiscal Machine</title>",
        f"<title>{title}</title>",
    )

    extra_css = """
<style>
  .toc { max-width: 720px; margin: 0 auto 48px; padding: 20px 24px;
         background: var(--paper-card); border: 1px solid var(--paper-card-border);
         border-radius: 6px; }
  .toc-head { font-family: var(--font-mono); font-size: 12px; letter-spacing: .06em;
              text-transform: uppercase; color: var(--pine); margin: 0 0 10px; font-weight: 600; }
  .toc ol { margin: 0; padding-left: 1.4em; }
  .toc li { margin-bottom: 6px; font-size: 15px; }
  .page-guide { border-left: 3px solid var(--pine); padding: 4px 0 4px 16px; margin: 0 0 36px; }
  .page-guide-head { font-family: var(--font-mono); font-size: 12px; letter-spacing: .06em; text-transform: uppercase;
                     color: var(--pine); margin: 0 0 6px; font-weight: 600; }
  .page-guide ul { margin: 0; padding-left: 1.1em; }
  .page-guide li { font-size: 15px; margin-bottom: 4px; color: var(--ink-muted); }
  .toc ol.toc-sub { margin: 4px 0 6px; padding-left: 1.2em; list-style: lower-alpha; }
  .toc ol.toc-sub li { margin-bottom: 2px; font-size: 14px; color: var(--ink-muted); }
  .generated-note { max-width: 720px; margin: 0 auto 28px; padding: 0 24px;
                    font-family: var(--font-mono); font-size: 11.5px; color: var(--ink-faint); }
  .prose-table-wrap { overflow-x: auto; }
  /* the short reads' opening, as in build_pages.PAGE_CSS */
  .eyebrow-layer { font-family: var(--font-mono); font-size: 12px; letter-spacing: .08em;
                   text-transform: uppercase; color: var(--pine); margin: 0 0 6px; font-weight: 600; }
  .question { font-family: var(--font-display); font-style: italic; font-size: 1.2rem;
              color: var(--ink-muted); margin: -6px 0 18px; }
  .summary { background: var(--paper-card); border: 1px solid var(--paper-card-border);
             border-radius: 6px; padding: 14px 22px 4px; margin: 0 0 36px; }
  .summary ul { margin: 0 0 10px; }
  /* headers and row labels may wrap, so narrow tables fit a phone without scrolling */
  /* text cells wrap so a table fits the column instead of scrolling; numbers rarely contain
     spaces, so they stay on one line */
  .prose-table-wrap table.data-table th, .prose-table-wrap table.data-table td { white-space: normal; }
  .prose-table-wrap th { vertical-align: bottom; }
  @media (max-width: 560px) { .prose-table-wrap th, .prose-table-wrap td { padding: 5px 6px; } }
  /* The shell has no blockquote rule - markdown uses them for pull-quotes
     and set-off formulas (3c's breakeven test), which rendered as a bare
     indent. */
  .wrap blockquote { margin: 22px 0; padding: 2px 0 2px 20px;
                     border-left: 3px solid var(--pine); color: var(--ink); }
  .wrap blockquote p { margin: 0; }
  /* Endnotes (markdown "footnotes" extension, added 2026-09-22). The
     extension appends them to the end of the body; the shell had no rule,
     so they rendered at full body size with no heading. */
  .footnote { max-width: 720px; margin: 48px auto 0; padding: 0 24px;
              font-size: 14.5px; color: var(--ink-faint); }
  .footnote hr { border: 0; border-top: 1px solid var(--paper-card-border);
                 margin: 0 0 12px; }
  .footnote::before { content: "Notes"; display: block;
                      font-family: var(--font-mono); font-size: 12px;
                      letter-spacing: .06em; text-transform: uppercase;
                      color: var(--pine); font-weight: 600; margin-bottom: 10px; }
  .footnote ol { padding-left: 1.4em; }
  .footnote li { margin-bottom: 10px; }
  .footnote li p { margin: 0; }
  .wrap sup a.footnote-ref { text-decoration: none; font-weight: 600; }
</style>
"""

    # The chart code is lifted verbatim from the hand-built pages, where every
    # chart was always present. Here the markdown decides which charts appear,
    # so a draw function whose <svg> is absent must no-op instead of throwing —
    # one uncaught error kills every chart after it in the render sequence
    # (exactly the failure that blanked three charts on 2026-09-06). This is a
    # mechanical guard inserted at build time, so re-extracting charts.js from
    # the source pages stays a straight copy.
    charts_js = CHARTS_JS.read_text()
    charts_js, n_guards = re.subn(
        r'(var svg = document\.getElementById\("[a-z0-9-]+"\);)',
        r"\1 if (!svg) return;",
        charts_js,
    )
    render.guards = n_guards

    html = f"""{head}
{extra_css}
<main>
  <div class="wrap">
{body}
  </div>
</main>

<footer>
  <div class="wrap">
    <p>{doc["footer"]}</p>
  </div>
</footer>

<script>
{charts_js}
</script>
"""
    # TOC goes after the first h1
    m = re.search(r"</h1>", html)
    if toc and m:
        html = html[: m.end()] + "\n  </div>\n  " + toc + '  <div class="wrap">\n' + html[m.end():]
    return html


def main():
    check = "--check" in sys.argv
    # `--doc reference|article|all`; default builds both, so a change to the
    # shared shell or chart blocks can never leave one document behind.
    which = "all"
    if "--doc" in sys.argv:
        which = sys.argv[sys.argv.index("--doc") + 1]
    names = list(DOCUMENTS) if which == "all" else [which]
    if any(n not in DOCUMENTS for n in names):
        raise SystemExit(f"--doc must be one of: {', '.join(DOCUMENTS)}, or all")

    stale = []
    for name in names:
        doc = DOCUMENTS[name]
        if not doc["src"].exists():
            if which == "all":
                continue  # article may not be written yet
            raise SystemExit(f"missing source: {doc['src']}")
        html = render(doc)
        out = doc["out"]
        if check:
            if not out.exists() or out.read_text() != html:
                stale.append(out.name)
            continue
        out.write_text(html)
        n_charts = len(CHART_RE.findall(doc["src"].read_text()))
        print(f"Wrote {out}")
        print(f"  {len(html):,} chars, {n_charts} chart(s) embedded")
        print(f"  {render.guards} draw function(s) guarded against a missing <svg>")
        print(f"  {render.tables_wrapped} prose table(s) wrapped in a scroll container")

    if check:
        if stale:
            print("OUT OF SYNC: " + ", ".join(stale) + " differ from their markdown")
            raise SystemExit(1)
        print("in sync")


if __name__ == "__main__":
    main()
