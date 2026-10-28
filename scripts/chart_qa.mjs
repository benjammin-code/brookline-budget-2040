/* Chart QA: opens a built HTML page in headless Chrome, lets charts.js draw,
   and measures every chart label where the browser actually put it, so
   labels that run off a chart or overlap each other are caught.

     node scripts/chart_qa.mjs docs/article.html
     node scripts/chart_qa.mjs docs/reference_document.html
     node scripts/chart_qa.mjs docs/site/build/topic-homes-changing-hands.html
     DUMP=ownerflow-svg node scripts/chart_qa.mjs docs/site/build/topic-homes-changing-hands.html

   Run it after every charts.js change. The builds report chart counts and pass
   happily while labels run off the canvas; this is the check that doesn't.
   Exits 1 if any label is out of bounds.

   Why a real browser: the first version ran charts.js against a DOM stub and
   estimated label widths at 0.605em a character, the old monospace font. The
   site's chart font is now Public Sans, which measures 0.4 to 0.73em a
   character depending on the text, so no single factor works. It also had to
   imitate every DOM method charts.js uses, and broke when one was added.

   Validate any change to this file with a positive control: CONTROL=1 adds a
   label off the right edge of the first chart and the report must flag it. */
import fs from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";

const HTML = process.argv[2];
if (!HTML) { console.error("usage: node scripts/chart_qa.mjs <built page.html>"); process.exit(2); }
const CHROME = process.env.CHROME || [
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  "/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser"
].find(p => fs.existsSync(p));
if (!CHROME) { console.error("Chrome not found; set CHROME to its path"); process.exit(2); }

// Runs in the page after the charts draw: every label's box in its chart's viewBox units.
const probe = `<script>
window.addEventListener("load", function () { setTimeout(function () {
  ${process.env.CONTROL ? `var c = document.querySelector("svg.chart"); if (c) { var x = document.createElementNS("http://www.w3.org/2000/svg", "text");
    x.setAttribute("x", c.viewBox.baseVal.width - 20); x.setAttribute("y", 40); x.textContent = "CONTROL LABEL OFF THE EDGE"; c.appendChild(x); }` : ""}
  var out = [];
  document.querySelectorAll("svg.chart").forEach(function (svg) {
    var vb = svg.viewBox.baseVal, s = svg.getBoundingClientRect(), k = vb && s.width ? vb.width / s.width : 0, labels = [];
    if (!k) { out.push({ id: svg.id, hidden: true }); return; }
    svg.querySelectorAll("text").forEach(function (t) {
      if (!t.textContent.trim()) return;
      var r = t.getBoundingClientRect();   // follows rotate() and the real font
      labels.push({ t: t.textContent, l: (r.left - s.left) * k, r: (r.right - s.left) * k, y0: (r.top - s.top) * k, y1: (r.bottom - s.top) * k });
    });
    out.push({ id: svg.id, w: vb.width, h: vb.height, labels: labels });
  });
  var pre = document.createElement("pre"); pre.id = "CHART-QA"; pre.textContent = JSON.stringify(out); document.body.appendChild(pre);
}, 1000); });
</script>`;

// The copy sits beside the page so its relative links still resolve.
const tmp = path.join(path.dirname(HTML), `.chart-qa-${process.pid}.html`);
fs.writeFileSync(tmp, fs.readFileSync(HTML, "utf8") + probe);
let dom;
try {
  dom = execFileSync(CHROME, ["--headless=new", "--disable-gpu", "--no-first-run", "--mute-audio", "--window-size=1280,900",
    "--virtual-time-budget=8000", "--dump-dom", "file://" + path.resolve(tmp)],
    { encoding: "utf8", maxBuffer: 256 * 1024 * 1024, stdio: ["ignore", "pipe", "ignore"], timeout: 120000 });
} finally { fs.rmSync(tmp, { force: true }); }
const m = dom.match(/<pre id="CHART-QA">([\s\S]*?)<\/pre>/);
if (!m) { console.error("no measurements came back (Chrome timed out, or the page threw before load?)"); process.exit(2); }
const unesc = s => s.replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&amp;/g, "&");
const charts = JSON.parse(unesc(m[1]));

let bad = 0;
if (!charts.length) console.log("no charts on this page");
for (const c of charts) {
  if (c.hidden) { console.log(`\n=== ${c.id}  (not displayed, skipped) ===`); continue; }
  console.log(`\n=== ${c.id}  (viewBox ${c.w}x${c.h}, ${c.labels.length} labels) ===`);
  const over = c.labels.filter(b => b.l < -1 || b.r > c.w + 1 || b.y0 < -1 || b.y1 > c.h + 1);
  if (over.length) {
    bad += over.length;
    console.log("  OUT OF BOUNDS:");
    over.forEach(b => console.log(`    "${b.t}"  x ${b.l.toFixed(0)} to ${b.r.toFixed(0)}, y ${b.y0.toFixed(0)} to ${b.y1.toFixed(0)}`));
  }
  // two labels whose boxes overlap; a halo drawn under its own label (same text, same place) isn't a collision
  const hits = [];
  for (let i = 0; i < c.labels.length; i++) for (let j = i + 1; j < c.labels.length; j++) {
    const a = c.labels[i], b = c.labels[j];
    if (a.t === b.t && Math.abs(a.l - b.l) < 1 && Math.abs(a.y0 - b.y0) < 1) continue;
    const ox = Math.min(a.r, b.r) - Math.max(a.l, b.l), oy = Math.min(a.y1, b.y1) - Math.max(a.y0, b.y0);
    if (ox > 1 && oy > 2) hits.push(`"${a.t}" / "${b.t}"`);
  }
  if (hits.length) { console.log("  OVERLAPPING:"); hits.forEach(h => console.log("    " + h)); }
  if (!over.length && !hits.length) console.log("  in bounds, no overlaps");
  if (process.env.DUMP === c.id)
    [...c.labels].sort((a, b) => a.y0 - b.y0)
      .forEach(b => console.log(`  y ${b.y0.toFixed(0).padStart(4)}-${b.y1.toFixed(0).padEnd(4)} x ${b.l.toFixed(0).padStart(4)}-${b.r.toFixed(0).padEnd(4)} "${b.t}"`));
}
process.exit(bad ? 1 : 0);
