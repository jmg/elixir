"""
test having entities using a custom base class
"""

from elixir import *

def setup():
    metadata.bind = 'sqlite://'

    global MyBase

    class MyBase(object):
        __metaclass__ = EntityMeta

        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

class TestCustomBase(object):
    def teardown(self):
        cleanup_all(True)

    def test_simple(self):
        class A(MyBase):
            name = Field(String(30))

        setup_all(True)

        a1 = A(name="a1")

        session.commit()
        session.clear()

        a = A.query.filter_by(name="a1").one()

        assert a.name == 'a1'

    def test_inherit(self):
        class A(MyBase):
            name = Field(String(30))

        class B(A):
            data = Field(String(30))

        setup_all(True)

        a1 = A(name="a1")
        b1 = B(name="b1", data="-b1-")

        session.commit()
        session.clear()

        b = A.query.filter_by(name="b1").one()

        assert b.data == '-b1-'

    def test_non_object_base(self):
        class BaseParent(object):
            def test(self):
                return "success"

        class InheritedBase(BaseParent):
            __metaclass__ = EntityMeta

        class A(InheritedBase):
            name = Field(String(30))

        setup_all(True)

        a1 = A()
        a1.name = "a1"

        session.commit()
        session.clear()

        a = A.query.filter_by(name="a1").one()

        assert a.name == 'a1'
        assert a.test() == "success"

    def test_base_with_fields(self):
        class FieldBase(object):
            __metaclass__ = EntityMeta

            common = Field(String(32))

        class A(FieldBase):
            name = Field(String(32))

        class B(FieldBase):
            pass

        setup_all(True)

        assert 'name' in A.table.columns
        assert 'common' in A.table.columns
        assert 'common' in B.table.columns

    def test_base_with_fields_in_parent(self):
        class BaseParent(object):
            common1 = Field(String(32))

        class FieldBase(BaseParent):
            __metaclass__ = EntityMeta

            common2 = Field(String(32))

        class A(FieldBase):
            name = Field(String(32))

        class B(FieldBase):
            pass

        setup_all(True)

        assert 'name' in A.table.columns
        assert 'common1' in A.table.columns
        assert 'common1' in B.table.columns
        assert 'common2' in A.table.columns
        assert 'common2' in B.table.columns

    def test_base_with_options(self):
        import re

        def camel_to_underscore(entity):
            return re.sub(r'(.+?)([A-Z])+?', r'\1_\2', entity.__name__).lower()

        class OptionBase(object):
            __metaclass__ = EntityMeta

            using_options_defaults(tablename=camel_to_underscore)

        class TestA(OptionBase):
            name = Field(String(32))

        class SuperTestB(OptionBase):
            pass

        setup_all(True)

        assert TestA.table.name == 'test_a'
        assert SuperTestB.table.name == 'super_test_b'

