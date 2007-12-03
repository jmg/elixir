"""
    simple test case
"""

from sqlalchemy import Table, Column, MetaData
from elixir import *

def setup():
    metadata.bind = 'sqlite:///'

def teardown():
    cleanup_all()

#-----------

class TestAutoload(object):
    def test_pk(self):
        local_meta = MetaData(metadata.bind)

        person_table = Table('person', local_meta,
            Column('id', Integer),
            Column('name', String(32)))
        
        local_meta.create_all()

        class Person(Entity):
            using_options(tablename='person', autoload=True)
            using_mapper_options(primary_key=['id'])

        setup_all()

        barney = Person(id=1, name="Barney")

        session.flush()
        session.clear()

        persons = Person.query.all()

        assert len(persons) == 1
        assert persons[0].name == "Barney"

