"""
    simple test case
"""

from elixir import *

def setup():
    global Person 

    class Person(Entity):
        has_field('firstname', Unicode(30))
        has_field('surname', Unicode(30))

        def __str__(self):
            return "<Person: %s %s>" % (self.firstname, self.surname)

    metadata.bind = 'sqlite:///'


def teardown():
    cleanup_all()


class TestHasField(object):
    def setup(self):
        create_all()
    
    def teardown(self):
        drop_all()
        objectstore.clear()
    
    def test_hasfield(self):
        homer = Person(firstname="Homer", surname="Simpson")
        bart = Person(firstname="Bart", surname="Simpson")
        
        objectstore.flush()
        objectstore.clear()
        
        p = Person.get_by(firstname="Homer")
        
        print p

        assert p.surname == 'Simpson'
        

if __name__ == '__main__':
    setup()
    test = TestHasField()
    test.setup()
    test.test_hasfield()
    test.teardown()
    teardown()
