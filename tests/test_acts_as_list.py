from elixir import *
from elixir.ext.list import acts_as_list

def setup():
    global ToDo, Person
    
    class ToDo(Entity):
        subject = Field(String(128))
        owner = ManyToOne('Person')

        def qualify(self):
            return ToDo.owner_id == self.owner_id
            
        acts_as_list(qualifier=qualify, column_name='position')
        
        def __repr__(self):
            return '<%d:%s>' % (self.position, self.subject)
    
    class Person(Entity):
        name = Field(String(64))
        todos = OneToMany('ToDo', order_by='position')
    
    
    setup_all()
    metadata.bind = 'sqlite:///'


def teardown():
    cleanup_all()


class TestActsAsList(object):
    def setup(self):
        create_all()
    
    def teardown(self):
        drop_all()
        session.clear()
    
    def test_acts_as_list(self):
        # create a person
        # you must create and flush this _before_ you attach todo's to it
        # because of the way that the plugin is implemented 
        p = Person(name='Jonathan')
        session.flush(); session.clear()
        
        # add three todos, in the reverse order that we want them
        p = Person.get(1)
        p.todos.append(ToDo(subject='Three'))
        p.todos.append(ToDo(subject='Two'))
        p.todos.append(ToDo(subject='One'))
        session.flush(); session.clear()
        
        # move the first item lower
        p = Person.get(1)
        p.todos[0].move_lower() 
        session.flush(); session.clear()
        
        # validate it worked
        p = Person.get(1)
        assert p.todos[0].subject == 'Two'
        assert p.todos[1].subject == 'Three'
        assert p.todos[2].subject == 'One'
        
        # move the last item to the top to put things in correct order
        p.todos[2].move_to_top()
        session.flush(); session.clear()
        
        # validate it worked
        p = Person.get(1)
        assert p.todos[0].subject == 'One'
        assert p.todos[1].subject == 'Two'
        assert p.todos[2].subject == 'Three'
        
        # lets shuffle them again for the sake of testing move_to_bottom
        # and move_to_top
        p.todos[2].move_to_top()
        session.flush(); session.clear()
        
        p = Person.get(1)
        assert p.todos[0].subject == 'Three'
        assert p.todos[1].subject == 'One'
        assert p.todos[2].subject == 'Two'
        
        p.todos[1].move_to_bottom()
        session.flush(); session.clear()
        
        p = Person.get(1)
        assert p.todos[0].subject == 'Three'
        assert p.todos[1].subject == 'Two'
        assert p.todos[2].subject == 'One'
                
        # lets move everything back to how it should be
        p = Person.get(1)
        p.todos[0].move_to(3)
        p.todos[2].move_to(1)
        session.flush(); session.clear()
        
        # validate it worked
        p = Person.get(1)
        assert p.todos[0].subject == 'One'
        assert p.todos[0].position == 1
        assert p.todos[1].subject == 'Two'
        assert p.todos[1].position == 2
        assert p.todos[2].subject == 'Three'
        assert p.todos[2].position == 3
                
        # delete the second todo list item
        p.todos[1].delete()
        session.flush(); session.clear()
        
        # validate that the deletion worked, and sequence numebers
        # were properly managed        
        p = Person.get(1)
        assert p.todos[0].subject == 'One'
        assert p.todos[0].position == 1
        assert p.todos[1].subject == 'Three'
        assert p.todos[1].position == 2