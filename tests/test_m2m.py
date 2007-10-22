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
    

    def test_has_and_belongs_to_many_multi_ref(self):
        class A(Entity):
            name = Field(String(100))

            rel1 = ManyToMany('B')
            rel2 = ManyToMany('B')
            
        class B(Entity):
            name = Field(String(20), primary_key=True)

        setup_all(True)
        
        b1 = B(name='b1')
        a1 = A(name='a1', rel1=[B(name='b2'), b1],
                          rel2=[B(name='b3'), B(name='b4'), b1])

        session.flush()
        session.clear()
        
        a1 = A.query.one()
        b1 = B.get_by(name='b1')
        b2 = B.get_by(name='b2')

        assert b1 in a1.rel1 
        assert b1 in a1.rel2
        assert b2 in a1.rel1

