"""Pre-deploy checks on the built site (website/dist): accessibility and phone width.

    python3 scripts/check_site_quality.py            # every page
    python3 scripts/check_site_quality.py forecast/money.html maps/index.html

Run by rebuild_all.py as its last step, and must pass before
`vercel deploy website/dist --scope ben-s-hobbies --yes`.

How it works. A small local server serves website/dist plus one extra page, a harness, at
/__qa/harness.html. Headless Chrome opens the harness, which loads each site page in turn into a
390px-wide iframe (a phone; headless Chrome cannot make its own window that narrow), waits for the
charts to draw, and inspects the rendered page, so labels that charts.js sets while drawing count.
The harness writes its findings into the page as JSON, and `--dump-dom` hands them back.

Failures (exit 1):
  - a chart (<svg class="chart"> or role="img") with no text alternative after rendering
  - an <img> with no alt attribute (alt="" is allowed: it marks a decorative image)
  - a form control (input, select, textarea) with no label
  - a link or button with no text and no aria-label
  - a chart block with neither a data table nor a "Show data table" button
  - phone width: the page scrolls sideways at 390px, or an element reaches past the right edge,
    other than inside a container that scrolls or clips on purpose (prose tables, chart wraps)
Warnings (printed, exit 0): a heading level skipped (an h2 followed by an h4, say).
"""
import http.server
import json
import re
import socketserver
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "website" / "dist"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PHONE = 390        # iframe width, px
SLACK = 2          # an element may reach this far past the edge (sub-pixel rounding, borders)
SETTLE_MS = 1500   # after load, time for charts to draw (virtual time, so cheap)
LOAD_CAP_MS = 8000 # move on if a page never fires load (an external map tile, say)
SKIP = {"404.html"}

HARNESS = r"""<!doctype html><meta charset="utf-8"><title>qa</title>
<body><pre id="out"></pre><script>
var PAGES = __PAGES__, W = __W__, SLACK = __SLACK__, SETTLE = __SETTLE__, CAP = __CAP__;
var results = [];
function textOf(el) { return (el.textContent || "").replace(/\s+/g, " ").trim(); }
function named(el, doc) {
  if ((el.getAttribute("aria-label") || "").trim()) return true;
  var lb = el.getAttribute("aria-labelledby");
  if (lb && lb.split(/\s+/).some(function (id) { var t = doc.getElementById(id); return t && textOf(t); })) return true;
  return false;
}
function hidden(el, win) {
  for (var e = el; e && e.nodeType === 1; e = e.parentElement) {
    if (e.getAttribute("aria-hidden") === "true") return true;
    var cs = win.getComputedStyle(e);
    if (cs.display === "none" || cs.visibility === "hidden") return true;
  }
  return false;
}
function where(el) {
  var s = el.tagName.toLowerCase();
  if (el.id) s += "#" + el.id;
  var c = (el.getAttribute("class") || "").trim().split(/\s+/).filter(Boolean).slice(0, 2);
  if (c.length) s += "." + c.join(".");
  var t = textOf(el).slice(0, 50);
  return s + (t ? ' "' + t + '"' : "");
}
function inspect(path, win) {
  var doc = win.document, fail = [], warn = [];
  // charts and other images drawn as SVG
  doc.querySelectorAll("svg.chart, [role=img]").forEach(function (el) {
    if (hidden(el, win)) return;
    if (!named(el, doc) && !el.querySelector("title")) fail.push("chart with no text alternative: " + where(el));
  });
  doc.querySelectorAll("img").forEach(function (el) {
    if (!el.hasAttribute("alt")) fail.push("image with no alt: " + (el.getAttribute("src") || "").slice(0, 80));
  });
  // form controls
  doc.querySelectorAll("input, select, textarea").forEach(function (el) {
    var type = (el.getAttribute("type") || "").toLowerCase();
    if (type === "hidden" || type === "submit" || type === "button" || hidden(el, win)) return;
    var ok = named(el, doc) || el.closest("label") ||
      (el.id && doc.querySelector('label[for="' + CSS.escape(el.id) + '"]')) || (el.getAttribute("title") || "").trim();
    if (!ok) fail.push("form control with no label: " + where(el));
  });
  // links and buttons need a name
  doc.querySelectorAll("a[href], button").forEach(function (el) {
    if (hidden(el, win)) return;
    var imgAlt = Array.prototype.some.call(el.querySelectorAll("img[alt]"), function (i) { return i.getAttribute("alt").trim(); });
    if (!textOf(el) && !named(el, doc) && !imgAlt && !(el.getAttribute("title") || "").trim())
      fail.push((el.tagName === "A" ? "link" : "button") + " with no text: " + where(el) + " " + (el.getAttribute("href") || ""));
  });
  // every chart block offers its numbers as a table
  doc.querySelectorAll(".chart-block").forEach(function (el) {
    var shown = Array.prototype.some.call(el.querySelectorAll("svg.chart"), function (s) { return !hidden(s, win); });
    if (shown && !el.querySelector("table, .data-table-wrap, .toggle-table-btn"))
      fail.push("chart block with no data table: " + where(el.querySelector("h3") || el));
  });
  // heading levels (warning only)
  var last = 0;
  doc.querySelectorAll("h1, h2, h3, h4, h5, h6").forEach(function (h) {
    if (hidden(h, win)) return;
    var n = +h.tagName[1];
    if (last && n > last + 1) warn.push("heading skips from h" + last + " to h" + n + ": " + where(h));
    last = n;
  });
  // phone width
  var sw = doc.documentElement.scrollWidth;
  if (sw > W + SLACK) fail.push("page scrolls sideways at " + W + "px: content is " + sw + "px wide");
  var over = [];
  doc.body.querySelectorAll("*").forEach(function (el) {
    var r = el.getBoundingClientRect();
    if (!r.width || r.right <= W + SLACK) return;
    if (win.getComputedStyle(el).position === "fixed") return;
    // inside a container that scrolls or clips on purpose: fine
    for (var a = el.parentElement; a && a !== doc.body; a = a.parentElement) {
      var ox = win.getComputedStyle(a).overflowX;
      if (ox === "auto" || ox === "scroll" || ox === "hidden" || ox === "clip") return;
    }
    // report only the outermost offender
    var p = el.parentElement;
    if (p && p !== doc.body && p.getBoundingClientRect().right > W + SLACK) return;
    over.push(where(el) + " reaches " + Math.round(r.right) + "px");
  });
  over.slice(0, 8).forEach(function (o) { fail.push("wider than a phone: " + o); });
  if (over.length > 8) fail.push("wider than a phone: " + (over.length - 8) + " more elements");
  return { page: path, fail: fail, warn: warn };
}
function next(i) {
  if (i >= PAGES.length) { document.getElementById("out").textContent = JSON.stringify(results); return; }
  var f = document.createElement("iframe"), done = false;
  f.style.width = W + "px"; f.style.height = "900px"; f.style.border = "0";
  function finish(loaded) {
    if (done) return; done = true;
    setTimeout(function () {
      try { results.push(inspect(PAGES[i], f.contentWindow)); }
      catch (e) { results.push({ page: PAGES[i], fail: ["could not inspect: " + e], warn: [] }); }
      if (!loaded) results[results.length - 1].warn.push("page did not finish loading within " + CAP + " ms");
      f.remove(); next(i + 1);
    }, SETTLE);
  }
  f.onload = function () { finish(true); };
  setTimeout(function () { finish(false); }, CAP);
  f.src = "/" + PAGES[i];
  document.body.appendChild(f);
}
next(0);
</script>"""


class Handler(http.server.SimpleHTTPRequestHandler):
    harness = b""

    def __init__(self, *a, **k):
        super().__init__(*a, directory=str(DIST), **k)

    def do_GET(self):
        if self.path.startswith("/__qa/harness.html"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(self.harness)))
            self.end_headers()
            self.wfile.write(self.harness)
            return
        # clean URLs, as on Vercel: /forecast/money -> forecast/money.html
        p = self.path.split("?")[0].split("#")[0]
        if p != "/" and not Path(p).suffix and (DIST / (p.lstrip("/") + ".html")).exists():
            self.path = p + ".html"
        super().do_GET()

    def log_message(self, *a):
        pass


def run_batch(port, pages):
    Handler.harness = (HARNESS.replace("__PAGES__", json.dumps(pages)).replace("__W__", str(PHONE))
                       .replace("__SLACK__", str(SLACK)).replace("__SETTLE__", str(SETTLE_MS))
                       .replace("__CAP__", str(LOAD_CAP_MS))).encode()
    budget = len(pages) * (SETTLE_MS + LOAD_CAP_MS) + 5000
    r = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-first-run", "--mute-audio",
                        "--hide-scrollbars", f"--virtual-time-budget={budget}", "--dump-dom",
                        f"http://127.0.0.1:{port}/__qa/harness.html"],
                       capture_output=True, text=True, timeout=300)
    m = re.search(r'<pre id="out">(.*?)</pre>', r.stdout, re.S)
    if not m or not m.group(1).strip():
        return [{"page": p, "fail": ["harness returned nothing (Chrome timed out?)"], "warn": []} for p in pages]
    import html
    return json.loads(html.unescape(m.group(1)))


def main():
    t0 = time.time()
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    pages = args or sorted(str(p.relative_to(DIST)) for p in DIST.rglob("*.html")
                           if p.name not in SKIP and "__qa" not in p.parts)
    socketserver.TCPServer.allow_reuse_address = True
    srv = socketserver.ThreadingTCPServer(("127.0.0.1", 0), Handler)
    port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        results = []
        for i in range(0, len(pages), 10):   # batches keep one slow page from stalling the rest
            results += run_batch(port, pages[i:i + 10])
    finally:
        srv.shutdown()
    fails = [(r["page"], f) for r in results for f in r["fail"]]
    warns = [(r["page"], w) for r in results for w in r["warn"]]
    for p, w in warns:
        print(f"  warn  {p}: {w}")
    for p, f in fails:
        print(f"  FAIL  {p}: {f}")
    print(f"{len(results)} pages checked in {time.time() - t0:.0f}s: "
          f"{len(fails)} failures, {len(warns)} warnings")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
