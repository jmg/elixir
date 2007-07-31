from elixir import *
from elixir.ext.events import *


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
        has_field('name', Unicode)
        responds_to_events()
        
        @before_insert
        def pre_insert(self):
            global before_insert_called
            before_insert_called += 1
        
        @after_insert
        def post_insert(self):
            global after_insert_called
            after_insert_called += 1

        @before_update
        def pre_update(self):
            global before_update_called
            before_update_called += 1
        
        @after_update
        def post_update(self):
            global after_update_called
            after_update_called += 1

        @before_delete
        def pre_delete(self):
            global before_delete_called
            before_delete_called += 1
        
        @after_delete
        def post_delete(self):
            global after_delete_called
            after_delete_called += 1
    
        @before_insert
        @before_update
        @before_delete
        def pre_any(self):
            global before_any_called
            before_any_called += 1
    metadata.connect('sqlite:///')


def teardown():
    cleanup_all()


class TestEvents(object):
    def setup(self):
        create_all()
    
    def teardown(self):
        drop_all()
        objectstore.clear()
    
    def test_events(self):
        d = Document(name='My Document')
        objectstore.flush(); objectstore.clear()
        
        d = Document.get(1)
        d.name = 'My Document Updated'
        objectstore.flush(); objectstore.clear()
        
        d = Document.get(1)
        d.delete()
        objectstore.flush(); objectstore.clear()
        
        assert before_insert_called == 1
        assert before_update_called == 1
        assert after_update_called == 1
        assert after_insert_called == 1
        assert before_delete_called == 1
        assert after_delete_called == 1
        assert before_any_called == 3


if __name__ == '__main__':
    setup()
    test = TestEvents()
    test.setup()
    test.test_events()
    test.teardown()
