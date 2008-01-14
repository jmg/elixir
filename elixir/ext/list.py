'''
An ordered-list plugin for Elixir to help you make an entity be able to be
managed in a list-like way. Much inspiration comes from the Ruby on Rails
acts_as_list plugin, which is currently more full-featured than this plugin.

Once you flag an entity with an `acts_as_list()` statement, a column will be
added to the entity called `position` which will be an integer column that is
managed for you by the plugin. In addition, your entity will get a series of new
methods attached to it, including:

+----------------------+------------------------------------------------------+
| Method Name          | Description                                          |
+======================+======================================================+
| ``move_lower``       | Specify a custom column name.                        |
+----------------------+------------------------------------------------------+
| ``move_higher``      | Specify whether or not this field can be set to None |
|                      | (left without a value). Defaults to ``False``,       |
|                      | unless the field is a primary key.                   |
+----------------------+------------------------------------------------------+
| ``move_to_bottom``   | Specify whether or not the column(s) created by this |
|                      | relationship should act as a primary_key.            |
|                      | Defaults to ``False``.                               |
+----------------------+------------------------------------------------------+
| ``move_to_top``      | A dictionary holding any other keyword argument you  |
|                      | might want to pass to the Column.                    |
+----------------------+------------------------------------------------------+
| ``move_to_position`` | A dictionary holding any other keyword argument you  |
|                      | might want to pass to the Column.                    |
+----------------------+------------------------------------------------------+


Sometimes, your entities that represent list items will be a part of different
lists. To implement this behavior, simply pass the `acts_as_list` statement a
callable that returns a "qualifier" SQLAlchemy expression. This expression will
be added to the generated WHERE clauses used by the plugin.

Example model usage:

.. sourcecode:: python

    from elixir import *
    from elixir.ext.list import acts_as_list
    
    class ToDo(Entity):
        subject = Field(String(128))
        owner = ManyToOne('Person')

        def qualify(self):
            return ToDo.owner_id == self.owner_id

        acts_as_list(qualify)

    class Person(Entity):
        name = Field(String(64))
        todos = OneToMany('ToDo', order_by='position')
        

The above example can then be used to manage ordered todo lists for people. Note
that you must set the `order_by` property on the `Person.todo` relation in order
for the relation to respect the ordering. Here is an example of using this model
in practice:

.. sourcecode:: python

    p = Person.query.filter_by(name='Jonathan').one()
    p.todos.append(ToDo(subject='Three'))
    p.todos.append(ToDo(subject='Two'))
    p.todos.append(ToDo(subject='One'))
    session.flush(); session.clear()
    
    p = Person.query.filter_by(name='Jonathan').one()
    p.todos[0].move_to_bottom()
    p.todos[2].move_to_top()
    session.flush(); session.clear()
    
    p = Person.query.filter_by(name='Jonathan').one()
    assert p.todos[0].subject == 'One'
    assert p.todos[1].subject == 'Two'
    assert p.todos[2].subject == 'Three'
    

For more examples, refer to the unit tests for this plugin.
'''

from elixir.statements import Statement
from elixir.events import before_insert, before_delete
from sqlalchemy import Column, Integer, select, func, literal, and_

__all__ = ['acts_as_list']
__doc_all__ = []


class ListEntityBuilder(object):
    
    def __init__(self, entity, qualifier_method=None):
        self.entity = entity
        self.qualifier_method = qualifier_method
    
    def create_non_pk_cols(self):
        self.entity._descriptor.add_column(Column('position', Integer))
    
    def after_table(self):
        qualifier_method = self.qualifier_method 
        if not qualifier_method:
            qualifier_method = lambda self: self.position==self.position
        
        @before_insert
        def _init_position(self):
            s = select(
                [(func.max(self.table.c.position)+1).label('value')],
                qualifier_method(self)
            ).union(
                select([literal(1).label('value')])
            )
            self.position = select([func.max(s.c.value)])
        
        @before_delete
        def _shift_items(self):
            self.table.update(
                and_(
                    self.table.c.position > self.position,
                    qualifier_method(self)
                ),
                values={
                    self.table.c.position : self.table.c.position - 1
                }
            ).execute()
            
        def move_to_bottom(self):        
            # move the items that were above this item up one
            self.table.update(
                and_(
                    self.table.c.position >= self.position,
                    qualifier_method(self)
                ),
                values = {
                    self.table.c.position : self.table.c.position - 1
                }
            ).execute()
            
            # move this item to the max position
            self.table.update(
                self.table.c.id == self.id,
                values={
                    self.table.c.position : select(
                        [func.max(self.table.c.position)+1],
                        qualifier_method(self)
                    )
                }
            ).execute()
            
            
        def move_to_top(self):
            # move the items that were above this item down one
            self.table.update(
                and_(
                    self.table.c.position <= self.position,
                    qualifier_method(self)
                ),
                values = {
                    self.table.c.position : self.table.c.position + 1
                }
            ).execute()

            # move this item to the first position
            self.table.update(self.table.c.id == self.id).execute(position=1)
            
        
        def move_to(self, position):
            # determine which direction we're moving
            if position < self.position:
                where = and_(
                    position <= self.table.c.position,
                    self.table.c.position < self.position,
                    qualifier_method(self)
                )
                modifier = 1
            elif position > self.position:
                where = and_(
                    self.position < self.table.c.position,
                    self.table.c.position <= position,
                    qualifier_method(self)
                )
                modifier = -1
            
            # shift the items in between the current and new positions
            self.table.update(where, values = {
                    self.table.c.position : self.table.c.position + modifier
            }).execute()
            
            # update this item's position to the desired position
            self.table.update(self.table.c.id==self.id).execute(position=position)
        
        
        def move_lower(self): self.move_to(self.position+1)
        def move_higher(self): self.move_to(self.position-1)
        
        
        self.entity._init_position = _init_position
        self.entity._shift_items = _shift_items
        self.entity.move_lower = move_lower
        self.entity.move_higher = move_higher
        self.entity.move_to_bottom = move_to_bottom
        self.entity.move_to_top = move_to_top
        self.entity.move_to = move_to


acts_as_list = Statement(ListEntityBuilder)