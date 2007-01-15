"""
    Entity baseclass, metaclass and descriptor
"""

import sys
from sqlalchemy import Table, Integer, relation, desc
from sqlalchemy.orm.properties import ColumnProperty

from sqlalchemy.ext.assignmapper import assign_mapper

import supermodel
from supermodel.statements import Statement
from supermodel.fields import Field


__all__ = ['Entity']

DEFAULT_AUTO_PRIMARYKEY_NAME = "id"
DEFAULT_AUTO_PRIMARYKEY_TYPE = Integer

class Entity(object):
    
    """
        The base class for all entities
    """
    
    class __metaclass__(type):
        def __init__(cls, name, bases, dict_):
            try:
                desc = cls._descriptor = EntityDescriptor(cls)
                EntityDescriptor.current = desc
            except NameError:
                return # happens only for the base class itself
            
            Statement.process(cls)

            # setup misc options here (like tablename etc.)
            desc.setup_options()
            
            # create table & assign mapper
            desc.setup()
            
            # try to setup all uninitialized relationships
            EntityDescriptor.setup_relationships()


class EntityDescriptor(object):
    
    """
        EntityDescriptor describes fields and options
        that are needed for table creation
    """
    
    uninitialized_rels = set()
    current = None
    
    def __init__(self, entity):
        self.entity = entity
        self.primary_keys = list()
        self.order_by = None
        self.fields = dict()
        self.relationships = dict()
        self.constraints = list()
        self.module = sys.modules[entity.__module__]
        self.metadata = getattr(self.module, 'metadata', supermodel.metadata)
        self.initialized = False
        self.autoload = None
        self.auto_primarykey = True
        self.shortnames = False
        self.tablename = None
        
        entity.table = None
        entity.mapper = None
    
    def setup_options(self):
        """
            Setup any values that might depend on using_options,
            for now only the tablename
        """
        entity = self.entity
        
        if not self.tablename:
            if self.shortnames:
                self.tablename = entity.__name__.lower()
            else:
                self.tablename = entity.__module__.replace('.', '_')
                self.tablename += '_'+ entity.__name__
    
    def setup(self):
        """
            Create tables, keys, columns that have been specified so far
            and assign a mapper. Will be called when an instance of the
            entity is created or a mapper is needed to access one or many
            instances of the entity.
        """
        
        if not self.primary_keys and self.auto_primarykey:
            self.create_auto_primary_key()
        
        if not self.entity.mapper:
            self.setup_mapper()
        
        EntityDescriptor.uninitialized_rels.update(
            self.relationships.values())
    
    def setup_mapper(self):
        """
            Initializes and assign a mapper to the given entity,
            which needs a table defined, so it calls setup_table.
        """
        entity = self.entity
        
        if entity.mapper:
            return
        
        session = getattr(self.module, 'session', supermodel.objectstore)
        table = self.setup_table()
        
        kwargs = dict()
        if self.order_by:
            if isinstance(self.order_by, basestring):
                self.order_by = [self.order_by]
            
            order = list()
            for field in self.order_by:
                col = self.fields[field.strip('-')].column
                if field.startswith('-'):
                    col = desc(col)
                order.append(col)
            
            kwargs['order_by'] = order
        
        assign_mapper(session.context, entity, table, **kwargs)
        supermodel.metadatas.add(self.metadata)
    
    def setup_table(self):
        """
            Create a SQLAlchemy table-object with all columns that have
            been defined up to this point, which excludes
        """
        if self.entity.table:
            return
        
        # create list of columns and constraints
        args = [field.column for field in self.fields.values()] \
                    + self.constraints
        
        # specify options
        kwargs = dict()
        
        if self.autoload:
            kwargs['autoload'] = True
        
        table = Table(self.tablename, self.metadata, *args, **kwargs)
        table.entity_descriptor = self
        self.entity.table = table
        return table
    
    def create_auto_primary_key(self):
        """
            Creates a primary key
        """
        assert not self.primary_keys and self.auto_primarykey
        
        colname = DEFAULT_AUTO_PRIMARYKEY_NAME
        if isinstance(self.auto_primarykey, basestring):
            colname = self.auto_primarykey
        
        self.add_field(Field(DEFAULT_AUTO_PRIMARYKEY_TYPE,
                             colname=colname, primary_key=True))
        
    def add_field(self, field):
        self.fields[field.colname] = field
        
        if field.primary_key:
            self.primary_keys.append(field)
        
        table = self.entity.table
        if table:
            table.append_column(field.column)
    
    def add_constraint(self, constraint):
        self.constraints.append(constraint)
        
        table = self.entity.table
        if table:
            table.append_constraint(constraint)
        
    @classmethod
    def setup_relationships(cls):
        for relationship in list(EntityDescriptor.uninitialized_rels):
            if relationship.setup():
                EntityDescriptor.uninitialized_rels.remove(relationship)

