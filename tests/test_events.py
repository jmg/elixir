from elixir import *
from elixir.events import *

from sqlalchemy import Table, Column

stateDict = dict(
    reconstructor_called = 0,
    before_insert_called = 0,
    after_insert_called = 0,
    before_update_called = 0,
    after_update_called = 0,
    before_delete_called = 0,
    after_delete_called = 0,
    before_any_called = 0
)


def setup():
    global events, Document

    events = Table('events', metadata,
        Column('id', Integer, primary_key=True),
        Column('name', String(50))
    )
    insertRecord = events.insert()

    def record_event(name):
        stateDict[name] += 1
        insertRecord.execute(name=name)

    class Document(Entity):
        name = Field(String(50))

        try:
            def post_fetch(self):
                record_event('reconstructor_called')
            post_fetch = reconstructor(post_fetch)
        except:
            pass

        def pre_insert(self):
            record_event('before_insert_called')
        pre_insert = before_insert(pre_insert)

        def post_insert(self):
            record_event('after_insert_called')
        post_insert = after_insert(post_insert)

        def pre_update(self):
            record_event('before_update_called')
        pre_update = before_update(pre_update)

        def post_update(self):
            record_event('after_update_called')
        post_update = after_update(post_update)

        def pre_delete(self):
            record_event('before_delete_called')
        pre_delete = before_delete(pre_delete)

        def post_delete(self):
            record_event('after_delete_called')
        post_delete = after_delete(post_delete)

        def pre_any(self):
            record_event('before_any_called')
        pre_any = before_insert(before_update(before_delete(pre_any)))

    setup_all()

    metadata.bind = 'sqlite:///'


def teardown():
    cleanup_all()


class TestEvents(object):
    def setup(self):
        create_all()

    def teardown(self):
        drop_all()
        session.clear()

    def test_events(self):
        d = Document(name='My Document')
        session.commit(); session.clear()

        d = Document.query.one()
        d.name = 'My Document Updated'
        session.commit(); session.clear()

        d = Document.query.one()
        d.delete()
        session.commit(); session.clear()

        def checkCount(name, value):
            print name, value
            dictCount = stateDict[name]
            assert dictCount == value, \
                'global var count for %s should be %s but is %s' % \
                (name, value, dictCount)

            dbCount = events.select().where(events.c.name == name) \
                                     .count().execute().fetchone()[0]
            assert dbCount == value, \
                'db record count for %s should be %s but is %s' % \
                (name, value, dbCount)

        checkCount('before_insert_called', 1)
        checkCount('before_update_called', 1)
        checkCount('after_update_called', 1)
        checkCount('after_insert_called', 1)
        checkCount('before_delete_called', 1)
        checkCount('after_delete_called', 1)
        checkCount('before_any_called', 3)

        reconstructor_available = False
        try:
            reconstructor(lambda: 0)
            reconstructor_available = True
        except:
            pass

        if reconstructor_available:
            checkCount('reconstructor_called', 2)

if __name__ == '__main__':
    setup()
    test = TestEvents()
    test.setup()
    test.test_events()
    test.teardown()
