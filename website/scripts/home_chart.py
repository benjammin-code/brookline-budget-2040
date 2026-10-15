"""The home page's forecast picture: the Explorer's "Revenue and spending" chart in its base case,
captured in light and dark (img/home-forecast-light.png, img/home-forecast-dark.png) so the home
page can follow the reader's theme. Run after the site is built (rebuild_all.py does), since it
photographs website/dist/forecast/explorer.html; it writes to website/src/img and website/dist/img.

The Explorer's caption and its "Base case" legend entry are hidden for the picture: the home page
gives its own caption, and the base-case line only appears once a setting is changed."""
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
W, SCALE = 1100, 2
HARNESS = """<!doctype html><html><head><style>body{margin:0}iframe{width:%dpx;height:2000px;border:0;display:block}</style></head>
<body><iframe id="f" src="/forecast/explorer.html"></iframe><pre id="out" style="position:absolute;top:2100px">pending</pre><script>
document.getElementById('f').onload=function(){setTimeout(function(){
var d=document.getElementById('f').contentDocument, c=d.getElementById('lineChart').closest('section');
c.querySelectorAll('.cap').forEach(function(e){e.style.display='none'});
c.querySelectorAll('.legend span').forEach(function(e){if(/Base case/.test(e.textContent))e.style.display='none'});
void c.offsetHeight; var r=c.getBoundingClientRect(), f=document.getElementById("f").getBoundingClientRect();
document.getElementById('out').textContent=JSON.stringify([r.left+f.left,r.top+f.top,r.width,r.height]);
},2500)};</script></body></html>""" % W


def main():
    harness = DIST / "_home_chart_harness.html"
    harness.write_text(HARNESS)
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    handler = partial(Quiet, directory=str(DIST))
    with socketserver.TCPServer(("127.0.0.1", 0), handler) as httpd:
        port = httpd.server_address[1]
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        url = f"http://127.0.0.1:{port}/{harness.name}"
        try:
            dom = subprocess.run([CHROME, "--headless=new", "--disable-gpu", f"--window-size={W},2200",
                                  "--virtual-time-budget=8000", "--dump-dom", url],
                                 capture_output=True, text=True, timeout=120).stdout
            x, y, w, h = json.loads(re.search(r'<pre id="out"[^>]*>(\[[^<]*\])', dom).group(1))
            for scheme, name in ((1, "light"), (0, "dark")):
                shot = SRC_IMG / f"_shot_{name}.png"
                subprocess.run([CHROME, "--headless=new", "--disable-gpu", f"--force-device-scale-factor={SCALE}",
                                f"--blink-settings=preferredColorScheme={scheme}", f"--window-size={W},2200",
                                "--virtual-time-budget=8000", f"--screenshot={shot}", url],
                               capture_output=True, timeout=120)
                out = SRC_IMG / f"home-forecast-{name}.png"
                Image.open(shot).crop(tuple(round(v * SCALE) for v in (x, y, x + w, y + h))).save(out, optimize=True)
                shot.unlink()
                (DIST / "img").mkdir(exist_ok=True)
                shutil.copy(out, DIST / "img" / out.name)
            print(f"wrote img/home-forecast-light.png and -dark.png ({round(w * SCALE)}x{round(h * SCALE)})")
        finally:
            httpd.shutdown()
            harness.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
