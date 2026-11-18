"""Mikoshi IDE graph actions stay separate from neural runtime bootstrap."""
from server import codemap, heritage, graph_union


def install(runtime):
    runtime.add('code.map', 'Карта исходников', 'ide.graph', [],
                lambda a: codemap.graph())
    runtime.add('graph.inspect', 'Полный граф IDE', 'ide.graph', [],
                lambda a: graph_union.build(runtime))
    runtime.add('code.read', 'Открыть файл целиком', 'ide.graph',
                [{'name':'path','type':'text'}],lambda a:codemap.read(a.get('path')))
    runtime.add('research.search', 'Поиск по графу', 'mikoshi.research',
                [{'name':'query','type':'text'}],
                lambda a:heritage.lookup(a.get('query','')))
    runtime.add('research.inventory', 'Каталог исходников', 'mikoshi.research',[],
                lambda a:heritage.inventory())
