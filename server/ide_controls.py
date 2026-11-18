"""Every graph-edit command is an ordinary discoverable capability."""


def install(runtime):
    layout = runtime.layout
    runtime.add('layout.create_tab', 'Создать вкладку', 'ide.graph', [
        {'name': 'title', 'label': 'Название', 'type': 'text'},
        {'name': 'parent', 'label': 'Родительская вкладка', 'type': 'text', 'optional': True}],
        lambda a: layout.tab(a.get('title'), a.get('parent') or None))
    runtime.add('layout.tab_edit', 'Изменить вкладку', 'ide.graph', [
        {'name': 'tab', 'type': 'text'}, {'name': 'title', 'type': 'text', 'optional': True},
        {'name': 'parent', 'type': 'text', 'optional': True},
        {'name': 'order', 'type': 'number', 'optional': True}],
        lambda a: layout.update_tab(a.get('tab'), a.get('title'),
            a['parent'] if 'parent' in a else '__keep__', a.get('order')))
    runtime.add('layout.tab_delete', 'Удалить пустую вкладку', 'ide.graph', [
        {'name': 'tab', 'type': 'text'}], lambda a: layout.delete_tab(a.get('tab')))
    runtime.add('layout.place', 'Добавить кнопку в область', 'ide.graph', [
        {'name': 'action', 'type': 'text'}, {'name': 'tab', 'type': 'text'},
        {'name': 'area', 'type': 'text', 'optional': True},
        {'name': 'order', 'type': 'number', 'optional': True},
        {'name': 'column', 'type': 'number', 'optional': True},
        {'name': 'row', 'type': 'number', 'optional': True}],
        lambda a: layout.place(a.get('action'), a.get('tab'), {c["id"]: True for c in runtime.visible_capabilities()},
            a.get('order', 0), a.get('area', 'workspace'),
            a.get('column', 0), a.get('row', 0)))
    runtime.add('layout.move', 'Переместить кнопку', 'ide.graph', [
        {'name': 'placement', 'type': 'text'}, {'name': 'tab', 'type': 'text'},
        {'name': 'area', 'type': 'text'}, {'name': 'order', 'type': 'number', 'optional': True},
        {'name': 'column', 'type': 'number', 'optional': True},
        {'name': 'row', 'type': 'number', 'optional': True}],
        lambda a: layout.move(a.get('placement'), a.get('tab'), a.get('area'),
            a.get('order', 0), a.get('column', 0), a.get('row', 0)))
    runtime.add('layout.remove', 'Убрать размещённую кнопку', 'ide.graph', [
        {'name': 'placement', 'type': 'text'}],
        lambda a: layout.remove(a.get('placement')))
