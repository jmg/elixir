from elixir import *

def setup():
    global Thing

    class Thing(Entity):
        name = Field(String(40))
        type = Field(String(40))

        class Stuff(Entity):
            ping = Field(String(32))
            pong = Field(String(32))

        other = Field(String(40))

    setup_all()

class TestNestedClass(object):
    def test_nestedclass(self):

        print "GLOBALS", globals().keys()
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
