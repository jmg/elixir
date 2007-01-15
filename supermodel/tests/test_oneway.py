"""
    simple test case
"""

import nose
from sqlalchemy import create_engine
from supermodel import *
from supermodel import metadata, objectstore


class Person(Entity):
    with_fields(
        name = Field(Unicode(30))
    )
    
    using_options(shortnames=True, order_by="name")


class Animal(Entity):
    with_fields(
        name = Field(Unicode(30)),
        nose_color = Field(Unicode(15))
    )
    
    belongs_to('owner', of_kind='Person')
    
    using_options(shortnames=True, order_by="name")


class TestOneWay(object):
    def setup(self):
        engine = create_engine('sqlite:///')
        metadata.connect(engine)
        create_all()
    
    def teardown(self):
        drop_all()
    
    def test_oneway(self):
        santa = Person(name="Santa Claus")
        rudolph = Animal(name="Rudolph", nose_color="red")
        rudolph.owner = santa
        
        objectstore.flush()
        objectstore.clear()
        
        assert "Claus" in Animal.get_by(name="Rudolph").owner.name
