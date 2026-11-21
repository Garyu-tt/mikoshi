import unittest
import numpy as np
from server.cyclon_core import TwinCell
from server.cyclon_loop import TwinLoop


class CyclonTests(unittest.TestCase):
    def test_shared_weights_separate_states(self):
        m = TwinCell(width=16, rank=2, seed=1)
        self.assertIsNot(m.agents['A'].hidden, m.agents['B'].hidden)
        self.assertIsNot(m.agents['A'].a, m.agents['B'].a)
        self.assertEqual(m.agents['B'].steps, 0)
        m.step('A', 42)
        self.assertEqual(m.agents['B'].steps, 0)
        self.assertEqual(m.agents['A'].steps, 1)

    def test_synchronous_peer_exchange(self):
        model = TwinCell(width=16, rank=2, seed=3)
        loop = TwinLoop(model, depth=2)
        loop.submit('A', 'abc')
        loop.submit('B', 'def')
        self.assertEqual(len(loop.run(2)), 2)
        self.assertEqual(model.agents['A'].steps, 4)
        self.assertEqual(model.agents['B'].steps, 4)
        self.assertEqual(loop.diagnostics()['agents']['A']['queued_bytes'], 0)

    def test_feedback_on_input_and_learning(self):
        m = TwinCell(width=32, rank=2, seed=5)
        first = m.step('A', 97)
        self.assertTrue(0 <= first['token'] < 256)
        self.assertEqual(m.step('A')['step'], 2)
        loop = TwinLoop(m)
        before = loop.train_text('A', 'ab' * 250, lr=0)
        for _ in range(8):
            loop.train_text('A', 'ab' * 250, lr=.03)
        after = loop.train_text('A', 'ab' * 250, lr=0)
        self.assertLess(after, before)

    def test_guardrails(self):
        loop = TwinLoop()
        with self.assertRaises(ValueError):loop.run(100000)
        with self.assertRaises(ValueError):loop.submit('A', 'a' * 4097)
        with self.assertRaises(ValueError):loop.model.step('A', 500)
        with self.assertRaises(ValueError):loop.model.step('B', 0, np.ones(13))


if __name__ == '__main__':unittest.main()
