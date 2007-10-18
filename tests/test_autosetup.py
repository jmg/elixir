"""
    simple test case
"""

from sqlalchemy import Table
from elixir import *


def setup():
    metadata.bind = 'sqlite:///'

def teardown():
    cleanup_all()

class TestSetup(object):
    def teardown(self):
        cleanup_all()
    
    def test_manual_setup_all(self):
        class Person(Entity):
            has_field('name', Unicode(30))
            using_options(autosetup=False, tablename='person')

        assert 'person' not in metadata.tables
        assert Person.table == None

        # check that accessing the table didn't trigger the setup
        assert 'person' not in metadata.tables
        
        setup_all(True)

        assert isinstance(metadata.tables['person'], Table)

    def test_call(self):
        class Person(Entity):
            has_field('name', Unicode(30))
            using_options(tablename='person')

        assert 'person' in metadata.tables
        homer = Person(name="Homer Simpson")
        assert isinstance(metadata.tables['person'], Table)
        
    def test_getattr(self):
        class Person(Entity):
            has_field('name', Unicode(30))
            using_options(tablename='person')

        tablename = Person.table.name
        assert tablename == 'person' 
        assert isinstance(metadata.tables['person'], Table)

    def test_createall(self):
        class Person(Entity):
            has_field('name', Unicode(30))
            using_options(tablename='person')

        create_all()
        assert isinstance(metadata.tables['person'], Table)

    def test_setupall(self):
        class Person(Entity):
            has_field('name', Unicode(30))
            using_options(tablename='person')

        setup_all()
        assert isinstance(metadata.tables['person'], Table)

    def test_query(self):
        class Person(Entity):
            has_field('name', Unicode(30))
            using_options(tablename='person')

        q = Person.query
        assert isinstance(metadata.tables['person'], Table)

