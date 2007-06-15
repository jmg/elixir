'''
Special properties statements for Elixir entities

==========
Properties
==========

This module contains DSL statements which allow you to declare special 
properties your Elixir entities might have.  For simple fields or relation
between your entities, please the corresponding modules.

`has_property`
--------------
The `has_property` statement allows you to define properties which rely on 
their entity's table and columns (an thus which need them to be defined before
the property can be declared).

Here is a quick example of how to use ``has_property``.

::

    class OrderLine(Entity):
        has_field('quantity', Float)
        has_field('unit_price', Float)
        has_property('price', 
                     lambda c: column_property(
                         (c.quantity * c.unit_price).label('price')))
'''

from elixir.statements import Statement

class HasProperty(object):

    def __init__(self, entity, name, prop):
        entity._descriptor.add_property(name, prop)


has_property = Statement(HasProperty)

