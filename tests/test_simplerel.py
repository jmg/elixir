from elixir import *

def setup():
    metadata.bind = "sqlite:///"

class TestAttrSyntax(object):
    def teardown(self):
        cleanup_all(True)

    def test_m2o_and_o2m(self):
        class A(Entity):
            name = Field(Unicode(60))
            bs = OneToMany('B')

        class B(Entity):
            name = Field(Unicode(60))
            a = ManyToOne('A')

        setup_all(True)

        b1 = B(name='b1', a=A(name='a1'))

        session.flush()
        session.clear()

        b = B.query.one()
        a = b.a

        assert b in a.bs

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

    def test_m2m(self):
        class A(Entity):
            name = Field(Unicode(60))
            bs_ = ManyToMany('B')

        class B(Entity):
            name = Field(Unicode(60))
            as_ = ManyToMany('A')

        setup_all(True)

        b1 = B(name='b1', as_=[A(name='a1')])

        session.flush()
        session.clear()

        a = A.query.one()
        b = B.query.one()

        assert a in b.as_
        assert b in a.bs_

