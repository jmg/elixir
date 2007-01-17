"""
    simple test case
"""

from sqlalchemy import create_engine
from supermodel import *
from supermodel import metadata, objectstore


class Person(Entity):
    with_fields(
        name = Field(Unicode(30))
    )
    
    belongs_to('father', of_kind='Person', as='children')
    has_many('children', of_kind='Person', as='father')
    
    using_options(tablename='people', order_by='name')


class TestSelfRef(object):
    def setup(self):
        engine = create_engine('sqlite:///')
        metadata.connect(engine)
        create_all()
    
    def teardown(self):
        drop_all()
    
    def test_selfref(self):
        grampa = Person(name="Abe")
        homer = Person(name="Homer")
        bart = Person(name="Bart")
        lisa = Person(name="Lisa")
        
        grampa.children.append(homer)        
        homer.children.append(bart)
        lisa.father = homer
        
        objectstore.flush()
        objectstore.clear()
        
        p = Person.get_by(name="Homer")
        
        print "%s is %s's child." % (p.name, p.father.name)        
        print "His children are: %s." % (
                " and ".join(c.name for c in p.children))
        
        assert p in p.father.children
        assert p.father is Person.get_by(name="Abe")
        assert p is Person.get_by(name="Lisa").father
