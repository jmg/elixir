"""
    simple test case
"""

from elixir import *

#-----------

class TestMultipleRelationships(object):
    def setup(self):
        metadata.bind = 'sqlite:///'
    
    def teardown(self):
        cleanup_all(True)
    
    def test_belongs_to_multi_ref(self):
        class A(Entity):
            has_field('name', String(32))
            
            has_many('brel1', of_kind='B', inverse='arel1')
            has_many('brel2', of_kind='B', inverse='arel2')
            
        class B(Entity):
            has_field('name', String(15))
            
            belongs_to('arel1', of_kind='A')
            belongs_to('arel2', of_kind='A')

        setup_all(True)

        b1 = B(name="b1")
        b2 = B(name="b2")
        a1 = A(name="a1", brel1=[b1, b2], brel2=[b2])
        a2 = A(name="a2", brel2=[b1])
        
        objectstore.flush()
        objectstore.clear()
        
        a1 = A.get_by(name="a1")
        a2 = A.get_by(name="a2")
        b1 = B.get_by(name="b1")
        
        assert len(a1.brel1) == 2
        assert a1 == a2.brel2[0].arel1
        assert a2 == b1.arel2

    def test_has_and_belongs_to_many_multi_ref(self):
        class A(Entity):
            has_field('name', String(100))

            has_and_belongs_to_many('rel1', of_kind='B')
            has_and_belongs_to_many('rel2', of_kind='B')
            
        class B(Entity):
            has_field('name', String(20), primary_key=True)

        setup_all(True)
        
        b1 = B(name='b1')
        a1 = A(name='a1', rel1=[B(name='b2'), b1],
                          rel2=[B(name='b3'), B(name='b4'), b1])

        objectstore.flush()
        objectstore.clear()
        
        a1 = A.query.one()
        b1 = B.get_by(name='b1')
        b2 = B.get_by(name='b2')

        assert b1 in a1.rel1 
        assert b1 in a1.rel2
        assert b2 in a1.rel1

