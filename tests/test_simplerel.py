from elixir import *

def setup():
    metadata.bind = "sqlite:///"

class TestAttrSyntax(object):
    def teardown(self):
        cleanup_all(True)

    def test_o2o(self):
        class A(Entity):
            name = Field(Unicode(60))
            b = OneToOne('B')

        class B(Entity):
            name = Field(Unicode(60))
            a = ManyToOne('A')

        setup_all(True)

        b1 = B(name='b1', a=A(name='a1'))

        session.flush()
        session.clear()

        b = B.query.one()
        a = b.a

        assert b == a.b


