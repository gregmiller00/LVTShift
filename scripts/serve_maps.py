#!/usr/bin/env python3
"""Range-capable static file server for viewing LVTShift vector-tile parcel maps.

The large-city parcel maps (``analysis/reports/<city>/parcel_map.html``) render
PMTiles through MapLibre GL. The PMTiles protocol fetches slices of the
``<city>.pmtiles`` archive with HTTP **byte-range** requests — and Python's
built-in ``python -m http.server`` does NOT honor ``Range`` (it returns the whole
file with a 200), so PMTiles fails to load. This tiny server adds proper
``206 Partial Content`` range support.

Usage — from the repository root:

    python3 scripts/serve_maps.py            # serves the repo on http://localhost:8000
    # then open, e.g.:
    #   http://localhost:8000/analysis/reports/phoenix/parcel_map.html

    python3 scripts/serve_maps.py 8080       # custom port

Small self-contained inline maps (the non-tiled cities) work with any server or
a plain file:// double-click; you only need this for the large vector-tile ones.
"""
import http.server
import os
import re
import socketserver
import sys

_RANGE_RE = re.compile(r"^bytes=(\d+)-(\d*)$")


class RangeHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """SimpleHTTPRequestHandler with single-range (``bytes=start-end``) support."""

    def do_GET(self):  # noqa: N802 (stdlib naming)
        rng = self.headers.get("Range")
        path = self.translate_path(self.path)
        m = _RANGE_RE.match(rng.strip()) if rng else None
        if not m or not os.path.isfile(path):
            return super().do_GET()

        size = os.path.getsize(path)
        start = int(m.group(1))
        end = int(m.group(2)) if m.group(2) else size - 1
        end = min(end, size - 1)
        if start >= size or start > end:
            self.send_error(416, "Requested Range Not Satisfiable")
            return

        length = end - start + 1
        self.send_response(206)
        self.send_header("Content-Type", self.guess_type(path))
        self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(length))
        self.end_headers()
        with open(path, "rb") as f:
            f.seek(start)
            self.wfile.write(f.read(length))


def main() -> None:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000

    class _Server(socketserver.ThreadingTCPServer):
        allow_reuse_address = True
        daemon_threads = True

    with _Server(("127.0.0.1", port), RangeHTTPRequestHandler) as httpd:
        print(f"Serving {os.getcwd()} at http://localhost:{port}/  (Ctrl-C to stop)")
        print("Open a large-city map at, e.g.:")
        print(f"  http://localhost:{port}/analysis/reports/<city>/parcel_map.html")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nstopped")


if __name__ == "__main__":
    main()
