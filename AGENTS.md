# Notes for an AI assistant working in this repository

This repository is the forecast behind brooklinefuture.org: Brookline, Massachusetts' General Fund from FY2026 to FY2040. Read `README.md` first for the layout. This file covers how to work in it without breaking it.

## The one command

```
python3 scripts/rebuild_all.py
```

Run it after any change to a script, an input or a page. It reruns every step in order, stops at the first failed check, and writes `output/rebuild_report.md`. The report lists every published number that changed and any typed number that still shows an old value. Read it before you call a change done. `--skip-workbook` skips the slow Excel checks while you iterate; run the full version before you finish.

## Rules the model follows

- **The forecast exists three times and they must agree.** The Python model is `scripts/expense_driver_forecast.py`. The JavaScript engine that runs the Explorer is `docs/_build/dashboard_engine.js`. The Excel workbook is written by `scripts/build_explorer_workbook.py`. A change to the logic of one needs the same change in the other two. The rebuild checks the Explorer against Python (114 cases, within $5) and the workbook against the Explorer (a gap of a few dollars is rounding).
- **The base case continues what has been observed.** Every base case assumption comes from Brookline's own history since about FY2011 or from a decision the Town has already made. Something favorable that hasn't happened yet, such as the freed pension money or faster growth, is a lever the reader can try, not part of the base case. A forecast with a large surplus loses credibility with the people it's meant for.
- **Growth rates compound, so keep levels and increments apart.** When a quantity grows on top of itself, write the level and the yearly change separately, and check the long-run growth rate it implies before you trust it. Never add nominal dollars from different years without growing each forward first.
- **Every published number comes from the model.** Page text writes numbers as `{{fact:name}}`, filled from `output/site_facts.json`, which `scripts/site_facts.js` produces. Add a fact there rather than typing a number into a page. Typed numbers go stale silently.
- **Sources are cited where they're used.** Constants in the scripts carry a comment naming the document and page they came from. Keep doing that, and add new files in `data/` to `data/SOURCES.md`.

## Charts

The drawing code is `docs/_build/charts.js`, with captions in `docs/_build/chart_blocks.json`. Chart data is written into `charts.js` by `scripts/sync_chart_data.py`; don't edit the data blocks by hand. After a change to a chart, run:

```
node scripts/chart_qa.mjs docs/article.html
```

It reports labels that run off the chart or overlap, which a successful build doesn't catch.

## Writing for the site

The pages are in `docs/site/pages/*.md`. Their readers are residents and Town Meeting Members, not finance specialists.

- Plain, complete sentences. Explain a term the first time it's used.
- Don't tell readers what they know, find confusing or will find surprising.
- No em dashes; use a comma, semicolon or colon.
- American spelling.
- Don't name individual Chapter 40B projects.
- Don't attribute motives to people in the data; describe the mechanism that's measured.

## What isn't here

Private working notes, one developer's project model, the Town's building permit records, and the names of property owners in the assessment records are left out; `DATA.md` lists them. Three rebuild steps read the permit records; here they're skipped and their saved outputs are used. Some comments mention a `.claude/memorialized.md` file, the author's private decision log, which isn't included either. The map pages on the live site (/maps) are built by a separate project and aren't in this repository; the site build skips them when they're absent.
