"""Local preview of website/dist with the same clean URLs Vercel serves.
Run:  python3 website/scripts/serve.py [port]   then open http://localhost:8000/"""
import http.server, os, sys
from pathlib import Path
DIST = Path(__file__).resolve().parent.parent / "dist"

class H(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k): super().__init__(*a, directory=str(DIST), **k)
    def translate_path(self, path):
        p = path.split("?")[0].split("#")[0].rstrip("/") or "/index"
        f = DIST / p.lstrip("/")
        # like Vercel's cleanUrls: /forecast serves forecast.html even though forecast/ exists
        if not f.is_file() and (DIST / (p.lstrip("/") + ".html")).exists(): return str(DIST / (p.lstrip("/") + ".html"))
        if f.is_dir() and (f / "index.html").exists(): return str(f / "index.html")
        return super().translate_path(path)
    def guess_type(self, path):
        t = super().guess_type(path)
        return t + "; charset=utf-8" if t.startswith("text/") else t

http.server.ThreadingHTTPServer(("127.0.0.1", int(sys.argv[1]) if len(sys.argv) > 1 else 8000), H).serve_forever()
