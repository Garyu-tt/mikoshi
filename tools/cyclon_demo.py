"""Run: PYTHONPATH=. python tools/cyclon_demo.py"""
from server.cyclon_loop import TwinLoop

loop = TwinLoop(depth=3)
print('CYCLON toy parameters:', loop.model.parameter_count)
print('Before training:', loop.train_text('A', 'ababab' * 100, lr=0))
for _ in range(6):
    loss = loop.train_text('A', 'ababab' * 100, lr=.025)
print('After training:', round(loss, 4))
loop.submit('A', 'Review the PR')
loop.submit('B', 'Write tests')
loop.run(12)
print('Twins (byte IDs only; NOT a language model):', loop.diagnostics())
