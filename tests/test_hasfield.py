"""
    simple test case
"""

import sqlalchemy

from sqlalchemy.types   import *
from elixir             import *


class Person(Entity):
    has_field('firstname', Unicode(30))
    has_field('surname', Unicode(30))

    def __str__(self):
        return "%s %s" % (self.firstname, self.surname)
    

class TestHasField(object):
    def setup(self):
        engine = sqlalchemy.create_engine('sqlite:///')
        metadata.connect(engine)
        create_all()
    
    def teardown(self):
        cleanup_all()
    
    def test_hasfield(self):
        homer = Person(firstname="Homer", surname="Simpson")
        bart = Person(firstname="Bart", surname="Simpson")
        
        objectstore.flush()
        objectstore.clear()
        
        p = Person.get_by(firstname="Homer")
        
        print p

        assert p.surname == 'Simpson'
        

if __name__ == '__main__':
    test = TestHasField()
    test.setup()
    test.test_hasfield()
    test.teardown()
