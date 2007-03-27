"""
    test options
"""

from sqlalchemy import create_engine, create_session, UniqueConstraint 
from sqlalchemy.exceptions import SQLError, ConcurrentModificationError 
from elixir     import *


class TestOptions(object):
    def setup(self):
        engine = create_engine('sqlite:///')
        metadata.connect(engine)

    # this test is a rip-off SQLAlchemy's activemapper's update test
    def test_version_id_col(self):
        class Person(Entity):
            has_field('name', Unicode(30))

            using_options(version_id_col=True)

        Person.table.create()

        p1 = Person(name='Daniel')
        objectstore.flush()
        objectstore.clear()
        
        person = Person.select()[0]
        person.name = 'Gaetan'
        objectstore.flush()
        objectstore.clear()
        assert person.row_version == 2

        person = Person.select()[0]
        person.name = 'Jonathan'
        objectstore.flush()
        objectstore.clear()
        assert person.row_version == 3

        # check that a concurrent modification raises exception
        p1 = Person.select()[0]
        s1 = objectstore.session
        s2 = create_session()
        objectstore.context.current = s2
        p2 = Person.select()[0]
        p1.name = "Daniel"
        p2.name = "Gaetan"
        objectstore.flush()
        try:
            objectstore.context.current = s1
            objectstore.flush()
            assert False
        except ConcurrentModificationError:
            pass

    def test_tablename_func(self):
        import re

        def camel_to_underscore(entity):
            return re.sub(r'(.+?)([A-Z])+?', r'\1_\2', entity.__name__).lower()

        options_defaults['tablename'] = camel_to_underscore

        class MyEntity(Entity):
            has_field('name', Unicode(30))

        class MySuperTestEntity(Entity):
            has_field('name', Unicode(30))

        assert MyEntity.table.name == 'my_entity'
        assert MySuperTestEntity.table.name == 'my_super_test_entity'

        options_defaults['tablename'] = None

    def teardown(self):
        cleanup_all()


class TestTableOptions(object):
    def setup(self):
        global Person

        class Person(Entity):
            has_field('firstname', Unicode(30))
            has_field('surname', Unicode(30))

            using_table_options(UniqueConstraint('firstname', 'surname'))

        engine = create_engine('sqlite:///')
        metadata.connect(engine)
        create_all()

    def test_table_options(self):
        homer = Person(firstname="Homer", surname='Simpson')
        bart = Person(firstname="Bart", surname='Simpson')

        objectstore.flush()

        homer2 = Person(firstname="Homer", surname='Simpson')

        raised = False
        try:
            objectstore.flush()
        except SQLError:
            raised = True

        assert raised

        objectstore.clear()

    def teardown(self):
        cleanup_all()

