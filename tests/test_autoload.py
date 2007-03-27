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

# First create the tables (it would be better to use an external db)
engine = sqlalchemy.create_engine('sqlite:///')
meta = BoundMetaData(engine)

person_table = Table('person', meta,
    Column('id', Integer, primary_key=True),
    Column('father_id', Integer, ForeignKey('person.id')),
    Column('name', Unicode(32)))
person_table.create()

animal_table = Table('animal', meta,
    Column('id', Integer, primary_key=True),
    Column('name', String(30)),
    Column('color', String(15)),
    Column('owner_id', Integer, ForeignKey('person.id')),
    Column('feeder_id', Integer, ForeignKey('person.id')))
animal_table.create()

category_table = Table('category', meta,
    Column('name', String, primary_key=True))
category_table.create()

person_category_table = Table('person_category', meta,
    Column('person_id', Integer, ForeignKey('person.id')),
    Column('category_name', String, ForeignKey('category.name')))
person_category_table.create()

person_person_table = Table('person_person', meta,
    Column('person_id1', Integer, ForeignKey('person.id')),
    Column('person_id2', Integer, ForeignKey('person.id')))
person_person_table.create()

elixir.delay_setup = True
elixir.options_defaults.update(dict(autoload=True, shortnames=True))

class Person(Entity):
    belongs_to('father', of_kind='Person')
    has_many('children', of_kind='Person')
    has_many('pets', of_kind='Animal', inverse='owner')
    has_many('animals', of_kind='Animal', inverse='feeder')
    has_and_belongs_to_many('categories', of_kind='Category', 
                            tablename='person_category')
    has_and_belongs_to_many('appreciate', of_kind='Person',
                            tablename='person_person',
                            local_side='person_id1')
    has_and_belongs_to_many('isappreciatedby', of_kind='Person',
                            tablename='person_person',
                            local_side='person_id2')

    def __str__(self):
        s = '%s\n' % self.name.encode('utf-8')  
        for pet in self.pets:
            s += '  * pet: %s\n' % pet.name
        return s


class Animal(Entity):
    belongs_to('owner', of_kind='Person', colname='owner_id')
    belongs_to('feeder', of_kind='Person', colname='feeder_id')


class Category(Entity):
    has_and_belongs_to_many('persons', of_kind='Person', 
                            tablename='person_category')

elixir.delay_setup = False
elixir.options_defaults.update(dict(autoload=False, shortnames=False))

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

    def test_autoload_has_and_belongs_to_many(self):
        stupid = Category(name="Stupid")
        simpson = Category(name="Simpson")
        old = Category(name="Old")

        grampa = Person(name="Abe", categories=[simpson, old])
        homer = Person(name="Homer", categories=[simpson, stupid])
        bart = Person(name="Bart")
        lisa = Person(name="Lisa")
        
        simpson.persons.extend([bart, lisa])
        
        objectstore.flush()
        objectstore.clear()
        
        c = Category.get_by(name="Simpson")
        grampa = Person.get_by(name="Abe")
        
        print "Persons in the '%s' category: %s." % (
                c.name, 
                ", ".join(p.name for p in c.persons))
        
        assert len(c.persons) == 4
        assert c in grampa.categories

    def test_autoload_has_and_belongs_to_many_selfref(self):
        barney = Person(name="Barney")
        homer = Person(name="Homer", appreciate=[barney])

        objectstore.flush()
        objectstore.clear()
        
        homer = Person.get_by(name="Homer")
        barney = Person.get_by(name="Barney")

        assert barney in homer.appreciate
        assert homer in barney.isappreciatedby

if __name__ == '__main__':
    test = TestAutoload()
    test.setup()
    test.test_autoload_has_and_belongs_to_many_selfref()
#    test.test_autoload()
    test.teardown()
