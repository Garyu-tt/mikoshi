import http.client
import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from server.api import Handler
from server.runtime import Runtime


class ApiTests(unittest.TestCase):
    def test_live_graph_and_auth(self):
        with tempfile.TemporaryDirectory() as temp:
            Handler.runtime = Runtime(temp)
            Handler.token = "test-token"
            server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
            t = threading.Thread(target=server.serve_forever, daemon=True)
            t.start()
            try:
                def req(method, path, payload=None, authorized=True):
                    c = http.client.HTTPConnection("127.0.0.1", server.server_port)
                    headers = {"Authorization": "Bearer test-token"} if authorized else {}
                    if payload is not None:
                        headers["Content-Type"] = "application/json"
                    c.request(method, path, json.dumps(payload) if payload else None, headers)
                    r = c.getresponse(); data = json.loads(r.read()); c.close()
                    return r.status, data
                self.assertEqual(req("GET", "/api/v1/graph", authorized=False)[0], 401)
                s, graph = req("GET", "/api/v1/graph")
                self.assertEqual(s, 200)
                self.assertTrue(any(n["id"] == "layout.create_tab" for n in graph["nodes"]))
                _, result = req("POST", "/api/v1/action", {"action": "layout.create_tab",
                                     "args": {"title": "Мой граф"}})
                self.assertEqual(result["result"]["title"], "Мой граф")
            finally:
                server.shutdown(); server.server_close(); t.join()
