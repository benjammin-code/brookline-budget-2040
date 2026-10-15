"""Pictures of four site charts for the forecast page's five takeaways (Ben, 2026-10-12), captured
from the built pages in light and dark so the page can follow the reader's theme:
img/takeaway-<name>-light.png and -dark.png. The fourth takeaway uses the levers chart, which the
page draws in HTML. Run after the site is built (rebuild_all.py does); writes to website/src/img
and website/dist/img.

Each chart is photographed in a narrow frame so its text stays legible at the size the page shows
it. The chart's own title stays; its subtitle and "Show data table" button are hidden, since the
forecast page gives its own caption and links to the live chart."""
import http.server
import json
import re
import shutil
import socketserver
import subprocess
import threading
from functools import partial
from pathlib import Path

from PIL import Image

WEB = Path(__file__).resolve().parents[1]
DIST, SRC_IMG = WEB / "dist", WEB / "src" / "img"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
W, SCALE = 660, 2
CHARTS = [("causes", "forecast/spending.html", "causes-wrap"),
          ("outlook", "forecast/base-case.html", "outlook-wrap"),
          ("services", "forecast/topics/growth-links.html", "gl-services-wrap"),
          ("permits", "forecast/topics/growth-links.html", "gl-revenue-wrap"),
          ("births", "forecast/watch.html", "births-watch-wrap")]
HARNESS = """<!doctype html><html><head><style>body{margin:0}iframe{width:%dpx;height:6000px;border:0;display:block}</style></head>
<body><iframe id="f" src="/%s"></iframe><pre id="out" style="position:absolute;top:6100px">pending</pre><script>
document.getElementById('f').onload=function(){setTimeout(function(){
var d=document.getElementById('f').contentDocument, c=d.getElementById('%s').closest('.chart-block');
c.querySelectorAll('.sub,.toggle-table-btn,.data-table-wrap').forEach(function(e){e.style.display='none'});
var top=c.getBoundingClientRect().top+d.defaultView.scrollY;
d.body.style.marginTop=(-top+20)+'px'; void c.offsetHeight;
// re-measure and correct: margin collapsing or late layout can leave the first shift off (2026-10-15)
for(var i=0;i<4;i++){var off=c.getBoundingClientRect().top-20; if(Math.abs(off)<0.5)break;
d.body.style.marginTop=(parseFloat(d.body.style.marginTop)-off)+'px'; void c.offsetHeight;}
var r=c.getBoundingClientRect(), f=document.getElementById('f').getBoundingClientRect();
document.getElementById('out').textContent=JSON.stringify([r.left+f.left,r.top+f.top,r.width,r.height]);
},2500)};</script></body></html>"""


def chrome(*args):
    return subprocess.run([CHROME, "--headless=new", "--disable-gpu", f"--window-size={W},1400",
                           "--virtual-time-budget=8000", *args], capture_output=True, text=True, timeout=120)


def main():
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    handler = partial(Quiet, directory=str(DIST))
    (DIST / "img").mkdir(exist_ok=True)
    with socketserver.TCPServer(("127.0.0.1", 0), handler) as httpd:
        port = httpd.server_address[1]
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        try:
            for name, page, wrap in CHARTS:
                harness = DIST / f"_takeaway_{name}.html"
                harness.write_text(HARNESS % (W, page, wrap))
                url = f"http://127.0.0.1:{port}/{harness.name}"
                try:
                    dom = chrome("--dump-dom", url).stdout
                    x, y, w, h = json.loads(re.search(r'<pre id="out"[^>]*>(\[[^<]*\])', dom).group(1))
                    if not (0 <= y and y + h <= 1400 and h > 100):
                        raise SystemExit(f"{name}: chart not in frame ({x}, {y}, {w}, {h})")
                    for scheme, theme in ((1, "light"), (0, "dark")):
                        shot = SRC_IMG / f"_shot_{name}_{theme}.png"
                        chrome(f"--force-device-scale-factor={SCALE}",
                               f"--blink-settings=preferredColorScheme={scheme}", f"--screenshot={shot}", url)
                        out = SRC_IMG / f"takeaway-{name}-{theme}.png"
                        Image.open(shot).crop(tuple(round(v * SCALE) for v in (x, y, x + w, y + h))).save(out, optimize=True)
                        shot.unlink()
                        shutil.copy(out, DIST / "img" / out.name)
                    print(f"  {name}: {round(w * SCALE)}x{round(h * SCALE)}")
                finally:
                    harness.unlink(missing_ok=True)
        finally:
            httpd.shutdown()
    print(f"wrote {len(CHARTS)} takeaway pictures, light and dark")


if __name__ == "__main__":
    main()
