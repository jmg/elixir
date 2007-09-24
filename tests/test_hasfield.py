"""
    simple test case
"""

from elixir import *

def setup():
    metadata.bind = 'sqlite:///'

class TestHasField(object):
    def teardown(self):
        cleanup_all()
    
    def test_hasfield(self):
        class Person(Entity):
            has_field('firstname', Unicode(30))
            has_field('surname', Unicode(30))

        setup_all(True)
        
        homer = Person(firstname="Homer", surname="Simpson")
        bart = Person(firstname="Bart", surname="Simpson")
        
        objectstore.flush()
        objectstore.clear()
        
        p = Person.get_by(firstname="Homer")
        
        assert p.surname == 'Simpson'

