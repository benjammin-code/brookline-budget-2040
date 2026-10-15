/* Chart QA: a headless DOM stub that runs the real charts.js out of a built
   HTML page and reports per-chart geometry, so label overflow and collisions
   are caught without a browser.

     node scripts/chart_qa.mjs docs/reference_document.html
     node scripts/chart_qa.mjs docs/article.html
     DUMP=control-svg node scripts/chart_qa.mjs docs/reference_document.html

   Run it after every charts.js change. `python3 scripts/build_reference_doc.py`
   reports chart counts and passes happily while labels run off the canvas;
   this is the check that doesn't.

   Two things it deliberately gets right, both learned by getting them wrong:
   - Labels are measured with the *monospace* metrics the chart CSS actually
     uses (~0.605em per char, 12.5px for .sankey-label and 11px for .pct).
     A generic 6px/char estimate under-reports overflow badly.
   - A draw function still runs when its <svg> is absent from the page (the
     build guards them), so a chart with no viewBox here is SKIPPED rather
     than measured against an invented default. Measuring against a default
     produced a screenful of false positives on the article.

   Validate any change to this file with a positive control: inject a
   deliberately over-long series name and confirm it gets flagged. */
import fs from "node:fs";

const HTML = process.argv[2];
const html = fs.readFileSync(HTML, "utf8");

// pull the inline charts.js out of the built page
const m = html.match(/<script>\s*\(function \(\) \{([\s\S]*?)\}\)\(\);\s*<\/script>/);
if (!m) { console.error("could not locate charts IIFE"); process.exit(1); }
const code = "(function () {" + m[1] + "})();";

const nodes = [];          // every svg element created, by svg id
let currentSvgId = null;

function makeEl(tag, attrs = {}) {
  const el = {
    tag, attrs: { ...attrs }, children: [], _text: "",
    style: {}, dataset: {}, classList: { add(){}, toggle(){return false;}, contains(){return false;} },
    setAttribute(k, v) { this.attrs[k] = v; },
    getAttribute(k) { return this.attrs[k]; },
    removeChild(c) { const i = this.children.indexOf(c); if (i >= 0) this.children.splice(i, 1); },
    appendChild(c) { this.children.push(c); c._parentSvg = this._parentSvg || this.id; nodes.push({ svg: c._parentSvg, el: c }); return c; },
    addEventListener() {},
    getBoundingClientRect() { return { left: 0, top: 0, width: 900, height: 500 }; },
    querySelectorAll() { return []; },
    get firstChild() { return this.children[0] || null; },
    set textContent(v) { this._text = String(v); },
    get textContent() { return this._text; },
    set innerHTML(v) { this._html = v; },
    get innerHTML() { return this._html || ""; }
  };
  return el;
}

const registry = {};
function reg(id) {
  if (!registry[id]) { const e = makeEl("svg"); e.id = id; e._parentSvg = id; registry[id] = e; }
  return registry[id];
}

const doc = {
  getElementById: (id) => reg(id),
  createElement: (t) => makeEl(t),
  createElementNS: (ns, t) => makeEl(t),
  querySelectorAll: () => [],
  documentElement: makeEl("html"),
  body: makeEl("body"),
  addEventListener() {}
};

const errors = [];
globalThis.document = doc;
globalThis.window = {
  addEventListener() {},
  matchMedia: () => ({ addEventListener() {} }),
  getComputedStyle: () => ({ getPropertyValue: () => "#888888" })
};
globalThis.setTimeout = (fn) => 0;
globalThis.clearTimeout = () => {};
globalThis.getComputedStyle = () => ({ getPropertyValue: () => "#888888" });

try { eval(code); } catch (e) { errors.push(e.stack || String(e)); }

if (errors.length) { console.log("JS ERRORS:\n" + errors.join("\n")); process.exit(1); }

// ---- geometry report ----
const bySvg = {};
for (const { svg, el } of nodes) {
  if (!svg) continue;
  (bySvg[svg] ||= []).push(el);
}

for (const svgId of Object.keys(bySvg).sort()) {
  const els = bySvg[svgId];
  const texts = els.filter(e => e.tag === "text" && e._text);
  const vb = (html.match(new RegExp('id="' + svgId + '"[^>]*viewBox="([^"]+)"')) || [])[1];
  // A draw function runs even when its <svg> isn't on this page (the build
  // guards them); without a real viewBox there's nothing to check against,
  // so skip rather than measure against a made-up default.
  if (!vb) { console.log(`\n=== ${svgId}  (not on this page, skipped) ===`); continue; }
  const [, , vbW, vbH] = vb.split(/\s+/).map(Number);
  console.log(`\n=== ${svgId}  (viewBox ${vbW}x${vbH}, ${els.length} nodes, ${texts.length} labels) ===`);

  const over = texts.filter(t => {
    const x = Number(t.attrs.x), y = Number(t.attrs.y);
    const anchor = t.attrs["text-anchor"];
    const w = t._text.length * (Number(t.attrs["font-size"]) || (String(t.attrs.class||"").includes("pct") ? 11 : 12.5)) * 0.605;
    const right = anchor === "end" ? x : anchor === "middle" ? x + w / 2 : x + w;
    const left = anchor === "end" ? x - w : anchor === "middle" ? x - w / 2 : x;
    return right > vbW + 1 || left < -1 || y > vbH + 1 || y < -1;
  });
  if (over.length) {
    console.log("  OUT OF BOUNDS:");
    over.forEach(t => console.log(`    "${t._text}" @ x=${t.attrs.x} y=${t.attrs.y} anchor=${t.attrs["text-anchor"] || "start"}`));
  }

  // collisions among left-anchored labels sharing an x band
  const right = texts.filter(t => Number(t.attrs.x) > vbW * 0.6 && (t.attrs["text-anchor"] || "start") === "start")
    .map(t => ({ t, y: Number(t.attrs.y) })).sort((a, b) => a.y - b.y);
  for (let i = 1; i < right.length; i++) {
    const d = right[i].y - right[i - 1].y;
    if (d < 11) console.log(`  TIGHT (${d.toFixed(1)}px): "${right[i-1].t._text}" / "${right[i].t._text}"`);
  }
  if (!over.length) console.log("  in bounds");
}

if (process.env.DUMP) {
  const els = bySvg[process.env.DUMP] || [];
  els.filter(e => e.tag === "text" && e._text)
     .sort((a,b) => Number(a.attrs.y) - Number(b.attrs.y))
     .forEach(t => console.log(`  y=${String(t.attrs.y).padEnd(20)} x=${String(t.attrs.x).padEnd(8)} "${t._text}"`));
}
