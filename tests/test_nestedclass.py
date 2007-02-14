from elixir import Entity, has_field, String

class Thing(Entity):
    has_field('name', String(40))
    has_field('type', String(40))
    
    class Stuff(Entity):
        has_field('ping', String(32))
        has_field('pong', String(32))
    
    has_field('other', String(40))


class TestNestedClass(object):
    def test_nestedclass(self):
        assert 'name' in Thing.table.columns.keys()
        assert 'type' in Thing.table.columns.keys()
        assert 'other' in Thing.table.columns.keys()
        assert 'ping' not in Thing.table.columns.keys()
        assert 'pong' not in Thing.table.columns.keys()

        assert 'name' not in Thing.Stuff.table.columns.keys()
        assert 'type' not in Thing.Stuff.table.columns.keys()
        assert 'other' not in Thing.Stuff.table.columns.keys()
        assert 'ping' in Thing.Stuff.table.columns.keys()
        assert 'pong' in Thing.Stuff.table.columns.keys()