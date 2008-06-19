"""
Autosetup tests. Test that all setup triggers actually work.
"""

from sqlalchemy import Table
from sqlalchemy.orm import create_session
from elixir import *
import elixir

def setup():
    metadata.bind = 'sqlite:///'

def teardown():
    cleanup_all()

class TestSetup(object):
    def teardown(self):
        cleanup_all()

    def test_autosetup_manual_setup_all(self):
        class Person(Entity):
            name = Field(String(30))
            using_options(autosetup=True, tablename='person')

        # check that we have a fake table installed
        assert 'person' in metadata.tables
        assert isinstance(metadata.tables['person'],
                          elixir.entity.TriggerProxy)

        setup_all()

        assert isinstance(metadata.tables['person'], Table)

    # jeeez, this used to lock up hard the program
    def test_cleanup_before_setup(self):
        class Person(Entity):
            name = Field(String(30))
            using_options(autosetup=True, tablename='person')

        # check that we have a fake table installed
        assert 'person' in metadata.tables
        assert isinstance(metadata.tables['person'],
                          elixir.entity.TriggerProxy)

        cleanup_all()

        assert 'person' not in metadata.tables

    def test_drop_create_drop(self):
        class User(Entity):
            using_options(tablename='users')
            some_field = Field(Boolean, default=False)

        metadata.bind = 'sqlite:///'

        drop_all()
        create_all()

        class MockUser(User):
            pass

        drop_all()

    def test_no_autosetup(self):
        class Person(Entity):
            name = Field(String(30))
            using_options(autosetup=False, tablename='person')

        assert 'person' not in metadata.tables
        assert Person.table == None

        # check that accessing the table didn't trigger the setup
        assert 'person' not in metadata.tables

        setup_all()

        assert isinstance(metadata.tables['person'], Table)

    def test_call(self):
        class Person(Entity):
            name = Field(String(30))
            using_options(autosetup=True, tablename='person')

        assert 'person' in metadata.tables
        homer = Person(name="Homer Simpson")
        assert isinstance(metadata.tables['person'], Table)

    def test_getattr(self):
        class Person(Entity):
            name = Field(String(30))
            using_options(autosetup=True, tablename='person')

        tablename = Person.table.name
        assert tablename == 'person'
        assert isinstance(metadata.tables['person'], Table)

    def test_createall(self):
        class Person(Entity):
            name = Field(String(30))
            using_options(autosetup=True, tablename='person')

        create_all()
        assert isinstance(metadata.tables['person'], Table)

    def test_setupall(self):
        class Person(Entity):
            name = Field(String(30))
            using_options(autosetup=True, tablename='person')

        setup_all()
        assert isinstance(metadata.tables['person'], Table)

    def test_query(self):
        class Person(Entity):
            name = Field(String(30))
            using_options(autosetup=True, tablename='person')

        q = Person.query
        assert isinstance(metadata.tables['person'], Table)

    # This test doesn't work with Elixir 0.4.1 and further (because of changes
    # in SA 0.4.2).
#    def test_mapper(self):
        # we want to hit the mapper directly (without hitting any of the
        # other triggers first). We do so by getting a query object using a
        # manual session.
#        class Person(Entity):
#            name = Field(String(30))
#            using_options(autosetup=True, tablename='person')
#        sess = create_session()
#        persons = sess.query(Person).all()
#        assert isinstance(metadata.tables['person'], Table)



