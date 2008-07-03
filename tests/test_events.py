from elixir import *
from elixir.events import *

on_reconstitute_called = 0

before_insert_called = 0
after_insert_called  = 0
before_update_called = 0
after_update_called  = 0
before_delete_called = 0
after_delete_called  = 0

before_any_called = 0

def setup():
    global Document

    class Document(Entity):
        name = Field(String(50))

        try:
            def post_fetch(self):
                global on_reconstitute_called
                on_reconstitute_called += 1
            post_fetch = on_reconstitute(post_fetch)
        except:
            pass

        def pre_insert(self):
            global before_insert_called
            before_insert_called += 1
        pre_insert = before_insert(pre_insert)

        def post_insert(self):
            global after_insert_called
            after_insert_called += 1
        post_insert = after_insert(post_insert)

        def pre_update(self):
            global before_update_called
            before_update_called += 1
        pre_update = before_update(pre_update)

        def post_update(self):
            global after_update_called
            after_update_called += 1
        post_update = after_update(post_update)

        def pre_delete(self):
            global before_delete_called
            before_delete_called += 1
        pre_delete = before_delete(pre_delete)

        def post_delete(self):
            global after_delete_called
            after_delete_called += 1
        post_delete = after_delete(post_delete)

        def pre_any(self):
            global before_any_called
            before_any_called += 1
        pre_any = before_insert(before_update(before_delete(pre_any)))
    metadata.bind = 'sqlite:///'

    setup_all()


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

        assert before_insert_called == 1
        assert before_update_called == 1
        assert after_update_called == 1
        assert after_insert_called == 1
        assert before_delete_called == 1
        assert after_delete_called == 1
        assert before_any_called == 3
        
        on_rec_available = False
        try:
            on_reconstitute(lambda:0)
            on_rec_available = True
        except:
            pass
        
        if on_rec_available:
            assert on_reconstitute_called == 2

if __name__ == '__main__':
    setup()
    test = TestEvents()
    test.setup()
    test.test_events()
    test.teardown()
