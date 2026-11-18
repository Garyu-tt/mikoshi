"""Authenticated HTTP is the only public-facing path to the CPU test circuit."""
import http.client
import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from server.api import Handler
from connectome_fixture_r06 import ConnectomeFixture


class ConnectomeHttpTests(ConnectomeFixture):
    def test_live_http_neural_steps_are_discovered_and_authenticated(self):
        self.write()
        Handler.runtime=self.runtime();Handler.token='r06-test-token'
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        worker=threading.Thread(target=server.serve_forever,daemon=True)
        worker.start()
        self.addCleanup(lambda: (server.shutdown(),server.server_close(),worker.join()))

        def request(path, body=None, auth=True):
            conn=http.client.HTTPConnection('127.0.0.1',server.server_port)
            h={'Authorization':'Bearer r06-test-token'} if auth else {}
            if body is not None:h['Content-Type']='application/json'
            conn.request('POST' if body is not None else 'GET',path,
                         body=json.dumps(body) if body is not None else None,headers=h)
            response=conn.getresponse();status=response.status
            data=json.loads(response.read());conn.close()
            return status,data

        self.assertEqual(request('/api/v1/capabilities',auth=False)[0],401)
        _,meta=request('/api/v1/module-map')
        self.assertIn('mikoshi.connectome.lif',{n['id'] for n in meta['nodes']})
        status,actions=request('/api/v1/capabilities')
        self.assertEqual(status,200)
        ids={a['id'] for a in actions['capabilities']}
        self.assertIn('connectome.step.labtest',ids)
        self.assertIn('visual2d.open.connectome.labtest',ids)
        query={'action':'connectome.step.labtest','args':{
            'sample_at_ns':'1000','clock_domain':'monotonic-ns',
            'pulses':{'n0':1.25}}}
        self.assertEqual(request('/api/v1/action',query,False)[0],401)
        status,answer=request('/api/v1/action',query)
        self.assertEqual(status,200)
        self.assertEqual(answer['result']['spike_ids'],['n0'])
        _,view=request('/api/v1/action',{
            'action':'visual2d.open.connectome.labtest','args':{}})
        self.assertEqual(view['result']['nodes'][0]['activity'],1.)
