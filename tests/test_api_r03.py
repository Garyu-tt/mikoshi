import http.client
import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from server.api import Handler
from server.runtime import Runtime


class ApiR03Tests(unittest.TestCase):
    def test_client_modules_and_unified_graph(self):
        with tempfile.TemporaryDirectory() as tmp:
            Handler.runtime=Runtime(tmp);Handler.token='r03-test-token'
            server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
            t=threading.Thread(target=server.serve_forever,daemon=True);t.start()
            try:
                def req(path, authorized=True):
                    conn=http.client.HTTPConnection('127.0.0.1',server.server_port)
                    h={'Authorization':'Bearer r03-test-token'} if authorized else {}
                    conn.request('GET',path,headers=h)
                    response=conn.getresponse();body=response.read()
                    code=response.status;conn.close();return code,body
                for resource in ('/app.js','/client/board.js','/client/editor.js','/style.css'):
                    self.assertEqual(req(resource)[0],200)
                self.assertEqual(req('/api/v1/unified-graph',False)[0],401)
                code,body=req('/api/v1/unified-graph')
                self.assertEqual(code,200)
                graph=json.loads(body)
                self.assertGreater(graph['source_files'],50)
                self.assertGreater(graph['heritage_nodes'],100)
                self.assertTrue(all(n['id'] for n in graph['nodes']))
            finally:
                server.shutdown();server.server_close();t.join()
