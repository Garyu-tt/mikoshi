"""Expose actual recursive catalog operations through the existing secure API."""


def install(runtime):
    registry = runtime.components
    runtime.add('components.graph','Рекурсивный граф компонентов','ide.graph',[],
                lambda a:registry.graph(runtime.capabilities))
    runtime.add('components.reload','Переиндексировать манифесты','ide.graph',[],
                lambda a:registry.reload())
    runtime.add('components.resolve','Найти capability по контракту','ide.graph',[
                {'name':'name','type':'text'},
                {'name':'minimum','type':'text','optional':True}],
                lambda a:{'provider':registry.provider(runtime.capabilities,a)})
    runtime.add('components.switch','Включить или отключить модуль','ide.graph',[
                {'name':'unit','type':'text'}, {'name':'enabled','type':'text'}],
                lambda a:registry.switch(a.get('unit'), _switch(a.get('enabled'))))


def _switch(value):
    if value not in ('true', 'false'):
        raise ValueError('Use true or false')
    return value == 'true'
