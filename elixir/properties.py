'''
Special properties statements for Elixir entities

==========
Properties
==========

This module contains DSL statements which allow you to declare special 
properties your Elixir entities might have.  For simple fields or 
relationships between your entities, please see the corresponding modules.

`has_property`
--------------
The `has_property` statement allows you to define properties which rely on 
their entity's table and columns (an thus which need them to be defined before
the property can be declared).

Here is a quick example of how to use ``has_property``.

.. sourcecode:: python

    class OrderLine(Entity):
        has_field('quantity', Float)
        has_field('unit_price', Float)
        has_property('price', 
                     lambda c: column_property(
                         (c.quantity * c.unit_price).label('price')))
'''

from elixir.statements import PropertyStatement
from sqlalchemy.orm import column_property


class EntityBuilder(object):
    #TODO: add stub methods (create_cols, etc...)
    #XXX: add helper methods: add_property, etc... here?
    # either in addition to in EntityDescriptor or instead of there.
    pass


class PropertyMeta(type):
    counter = 0

    def __call__(self, *args, **kwargs):
        instance = type.__call__(self, *args, **kwargs)
        instance._counter = PropertyMeta.counter
        PropertyMeta.counter += 1
        return instance


class Property(EntityBuilder):
    __metaclass__ = PropertyMeta
    
    def __init__(self, *args, **kwargs):
        self.entity = None
        self.name = None

    def attach(self, entity, name):
        """Attach this property to its entity, using 'name' as name.

        Note that properties will not necessarily be attached in the order 
        they were declared.
        """
        self.entity = entity
        self.name = name

        # register this property as a builder
        entity._descriptor.builders.append(self)

    def __repr__(self):
        return "Property(%s, %s)" % (self.name, self.entity)


class GenericProperty(Property):
    def __init__(self, prop):
        super(GenericProperty, self).__init__()
        self.prop = prop

    def create_properties(self):
        if callable(self.prop):
            prop_value = self.prop(self.entity.table.c)
        else:
            prop_value = self.prop
        prop_value = self.evaluate_property(prop_value)
        self.entity.mapper.add_property(self.name, prop_value)

    def evaluate_property(self, prop):
        return prop

class ColumnProperty(GenericProperty):
    def evaluate_property(self, prop):
        return column_property(prop.label(self.name))

#class Composite(GenericProperty):
#    def __init__(self, prop):
#        super(GenericProperty, self).__init__()
#        self.prop = prop

#    def evaluate_property(self, prop):
#        return composite(prop.label(self.name))

#start = Composite(Point, lambda c: (c.x1, c.y1))

#mapper(Vertex, vertices, properties={
#    'start':composite(Point, vertices.c.x1, vertices.c.y1),
#    'end':composite(Point, vertices.c.x2, vertices.c.y2)
#})


has_property = PropertyStatement(GenericProperty)

