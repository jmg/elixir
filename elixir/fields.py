'''
Field statements for Elixir entities

======
Fields
======

This module contains DSL statements which allow you to declare which 
fields (columns) your Elixir entities have.  There are currently two
different ways to declare your entities fields: through the has_field_
statement, and by using the `Object-oriented syntax`_. Note that the 
with_fields_ statement is currently deprecated in favor of the 
`Object-oriented syntax`_.


has_field
---------
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
| ``through``       | Specify a relation name to go through. This field will  |
|                   | not exist as a column on the database but will be a     |
|                   | property which automatically proxy values to the        |
|                   | ``attribute`` attribute of the object pointed to by the |
|                   | relation. If the ``attribute`` argument is not present, |
|                   | the name of the current field will be used. In an       |
|                   | has_field statement, you can only proxy through a       |
|                   | belongs_to or an has_one relationship.                  |
+-------------------+---------------------------------------------------------+
| ``attribute``     | Name of the "endpoint" attribute to proxy to. This      |
|                   | should only be used in combination with the ``through`` |
|                   | argument.                                               |
+-------------------+---------------------------------------------------------+

Any other keyword argument is passed on to the SQLAlchemy
``Column`` object. Please refer to the `SQLAlchemy Column object's
documentation <http://www.sqlalchemy.org/docs/docstrings.myt
#docstrings_sqlalchemy.schema_Column>`_ for further detail about which 
keyword arguments are supported.

Here is a quick example of how to use ``has_field``.

.. sourcecode:: python

    class Person(Entity):
        has_field('id', Integer, primary_key=True)
        has_field('name', String(50))

Object-oriented syntax
----------------------

Here is a quick example of how to use the object-oriented syntax.

.. sourcecode:: python

    class Person(Entity):
        id = Field(Integer, primary_key=True)
        name = Field(String(50))

with_fields
-----------
The `with_fields` statement is **deprecated** in favor of the `Object-oriented
syntax`_. It allows you to define all fields of an entity at once. 
Each keyword argument to this statement represents one field, which should
be a `Field` object. The first argument to a Field object is its type. 
Following it, any number of keyword arguments can be specified for
additional behavior. The `with_fields` statement supports the same keyword 
arguments than the `has_field` statement.

Here is a quick example of how to use ``with_fields``.

.. sourcecode:: python

    class Person(Entity):
        with_fields(
            id = Field(Integer, primary_key=True),
            name = Field(String(50))
        )
'''
import sys

from sqlalchemy import Column
from sqlalchemy.orm import deferred
from sqlalchemy.ext.associationproxy import association_proxy

from elixir.statements import ClassMutator
from elixir.properties import Property

__doc_all__ = ['Field']


class Field(Property):
    '''
    Represents the definition of a 'field' on an entity.
    
    This class represents a column on the table where the entity is stored.
    This object is only used with the `with_fields` syntax for defining all
    fields for an entity at the same time. The `has_field` syntax does not
    require the manual creation of this object.
    '''
    
    def __init__(self, type, *args, **kwargs):
        super(Field, self).__init__()
        
        self.colname = kwargs.pop('colname', None)
        self.deferred = kwargs.pop('deferred', False)
        if 'required' in kwargs:
            kwargs['nullable'] = not kwargs.pop('required')
        self.type = type
        self.primary_key = kwargs.get('primary_key', False)

        self.column = None
        self.property = None
        
        self.args = args
        self.kwargs = kwargs

    def attach(self, entity, name):
        # If no colname was defined (through the 'colname' kwarg), set
        # it to the name of the attr.
        if self.colname is None:
            self.colname = name
        super(Field, self).attach(entity, name)

    def create_pk_cols(self):
        if self.primary_key:
            self.create_col()

    def create_non_pk_cols(self):
        if not self.primary_key:
            self.create_col()

    def create_col(self):
        self.column = Column(self.colname, self.type,
                             *self.args, **self.kwargs)
        self.entity._descriptor.add_column(self.column)

    def create_properties(self):
        if self.deferred:
            group = None
            if isinstance(self.deferred, basestring):
                group = self.deferred
            self.property = deferred(self.column, group=group)
        elif self.name != self.colname:
            self.property = self.column

        if self.property:
            self.entity.mapper.add_property(self.name, self.property)



def has_field_handler(entity, name, *args, **kwargs):
    if 'through' in kwargs:
        setattr(entity, name, 
                association_proxy(kwargs.pop('through'), 
                                  kwargs.pop('attribute', name),
                                  **kwargs))
        return
    field = Field(*args, **kwargs)
    field.attach(entity, name)


def with_fields_handler(entity, *args, **fields):
    for name, field in fields.iteritems():
        field.attach(entity, name)


has_field = ClassMutator(has_field_handler)
with_fields = ClassMutator(with_fields_handler)
