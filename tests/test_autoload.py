"""
    simple test case
"""

import sqlalchemy
from sqlalchemy import Table, Column, ForeignKey, BoundMetaData
from sqlalchemy.types import *
from elixir import *
from elixir import metadata, objectstore
import elixir
import datetime

# First create two tables (it would be better to user an external db)
engine = sqlalchemy.create_engine('sqlite:///')
meta = BoundMetaData(engine)

person_table = Table('person', meta,
    Column('id', Integer, primary_key=True),
    Column('father_id', Integer, ForeignKey('person.id')),
    Column('name', Unicode(32)))
person_table.create()

animal_table = Table('animal', meta,
    Column('id', Integer, primary_key=True),
    Column('name', String(15)),
    Column('color', String(15)),
    Column('owner_id', Integer, ForeignKey('person.id')),
    Column('feeder_id', Integer, ForeignKey('person.id')))
animal_table.create()

elixir.delay_setup = True

class Person(Entity):
#    has_field('name', Unicode(32))
    
    belongs_to('father', of_kind='Person', colname='father_id')
    has_many('children', of_kind='Person')
    has_many('pets', of_kind='Animal', inverse='owner')
    has_many('animals', of_kind='Animal', inverse='feeder')
    
    using_options(autoload=True, shortnames=True)

    def __str__(self):
        s = '%s\n' % self.name.encode('utf-8')  
        for pet in self.pets:
            s += '  * pet: %s\n' % pet.name
        return s

class Animal(Entity):
#    has_field('name', String(15))
#    has_field('color', String(15))
    
    belongs_to('owner', of_kind='Person', colname='owner_id')
    belongs_to('feeder', of_kind='Person', colname='feeder_id')

    using_options(autoload=True, shortnames=True)

elixir.delay_setup = False

#-----------

class TestAutoload(object):
    def setup(self):
        metadata.connect(engine)
        setup_all()
    
    def teardown(self):
        drop_all()
    
    def test_autoload(self):
        snowball = Animal(name="Snowball II", color="grey")
        slh = Animal(name="Santa's Little Helper")
        homer = Person(name="Homer", animals=[snowball, slh], pets=[slh])
        lisa = Person(name="Lisa", pets=[snowball])
        
        objectstore.flush()
        objectstore.clear()
        
        homer = Person.get_by(name="Homer")
        lisa = Person.get_by(name="Lisa")
        
        print homer

        assert len(homer.animals) == 2
        assert homer == lisa.pets[0].feeder
        assert homer == slh.owner

    def test_autoload_selfref(self):
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

if __name__ == '__main__':
    test = TestAutoload()
    test.setup()
    test.test_autoload()
    test.teardown()
