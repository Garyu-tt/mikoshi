"""Guard against claiming R228 alone works with genuine R239."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from server import retina_loader, retina_state
from server.retina_sparse import SparseRetinaR239


class OriginalGateR08(unittest.TestCase):
    def test_historical_r238_is_mandatory_hash_pinned_dependency(self):
        self.assertIn('tile_sampler_r238.py', retina_loader.DEPENDS)
        source = retina_loader.PINS.read_text(encoding='utf-8')
        self.assertIn('168c85e01778ba3652488944fbd5be435f941db7d3708079dccfdf388732c3eb',source)

    def test_missing_cluster_sampler_fails_before_runtime_registration(self):
        class Retina:
            def __init__(self, width, height): pass
        class BadSampler:
            def __init__(self, width, height, passes): pass
        loaded = {'neural_retina_r188':SimpleNamespace(FastNeuralRetinaR188=Retina),
                  'tile_sampler_r238':SimpleNamespace(ClusteredRetinalSamplerR238=BadSampler)}
        with patch('server.retina_sparse.load', return_value=loaded):
            with self.assertRaisesRegex(ValueError, 'requires R238'):
                SparseRetinaR239('unused',width=16,height=16)

    def test_r07_checkpoint_is_not_silently_accepted_by_r08(self):
        eye, archive = None, None
        with self.assertRaisesRegex(ValueError, 'schema'):
            retina_state.restore(eye,{'schema':'mikoshi.retina-r239-state.v1'},archive)


if __name__ == '__main__':
    unittest.main()
