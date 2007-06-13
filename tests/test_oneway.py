"""
    simple test case
"""

from sqlalchemy import create_engine
from elixir import *

def setup():
    global Person, Animal

    class Person(Entity):
        with_fields(
            name = Field(Unicode(30))
        )

    class Animal(Entity):
        with_fields(
            name = Field(Unicode(30)),
            nose_color = Field(Unicode(15))
        )
        
        belongs_to('owner', of_kind='Person')

    engine = create_engine('sqlite:///')
    metadata.connect(engine)

def teardown():
    cleanup_all()

class TestOneWay(object):
    def setup(self):
        create_all()
    
    def teardown(self):
        drop_all()
        objectstore.clear()
    
    def test_oneway(self):
        santa = Person(name="Santa Claus")
        rudolph = Animal(name="Rudolph", nose_color="red")
        rudolph.owner = santa
        
        objectstore.flush()
        objectstore.clear()
        
        assert "Claus" in Animal.get_by(name="Rudolph").owner.name
