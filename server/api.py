"""Small HTTP API and graph-driven modular IDE client. Auth always required."""
import hmac
import json
import os
import secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
from server.runtime import Runtime
from server import codemap, graph_union, module_graph, buildinfo

ROOT = Path(__file__).resolve().parent.parent
MAX_BODY = 8 * 1024 * 1024


class Handler(BaseHTTPRequestHandler):
    runtime = None
    token = None

    def _auth(self):
        given = self.headers.get("Authorization", "")
        return hmac.compare_digest(given, "Bearer " + self.token)

    def _json(self, status, obj):
        content = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _static(self, name, mime):
        from server.http_static import send_static
        return send_static(self, ROOT, name, mime)

    def do_GET(self):
        path = urlsplit(self.path).path
        if path in ("/", "/index.html"):
            return self._static("index.html", "text/html; charset=utf-8")
        if path == "/app.js":
            return self._static("app.js", "text/javascript; charset=utf-8")
        if path in ("/client/board.js", "/client/editor.js", "/client/app.js",
                    "/client/visual2d.js", "/client/visual2d_canvas.js",
                    "/client/visual2d_input.js"):
            return self._static(path.rsplit("/", 1)[-1], "text/javascript; charset=utf-8")
        if path == "/style.css":
            return self._static("style.css", "text/css; charset=utf-8")
        if path == "/api/v1/health":
            return self._json(200, {"module": "mikoshi.ide", "version": buildinfo.version(), "ready": True})
        if not self._auth():
            return self._json(401, {"error": "Bearer token required"})
        self.runtime.update_views()
        if path == "/api/v1/graph":
            return self._json(200, self.runtime.layout.graph(self.runtime.visible_capabilities()))
        if path == "/api/v1/capabilities":
            return self._json(200, {"capabilities": self.runtime.visible_capabilities()})
        if path == "/api/v1/code-map":
            return self._json(200, codemap.graph())
        if path == "/api/v1/component-graph":
            return self._json(200, self.runtime.components.graph(self.runtime.visible_capabilities()))
        if path == "/api/v1/module-map":
            return self._json(200, module_graph.build())
        if path == "/api/v1/unified-graph":
            return self._json(200, graph_union.build(self.runtime))
        return self._json(404, {"error": "No such endpoint"})

    def do_POST(self):
        if not self._auth():
            return self._json(401, {"error": "Bearer token required"})
        if urlsplit(self.path).path != "/api/v1/action":
            return self._json(404, {"error": "No such endpoint"})
        try:
            size = int(self.headers.get("Content-Length", "-1"))
            if not 0 <= size <= MAX_BODY:
                return self._json(413, {"error": "Invalid request size"})
            request = json.loads(self.rfile.read(size))
            if not isinstance(request, dict):
                raise ValueError("Expected JSON object")
            result = self.runtime.execute(request.get("action"), request.get("args", {}))
            return self._json(200, {"ok": True, "result": result})
        except (ValueError, TypeError, KeyError, json.JSONDecodeError) as e:
            return self._json(400, {"ok": False, "error": str(e)[:250]})
        except Exception:
            return self._json(500, {"ok": False, "error": "Internal action error"})


def main():
    token = os.environ.get("MIKOSHI_API_TOKEN") or secrets.token_urlsafe(28)
    host = os.getenv("MIKOSHI_HOST", "127.0.0.1")
    if host not in ("127.0.0.1", "localhost", "::1") and not os.getenv("MIKOSHI_API_TOKEN"):
        raise RuntimeError("Explicit token required for remote binding")
    Handler.token = token
    Handler.runtime = Runtime(os.getenv("MIKOSHI_STATE_DIR", str(Path.home() / ".local/share/mikoshi-ide")))
    addr = (host, int(os.getenv("MIKOSHI_PORT", "8768")))
    print(f"Mikoshi IDE API on http://{addr[0]}:{addr[1]}/", flush=True)
    if not os.getenv("MIKOSHI_API_TOKEN"):
        print("Ephemeral local API token:", token, flush=True)
    ThreadingHTTPServer(addr, Handler).serve_forever()


if __name__ == "__main__":
    main()
