"""
test autoloaded entities
"""

from sqlalchemy import Table, Column, ForeignKey, MetaData
from elixir import *
from elixir import options
import elixir

def setup_entity_raise(cls):
    try:
        setup_entities([cls])
    except Exception, e:
        pass
    else:
        assert False, "Exception did not occur setting up %s" % cls.__name__

# ------

def setup():
    # First create the tables
    meta = MetaData('sqlite:///')

    person_table = Table('person', meta,
        Column('id', Integer, primary_key=True),
        Column('father_id', Integer, ForeignKey('person.id')),
        Column('name', String(32)))

    animal_table = Table('animal', meta,
        Column('id', Integer, primary_key=True),
        Column('name', String(30)),
        Column('owner_id', Integer, ForeignKey('person.id')),
        Column('feeder_id', Integer, ForeignKey('person.id')))

    category_table = Table('category', meta,
        Column('name', String(30), primary_key=True))

    person_category_table = Table('person_category', meta,
        Column('person_id', Integer, ForeignKey('person.id')),
        Column('category_name', String(30), ForeignKey('category.name')))

    person_person_table = Table('person_person', meta,
        Column('person_id1', Integer, ForeignKey('person.id')),
        Column('person_id2', Integer, ForeignKey('person.id')))

    meta.create_all()

    elixir.options_defaults.update(dict(autoload=True, shortnames=True))

    global Person, Animal, Category

    #TODO: split these into individual classes for each test.
    class Person(Entity):
        father = ManyToOne('Person')
        children = OneToMany('Person')
        pets = OneToMany('Animal', inverse='owner')
        animals = OneToMany('Animal', inverse='feeder')
        categories = ManyToMany('Category',
                                tablename='person_category')
        appreciate = ManyToMany('Person',
                                tablename='person_person',
                                local_side='person_id1')
        isappreciatedby = ManyToMany('Person',
                                tablename='person_person',
                                local_side='person_id2')

    class Animal(Entity):
        owner = ManyToOne('Person', colname='owner_id')
        feeder = ManyToOne('Person', colname='feeder_id')


    class Category(Entity):
        persons = ManyToMany('Person',
                                tablename='person_category')

    metadata.bind = meta.bind
    setup_all()


def teardown():
    cleanup_all()
    elixir.options_defaults.update(dict(autoload=False, shortnames=False))

# -----------

class TestAutoload(object):
    def setup(self):
        create_all()

    def teardown(self):
        drop_all()
        session.clear()

    def test_simple(self):
        snowball = Animal(name="Snowball II")
        slh = Animal(name="Santa's Little Helper")
        homer = Person(name="Homer", animals=[snowball, slh], pets=[slh])
        lisa = Person(name="Lisa", pets=[snowball])

        session.commit()
        session.clear()

        homer = Person.get_by(name="Homer")
        lisa = Person.get_by(name="Lisa")
        slh = Animal.get_by(name="Santa's Little Helper")

        assert len(homer.animals) == 2
        assert homer == lisa.pets[0].feeder
        assert homer == slh.owner

    def test_selfref(self):
        grampa = Person(name="Abe")
        homer = Person(name="Homer")
        bart = Person(name="Bart")
        lisa = Person(name="Lisa")

        grampa.children.append(homer)
        homer.children.append(bart)
        lisa.father = homer

        session.commit()
        session.clear()

        p = Person.get_by(name="Homer")

        assert p in p.father.children
        assert p.father.name == "Abe"
        assert p.father is Person.get_by(name="Abe")
        assert p is Person.get_by(name="Lisa").father

    def test_m2m(self):
        stupid = Category(name="Stupid")
        simpson = Category(name="Simpson")
        old = Category(name="Old")

        grampa = Person(name="Abe", categories=[simpson, old])
        homer = Person(name="Homer", categories=[simpson, stupid])
        bart = Person(name="Bart")
        lisa = Person(name="Lisa")

        simpson.persons.extend([bart, lisa])

        session.commit()
        session.clear()

        c = Category.get_by(name="Simpson")
        grampa = Person.get_by(name="Abe")

        print "Persons in the '%s' category: %s." % (
                c.name,
                ", ".join([p.name for p in c.persons]))

        assert len(c.persons) == 4
        assert c in grampa.categories

    def test_m2m_selfref(self):
        barney = Person(name="Barney")
        homer = Person(name="Homer", appreciate=[barney])

        session.commit()
        session.clear()

        homer = Person.get_by(name="Homer")
        barney = Person.get_by(name="Barney")

        assert barney in homer.appreciate
        assert homer in barney.isappreciatedby

    # overrides tests

    def test_override_pk_fails(self):
        class Person(Entity):
            id = Field(Integer, primary_key=True)

        setup_entity_raise(Person)

    def test_override_non_pk_fails(self):
        class Animal(Entity):
            name = Field(String(30))

        setup_entity_raise(Animal)

    def test_override_pk(self):
        class Person(Entity):
            using_options(allowcoloverride=True)

            id = Field(Integer, primary_key=True)

        setup_entities([Person])

    def test_override_non_pk(self):
        class Animal(Entity):
            using_options(allowcoloverride=True)

            name = Field(String(30))

        setup_entities([Animal])
        assert isinstance(Animal.table.columns['name'].type, String)

    # ----------------

    def test_nopk(self):
        metadata.bind = 'sqlite:///'

        local_meta = MetaData(metadata.bind)

        table = Table('a', local_meta,
            Column('id', Integer),
            Column('name', String(32)))

        local_meta.create_all()

        class A(Entity):
            using_options(tablename='a', autoload=True)
            using_mapper_options(primary_key=['id'])

        setup_all()

        a1 = A(id=1, name="a1")

        session.commit()
        session.clear()

        res = A.query.all()

        assert len(res) == 1
        assert res[0].name == "a1"

    def test_inheritance(self):
        metadata.bind = 'sqlite:///'

        local_meta = MetaData(metadata.bind)

        table = Table('father', local_meta,
            Column('id', Integer, primary_key=True),
            Column('row_type', options.POLYMORPHIC_COL_TYPE))

        local_meta.create_all()

        options_defaults["autoload"] = True

        class Father(Entity):
            using_options(tablename='father')

        class Son(Father):
            pass

        setup_all()
