'''
Associable Elixir Statement Generator

==========
Associable
==========

About Polymorphic Associations
------------------------------

A frequent pattern in database schemas is the has_and_belongs_to_many, or a 
many-to-many table. Quite often multiple tables will refer to a single one
creating quite a few many-to-many intermediate tables.

Polymorphic associations lower the amount of many-to-many tables by setting up
a table that allows relations to any other table in the database, and relates it
to the associable table. In some implementations, this layout does not enforce
referential integrity with database foreign key constraints, this implementation
uses an additional many-to-many table with foreign key constraints to avoid
this problem.

.. note:
    SQLite does not support foreign key constraints, so referential integrity
    can only be enforced using database backends with such support.

Elixir Statement Generator for Polymorphic Associations
-------------------------------------------------------

The ``associable`` function generates the intermediary tables for an Elixir
entity that should be associable with other Elixir entities and returns an
Elixir Statement for use with them. This automates the process of creating the
polymorphic association tables and ensuring their referential integrity.

Matching select_XXX and select_by_XXX are also added to the associated entity
which allow queries to be run for the associated objects.

Example usage:

::
    
    class Tag(Entity):
        has_field('name', Unicode)
    
    acts_as_taggable = associable(Tag)
    
    class Entry(Entity):
        has_field('title', Unicode)
        acts_as_taggable('tags')
    
    class Article(Entity):
        has_field('title', Unicode)
        acts_as_taggable('tags')

Or if one of the entities being associated should only have a single member of
the associated table:

::
    
    class Address(Entity):
        has_field('street', String(130))
        has_field('city', String)
    
    is_addressable = associable(Address)
    
    class Person(Entity):
        has_field('name', Unicode)
        has_many('orders', of_kind='Order')
        is_addressable('addresses')
    
    class Order(Entity):
        has_field('order_num', primary_key=True)
        has_field('item_count', Integer)
        belongs_to('person', of_kind='Person')
        is_addressable('address', uselist=False)
    
    home = Address(street='123 Elm St.', city='Spooksville')
    user = Person(name='Jane Doe')
    user.addresses.append(home)
    
    neworder = Order(item_count=4)
    neworder.address = home
    user.orders.append(neworder)
    
    # Queries using the added helpers
    Person.select_by_addresses(city='Cupertino')
    Person.select_addresses(and_(Address.c.street=='132 Elm St',
                                 Address.c.city=='Smallville'))

Statement Options
-----------------

The generated Elixir Statement has several options available:

+---------------+-------------------------------------------------------------+
| Option Name   | Description                                                 |
+===============+=============================================================+
| ``name``      | Specify a custom name for the Entity attribute. This is     |
|               | used to declare the attribute used to access the associated |
|               | table values                                                |
+---------------+-------------------------------------------------------------+
| ``uselist``   | Whether or not the associated table should be represented   |
|               | as a list, or a single property. It should be set to False  |
|               | when the entity should only have a single associated        |
|               | entity. Defaults to True.                                   |
+---------------+-------------------------------------------------------------+
| ``lazy``      | Determines eager loading of the associated entity objects.  |
|               | Defaults to False, to indicate that they should not be      |
|               | lazily loaded.                                              |
+---------------+-------------------------------------------------------------+
'''
from elixir.statements import Statement
import elixir as el
import sqlalchemy as sa

def associable(entity):
    '''
    Generate an associable Elixir Statement
    '''
    interface_name = entity.table.name
    able_name = interface_name + 'able'
    attr_name = "%s_rel" % interface_name
    
    association_table = sa.Table("%s" % able_name, entity._descriptor.metadata,
        sa.Column('%s_id' % able_name, sa.Integer, primary_key=True),
        sa.Column('%s_type' % able_name, sa.String(40), nullable=False),
    )
    
    association_to_table = sa.Table("%s_to_%s" % (able_name, interface_name), entity._descriptor.metadata,
        sa.Column('%s_id' % able_name, sa.Integer, sa.ForeignKey(getattr(association_table.c, '%s_id' % able_name), ondelete="CASCADE"), primary_key=True),
        sa.Column('%s_id' % interface_name, sa.Integer, sa.ForeignKey(entity.table.c.id, ondelete="RESTRICT"), primary_key=True),
    )
    
    entity._assoc_table = association_table
    entity._assoc_to_table = association_to_table
    assoc_entity = entity
    assoc_entity._assoc_relations = []
    
    def finder(key):
        def find_by(cls, value):
            pass
        return find_by
    
    for col in entity.table.columns.keys():
        if col != 'id':
            setattr(entity, 'find_by_%s' % col, finder(col))
    
    class GenericAssoc(object):
        def __init__(self, name):
            setattr(self, '%s_type' % able_name, name)
    
    class Associable(el.relationships.Relationship):
        """An associable Elixir Statement object"""
        def __init__(self, entity, name, uselist=True, lazy=False):
            self.entity = entity
            self.name = name
            self.lazy = lazy
            self.uselist = uselist
            assoc_entity._assoc_relations.append(entity)
            
            field = type('myfield', (object,), {})
            field.colname = '%s_assoc_id' % interface_name
            field.deferred = False
            field.primary_key = False
            field.column = sa.Column('%s_assoc_id' % interface_name, None, 
                                  sa.ForeignKey('%s.%s_id' % (able_name, able_name)))
            entity._descriptor.add_field(field)
            entity._descriptor.relationships[able_name] = self
            
            def select_by(cls, **kwargs):
                return cls.query().join(attr_name).join('targets').filter_by(**kwargs).list()
            setattr(entity, 'select_by_%s' % self.name, classmethod(select_by))
            
            def select(cls, *args, **kwargs):
                return cls.query().join(attr_name).join('targets').filter(*args, **kwargs).list()
            setattr(entity, 'select_%s' % self.name, classmethod(select))
        
        def setup(self):
            self.create_properties()
            return True
        
        def create_properties(self):
            entity = self.entity
            entity.mapper.add_property(attr_name, sa.relation(GenericAssoc, lazy=self.lazy,
                                       backref='_backref_%s' % entity.table.name))
            entity.mapper.add_property(self.name, sa.synonym(attr_name))
            if self.uselist:
                def get(self):
                    if getattr(self, attr_name) is None:
                        setattr(self, attr_name, 
                                GenericAssoc(entity.table.name))
                    return getattr(self, attr_name).targets
                setattr(entity, self.name, property(get))
            else:
                # scalar based property decorator
                def get(self):
                    return getattr(self, attr_name).targets[0]
                def set(self, value):
                    if getattr(self, attr_name) is None:
                        setattr(self, attr_name, 
                                GenericAssoc(entity.table.name))
                    getattr(self, attr_name).targets = [value]
                setattr(entity, self.name, property(get, set))
                
    sa.mapper(GenericAssoc, association_table, properties={
        'targets':sa.relation(entity, secondary=association_to_table, 
                              lazy=False, backref='association')
    })
    return Statement(Associable)
