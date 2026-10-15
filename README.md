# Brookline's budget to 2040

This repository holds everything behind **[brooklinefuture.org](https://www.brooklinefuture.org)**: an independent forecast of the Town of Brookline, Massachusetts General Fund from FY2026 to FY2040. It includes the model, the data it reads, the checks that keep its three versions in agreement, and the source of every page on the site.

It was built by Ben Chostner, a Town Meeting Member for Precinct 9, working with Claude, an AI model made by Anthropic. It is not an official Town forecast. It's published so anyone can check how each number was reached, rerun it with different assumptions, or adapt it for another town.

## What's here

| Folder | What it holds |
|---|---|
| `scripts/` | The model and every step that builds on it. `expense_driver_forecast.py` is the forecast itself; `rebuild_all.py` runs everything in order. |
| `output/` | What the scripts produce: forecast tables (CSV), the numbers the site quotes (`site_facts.json`), and a methodology note beside most tables. |
| `data/` | The inputs the scripts read. `data/SOURCES.md` says where each came from; `DATA.md` explains what was left out and why. |
| `docs/site/pages/` | The text of the forecast pages, in Markdown. Numbers written as `{{fact:name}}` are filled in from `output/site_facts.json` when the site is built. |
| `docs/_build/` | The chart drawing code (`charts.js`), chart captions, and the Explorer's calculation engine (`dashboard_engine.js`). |
| `website/` | The site's page templates, styles and build scripts. |
| `Brookline_Fiscal_Model.xlsx` | An earlier spreadsheet model the build still reads. The current Excel version of the forecast, `Brookline_Forecast_Model.xlsx`, is built by `scripts/build_explorer_workbook.py`. |

## One model, three versions

The forecast exists in three forms that must give the same answer:

1. **Python** (`scripts/expense_driver_forecast.py`), the reference version.
2. **JavaScript** (`docs/_build/dashboard_engine.js`), which runs the Explorer in a reader's browser.
3. **Excel** (`scripts/build_explorer_workbook.py` writes it), with live formulas a reader can change.

`rebuild_all.py` checks that they agree: the Explorer against Python across 114 test cases, and the workbook against the Explorer after a full formula recalculation.

## Running it

You need Python 3.12 or newer and Node.js 20 or newer:

```
pip install -r requirements.txt
python3 scripts/rebuild_all.py
```

This reruns the forecast and every step after it, checks the results, and builds the site into `website/dist/`. It takes about four minutes. Two steps need more:

- **Google Chrome** draws the home page and forecast pictures and runs the accessibility and phone width check. The scripts look for it at the macOS location; on another system, change `CHROME` in `scripts/check_site_quality.py` and `website/scripts/takeaway_charts.py`.
- **The workbook checks** recalculate every formula in Python with the `formulas` package, so they need no Excel. They are the slow part; `python3 scripts/rebuild_all.py --skip-workbook` leaves them out.

To see the site, run `python3 website/scripts/serve.py 8000` and open http://localhost:8000.

When it finishes, `output/rebuild_report.md` lists every published number that changed and any page that still has the old number typed in by hand.

## Changing an assumption

The base case's settings are the `BASE` dictionary in `scripts/expense_driver_forecast.py`. Revenue inputs come from `scripts/baseline_revenue_forecast.py`, and new growth from `scripts/new_growth_scenario_forecast.py`. Change a setting, run `rebuild_all.py`, and read the rebuild report. If you change the Python model's logic rather than a setting, the Explorer and the workbook need the same change, or the checks will fail. That's on purpose.

For a quicker look, the Explorer on the site (/forecast/explorer) and the Excel workbook let you move the main assumptions without running anything.

## Using it with your own AI

`AGENTS.md` is written for an AI coding assistant (Claude Code, Codex, Cursor and others read it automatically). It explains the layout, the rules the model follows, and the checks to run after any change. A good first request is "Read AGENTS.md, run the rebuild, and explain how the base case reaches its FY2040 number."

## Adapting it for another town

The structure carries over: revenue under Proposition 2½, spending grouped by what drives it, and staff, pay, health premiums and enrollment each forecast from their own history. The numbers don't. Most of the Brookline-specific work is in `data/` and in the constants at the top of each script, and `data/SOURCES.md` shows what each one came from. Massachusetts towns can find most of the same inputs in the Division of Local Services' data and their own budget books.

## How this copy is kept current

This repository is a copy of the working project, refreshed each time the live site is updated, so it always matches what brooklinefuture.org shows. A short list of things is left out: private working notes, one developer's project model, the Town's building permit records, and the names of property owners in the assessment records. `DATA.md` lists them.

## License

The code is under the MIT License (`LICENSE`). The written content, meaning the page text, methodology notes and analysis, is under Creative Commons Attribution 4.0 (`LICENSE-CONTENT.md`). The data in `data/` comes from public sources, listed in `data/SOURCES.md`, under their own terms. Photographs of Ben on the site are not covered by either license.

Questions and corrections are welcome as GitHub issues.
