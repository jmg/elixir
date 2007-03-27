"""
    simple test case
"""

import sqlalchemy

from sqlalchemy.types   import *
from elixir             import *

#import elixir
#elixir.delay_setup = True

class Person(Entity):
    has_field('firstname', Unicode(30))
    has_field('surname', Unicode(30))
    belongs_to('sister', of_kind='Person')

    @property
    def name(self):
        return "%s %s" % (self.firstname, self.surname)

    def __str__(self):
        sister = self.sister and self.sister.name or "unknown"
        return "%s [%s]" % (self.name, sister)
    
class PersonExtended(Person):
    has_field('age', Integer)
    belongs_to('parent', of_kind='PersonExtended')

    using_options(inheritance='single')

    def __str__(self):
        parent = self.parent and self.parent.name or "unknown"
        return "%s (%s) {%s}" % (super(PersonExtended, self).__str__(), 
                                 self.age, parent)

#elixir.delay_setup = False

class TestInheritance(object):
    def setup(self):
        engine = sqlalchemy.create_engine('sqlite:///')
        metadata.connect(engine)
        setup_all()
    
    def teardown(self):
        cleanup_all()

    def test_singletable_inheritance(self):
        homer = PersonExtended(firstname="Homer", surname="Simpson", age=36)
        # lisa needs to be a Person object, not a PersonExtended object because
        # the sister relationship points to a Person, not a PersonExtendend, so
        # bart's sister must be a Person. This is to comply with SQLAlchemy's
        # policy to prevent loading relationships with unintended types, unless 
        # explicitly enabled (enable_typechecks=False).
        lisa = Person(firstname="Lisa", surname="Simpson")
        bart = PersonExtended(firstname="Bart", surname="Simpson", 
                              parent=homer, sister=lisa)

        objectstore.flush()
        objectstore.clear()

        p = PersonExtended.get_by(firstname="Bart")

        assert p.sister.name == 'Lisa Simpson'
        assert p.parent.age == 36

        for p in Person.select():
            print p

        for p in PersonExtended.select():
            print p

if __name__ == '__main__':
    test = TestInheritance()
    test.setup()
    test.test_singletable_inheritance()
    test.teardown()
