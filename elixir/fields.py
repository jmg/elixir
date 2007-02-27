'''
Field statements for Elixir entities

======
Fields
======

This module contains DSL statements which allow you to declare which 
fields (columns) your Elixir entities have.  There are currently two
different statements that you can use to declare fields:


`has_field`
-----------
The `has_field` statement allows you to define fields one at a time.

The first argument is the name of the field, the second is its type. Following
these, any number of keyword arguments can be specified for additional 
behavior. The following arguments are supported:

+-------------------+---------------------------------------------------------+
| Argument Name     | Description                                             |
+===================+=========================================================+
| ``required``      | Specify whether or not this field can be set to None    |
|                   | (left without a value). Defaults to ``False``, unless   | 
|                   | the field is a primary key.                             |
+-------------------+---------------------------------------------------------+
| ``deferred``      | Specify whether this particular column should be        |
|                   | fetched by default (along with the other columns) when  |
|                   | an instance of the entity is fetched from the database  | 
|                   | or rather only later on when this particular column is  |
|                   | first referenced. This can be useful when one wants to  |
|                   | avoid loading a large text or binary field into memory  |
|                   | when its not needed. Individual columns can be lazy     |
|                   | loaded by themselves (by using ``deferred=True``)       |
|                   | or placed into groups that lazy-load together (by using |
|                   | ``deferred`` = `"group_name"`).                         |
+-------------------+---------------------------------------------------------+

Any other keyword argument is passed on to the SQLAlchemy
``Column`` object. Please refer to the `SQLAlchemy Column object's
documentation <http://www.sqlalchemy.org/docs/docstrings.myt
#docstrings_sqlalchemy.schema_Column>`_ for further detail about which 
keyword arguments are supported.

Here is a quick example of how to use ``has_field``.

::

    class Person(Entity):
        has_field('id', Integer, primary_key=True)
        has_field('name', String(50))


`with_fields`
-------------
The `with_fields` statement allows you to define fields all at once.

Each keyword argument to this statement represents one field, which should
be a `Field` object. The first argument to a Field object is its type. 
Following it, any number of keyword arguments can be specified for
additional behavior. The `with_fields` statement supports the same keyword 
arguments than the `has_field` statement.

Here is a quick example of how to use ``with_fields``.

::

    class Person(Entity):
        with_fields(
            id = Field(Integer, primary_key=True),
            name = Field(String(50))
        )
'''

from sqlalchemy             import Column
from elixir.statements      import Statement

__all__ = ['has_field', 'with_fields', 'Field']

__pudge_all__ = ['Field']

class Field(object):
    '''
    Represents the definition of a 'field' on an entity.
    
    This class represents a column on the table where the entity is stored.
    This object is only used with the `with_fields` syntax for defining all
    fields for an entity at the same time. The `has_field` syntax does not
    require the manual creation of this object.
    '''
    
    def __init__(self, type, *args, **kwargs):
        self.colname = kwargs.pop('colname', None)
        self.deferred = kwargs.pop('deferred', False)
        if 'required' in kwargs:
            kwargs['nullable'] = not kwargs.pop('required')
        self.type = type
        self.primary_key = kwargs.get('primary_key', False)
        
        self.args = args
        self.kwargs = kwargs
    
    def column(self):
        '''
        Returns the corresponding sqlalchemy-column
        '''
    
        if not hasattr(self, '_column'):
            self._column = Column(self.colname, self.type,
                                  *self.args, **self.kwargs)
        return self._column
    column = property(column)


class HasField(object):
    def __init__(self, entity, name, *args, **kwargs):
        field = Field(*args, **kwargs)
        field.colname = name
        entity._descriptor.add_field(field)


class WithFields(object):
    def __init__(self, entity, *args, **fields):
        columns = list()
        desc = entity._descriptor
        
        for colname, field in fields.iteritems():
            if not field.colname:
                field.colname = colname
            desc.add_field(field)

has_field = Statement(HasField)
with_fields = Statement(WithFields)
