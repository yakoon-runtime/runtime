#!/usr/bin/env python3
"""Start the web client (static file server).

Usage:
    python scripts/serve-webclient.py 8000

The browser connects directly to a local runtime via WebSocket.
Start the runtime first:
    python scripts/serve-runtime.py 9100
Then open http://localhost:8000 in a browser.
"""

import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

HOST = "127.0.0.1"
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000

WEB_DIR = Path(__file__).resolve().parent.parent / "apps" / "y5napp-web"


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)


if __name__ == "__main__":
    server = HTTPServer((HOST, PORT), Handler)
    print(f"Web client serving {WEB_DIR} on http://{HOST}:{PORT}")
    print(f"Connect to runtime at ws://localhost:9100 (default)")
    server.serve_forever()
