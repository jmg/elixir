"""
    simple test case
"""

from elixir import *

def setup():
    metadata.bind = 'sqlite:///'

class TestOneWay(object):
    def teardown(self):
        cleanup_all(True)
    
    def test_belongs_to(self):
        class Person(Entity):
            has_field('name', Unicode(30))

        class Animal(Entity):
            has_field('name', Unicode(30))
            belongs_to('owner', of_kind='Person')

        setup_all(True)
        
        santa = Person(name="Santa Claus")
        rudolph = Animal(name="Rudolph", owner=santa)
        
        objectstore.flush()
        objectstore.clear()
        
        assert "Claus" in Animal.get_by(name="Rudolph").owner.name

    def test_belongs_to_wh_key(self):
        class T1(Entity):
            has_field('test', Integer, primary_key=True, key='testx')

        class T2(Entity):
            belongs_to('t1', of_kind='T1')
            
        setup_all(True)
        
        t1 = T1(testx=1)
        
        objectstore.flush()

