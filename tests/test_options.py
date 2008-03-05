"""
test options
"""

from sqlalchemy import UniqueConstraint, create_engine, Column
from sqlalchemy.orm import create_session
from sqlalchemy.exceptions import SQLError, ConcurrentModificationError 
from elixir import *

class TestOptions(object):
    def setup(self):
        metadata.bind = 'sqlite:///'

    def teardown(self):
        cleanup_all()

    # this test is a rip-off SQLAlchemy's activemapper's update test
    def test_version_id_col(self):
        class Person(Entity):
            name = Field(String(30))
 
            using_options(version_id_col=True)
 
        setup_all()
        Person.table.create()
 
        p1 = Person(name='Daniel')
        session.flush()
        session.clear()
        
        person = Person.query.first()
        person.name = 'Gaetan'
        session.flush()
        session.clear()
        assert person.row_version == 2
 
        person = Person.query.first()
        person.name = 'Jonathan'
        session.flush()
        session.clear()
        assert person.row_version == 3
 
        # check that a concurrent modification raises exception
        p1 = Person.query.first()
        s2 = create_session()
        p2 = s2.query(Person).first()
        p1.name = "Daniel"
        p2.name = "Gaetan"
        s2.flush()
        try:
            session.flush()
            assert False
        except ConcurrentModificationError:
            pass
        s2.close()

    def test_allowcoloverride_false(self):
        class MyEntity(Entity):
            name = Field(String(30))

        setup_all(True)

        raised = False
        try:
            MyEntity._descriptor.add_column(Column('name', String(30)))
        except Exception:
            raised = True

        assert raised

    def test_allowcoloverride_true(self):
        class MyEntity(Entity):
            name = Field(String(30))
            using_options(allowcoloverride=True)

        setup_all()

        # Note that this test is bogus as you cannot just change a column this
        # way since the mapper is already constructed at this point and will 
        # use the old column!!! This test is only meant as a way to check no
        # exception is raised.
        #TODO: provide a proper test (using autoloaded tables)
        MyEntity._descriptor.add_column(Column('name', String(30),
                                               default='test'))

    def test_tablename_func(self):
        import re

        def camel_to_underscore(entity):
            return re.sub(r'(.+?)([A-Z])+?', r'\1_\2', entity.__name__).lower()

        options_defaults['tablename'] = camel_to_underscore

        class MyEntity(Entity):
            name = Field(String(30))

        class MySuperTestEntity(Entity):
            name = Field(String(30))

        setup_all(True)

        assert MyEntity.table.name == 'my_entity'
        assert MySuperTestEntity.table.name == 'my_super_test_entity'

        options_defaults['tablename'] = None


class TestSessionOptions(object):
    def setup(self):
        metadata.bind = None

    def teardown(self):
        cleanup_all()

    def test_session_context(self):
        from sqlalchemy.ext.sessioncontext import SessionContext

        engine = create_engine('sqlite:///')
        
        ctx = SessionContext(lambda: create_session(bind=engine))
        
        class Person(Entity):
            using_options(session=ctx)
            firstname = Field(String(30))
            surname = Field(String(30))

        setup_all()
        create_all(engine)

        homer = Person(firstname="Homer", surname='Simpson')
        bart = Person(firstname="Bart", surname='Simpson')
        ctx.current.flush()
        
        assert Person.query.session is ctx.current
        assert Person.query.filter_by(firstname='Homer').one() is homer

    def test_manual_session(self):
        engine = create_engine('sqlite:///')
        
        class Person(Entity):
            using_options(session=None)
            firstname = Field(String(30))
            surname = Field(String(30))

        setup_all()
        create_all(engine)

        session = create_session(bind=engine)

        homer = Person(firstname="Homer", surname='Simpson')
        bart = Person(firstname="Bart", surname='Simpson')

        session.save(homer)
        session.save(bart)
        session.flush()
       
        bart.delete()
        session.flush()

        assert session.query(Person).filter_by(firstname='Homer').one() is homer
        assert session.query(Person).count() == 1

    def test_activemapper_session(self):
        try:
            from sqlalchemy.orm import scoped_session, sessionmaker
            #TODO: this test, as-is has no sense on SA 0.4 since activemapper 
            # session uses scoped_session, but we need to provide a new 
            # test for that.
            return
        except ImportError:
            pass

        try:
            from sqlalchemy.ext import activemapper
        except ImportError:
            return
            
        engine = create_engine('sqlite:///')

        store = activemapper.Objectstore(lambda: create_session(bind=engine))

        class Person(Entity):
            using_options(session=store)
            firstname = Field(String(30))
            surname = Field(String(30))

        setup_all()
        create_all(engine)

        homer = Person(firstname="Homer", surname='Simpson')
        bart = Person(firstname="Bart", surname='Simpson')

        store.flush()

        assert Person.query.session is store.context.current
        assert Person.query.filter_by(firstname='Homer').one() is homer

    def test_scoped_session(self):
        try:
            from sqlalchemy.orm import scoped_session, sessionmaker
        except ImportError:
            print "Not on version 0.4 of sqlalchemy"
            return
            
        engine = create_engine('sqlite:///')

        Session = scoped_session(sessionmaker(bind=engine))

        class Person(Entity):
            using_options(session=Session)
            firstname = Field(String(30))
            surname = Field(String(30))

        setup_all()
        create_all(engine)

        homer = Person(firstname="Homer", surname='Simpson')
        bart = Person(firstname="Bart", surname='Simpson')
        Session.flush()

        assert Person.query.session is Session()
        assert Person.query.filter_by(firstname='Homer').one() is homer
        
    def test_global_scoped_session(self):
        try:
            from sqlalchemy.orm import scoped_session, sessionmaker
        except ImportError:
            print "Not on version 0.4 of sqlalchemy"
            return

        global __session__
        
        engine = create_engine('sqlite:///')
        
        session = scoped_session(sessionmaker(bind=engine))
        __session__ = session
        
        class Person(Entity):
            firstname = Field(String(30))
            surname = Field(String(30))

        setup_all()
        create_all(engine)

        homer = Person(firstname="Homer", surname='Simpson')
        bart = Person(firstname="Bart", surname='Simpson')
        session.flush()
        
        assert Person.query.session is session()
        assert Person.query.filter_by(firstname='Homer').one() is homer

        del __session__
        
class TestTableOptions(object):
    def setup(self):
        metadata.bind = 'sqlite:///'

    def teardown(self):
        cleanup_all()

    def test_unique_constraint(self):
        
        class Person(Entity):
            firstname = Field(String(30))
            surname = Field(String(30))

            using_table_options(UniqueConstraint('firstname', 'surname'))

        setup_all(True)

        homer = Person(firstname="Homer", surname='Simpson')
        bart = Person(firstname="Bart", surname='Simpson')

        session.flush()

        homer2 = Person(firstname="Homer", surname='Simpson')

        raised = False
        try:
            session.flush()
        except SQLError:
            raised = True

        assert raised

    def test_unique_constraint_belongs_to(self):
        class Author(Entity):
            name = Field(String(50))

        class Book(Entity):
            title = Field(String(200), required=True)
            author = ManyToOne("Author")

            using_table_options(UniqueConstraint("title", "author_id"))

        setup_all(True)

        tolkien = Author(name="J. R. R. Tolkien")
        lotr = Book(title="The Lord of the Rings", author=tolkien)
        hobbit = Book(title="The Hobbit", author=tolkien)

        session.flush()

        tolkien2 = Author(name="Tolkien")
        hobbit2 = Book(title="The Hobbit", author=tolkien2)

        session.flush()

        hobbit3 = Book(title="The Hobbit", author=tolkien)

        raised = False
        try:
            session.flush()
        except SQLError:
            raised = True

        assert raised

