#!/usr/bin/env python3
"""Start the web client (static file server).

Usage:
    python scripts/serve-webclient.py 8000

The browser connects directly to a local runtime via WebSocket.
Start the runtime first:
    python scripts/serve-runtime.py 9100
Then open http://localhost:8000 in a browser.
"""

import io
import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

from y5n.base.config import load_config
from themes import THEMES

HOST = "127.0.0.1"
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000

WEB_DIR = Path(__file__).resolve().parent.parent / "apps" / "y5napp-web"

def _inject_theme(html: str) -> str:
    cfg, _ = load_config()
    if not cfg.theme:
        return html

    colors = THEMES.get(cfg.theme)
    if not colors:
        return html

    css_vars = "\n".join(
        f"    --{k}: {v};" for k, v in colors.items()
    )
    style = f"""<style>
  :root {{
{css_vars}
  }}
</style>"""
    return html.replace("</head>", f"{style}\n</head>")


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def _serve_html(self, path: str) -> None:
        with open(path, "rb") as f:
            raw = f.read()
        html = _inject_theme(raw.decode("utf-8"))
        encoded = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self):
        path = self.translate_path(self.path)
        if os.path.isdir(path):
            path = os.path.join(path, "index.html")
        if os.path.isfile(path) and path.endswith(".html"):
            self._serve_html(path)
            return
        super().do_GET()


if __name__ == "__main__":
    server = HTTPServer((HOST, PORT), Handler)
    print(f"Web client serving {WEB_DIR} on http://{HOST}:{PORT}")
    print(f"Connect to runtime at ws://localhost:9100 (default)")
    server.serve_forever()
