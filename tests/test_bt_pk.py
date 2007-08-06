"""
    simple test case
"""

from elixir import *

def setup():
    metadata.connect('sqlite:///')


def teardown():
    cleanup_all()


class TestBelongsToWithPrimaryKey(object):
    def teardown(self):
        cleanup_all(drop_tables=True)
    
    def test_one_pk(self):
        class A(Entity):
            has_field('name', Unicode(40), primary_key=True)
         
        class B(Entity):
            belongs_to('a', of_kind='A',
                       column_kwargs={'primary_key': True})
         
        class C(Entity):
            belongs_to('b', of_kind='B',
                       column_kwargs={'primary_key': True})

        setup_all()

        assert A.table.primary_key.columns.has_key('name')
        assert B.table.primary_key.columns.has_key('a_name')
        assert C.table.primary_key.columns.has_key('b_a_name')

    def test_bt_is_only_pk(self):
        class A(Entity):
            pass
         
        class B(Entity):
            belongs_to('a', of_kind='A',
                       column_kwargs={'primary_key': True})
         
        setup_all()

        assert A.table.primary_key.columns.has_key('id')
        assert B.table.primary_key.columns.has_key('a_id')
        assert not B.table.primary_key.columns.has_key('id')

    def test_multi_pk_in_target(self):
        class A(Entity):
            has_field('key1', Integer, primary_key=True)
            has_field('key2', Unicode(40), primary_key=True)
         
        class B(Entity):
            has_field('num', Integer, primary_key=True)
            belongs_to('a', of_kind='A',
                       column_kwargs={'primary_key': True})
         
        class C(Entity):
            has_field('num', Integer, primary_key=True)
            belongs_to('b', of_kind='B',
                       column_kwargs={'primary_key': True})

        setup_all()

        assert A.table.primary_key.columns.has_key('key1')
        assert A.table.primary_key.columns.has_key('key2')

        assert B.table.primary_key.columns.has_key('num')
        assert B.table.primary_key.columns.has_key('a_key1')
        assert B.table.primary_key.columns.has_key('a_key2')

        assert C.table.primary_key.columns.has_key('num')
        assert C.table.primary_key.columns.has_key('b_num')
        assert C.table.primary_key.columns.has_key('b_a_key1')
        assert C.table.primary_key.columns.has_key('b_a_key2')

    def test_cycle_but_use_alter(self):
        class A(Entity):
            belongs_to('c', of_kind='C', use_alter=True)
         
        class B(Entity):
            belongs_to('a', of_kind='A',
                       column_kwargs={'primary_key': True})
         
        class C(Entity):
            belongs_to('b', of_kind='B',
                       column_kwargs={'primary_key': True})

        setup_all()

        assert B.table.primary_key.columns.has_key('a_id')
        assert C.table.primary_key.columns.has_key('b_a_id')
        assert A.table.primary_key.columns.has_key('id')
        assert A.table.columns.has_key('c_b_a_id')

