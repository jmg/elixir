'''
Entity baseclass, metaclass and descriptor
'''

from sqlalchemy                     import Table, Integer, desc
from sqlalchemy.ext.assignmapper    import assign_mapper
from elixir.statements              import Statement
from elixir.fields                  import Field

import sys
import elixir


__all__ = ['Entity']

DEFAULT_AUTO_PRIMARYKEY_NAME = "id"
DEFAULT_AUTO_PRIMARYKEY_TYPE = Integer

class Entity(object):
    '''
    The base class for all entities
    '''
    
    class __metaclass__(type):
        def __init__(cls, name, bases, dict_):
            try:
                desc = cls._descriptor = EntityDescriptor(cls)
                EntityDescriptor.current = desc
            except NameError:
                # TODO - do what the comment says.
                # happens only for the base class itself
                #CHECKME: checking explicitely for the name 'Entity' seem 
                # cleaner to me because it's more explicit and we wouldn't 
                # rely on code position which is always subject to change
                return 
            
            Statement.process(cls)

            # setup misc options here (like tablename etc.)
            desc.setup_options()
            
            # create table & assign mapper
            desc.setup()
            
            # try to setup all uninitialized relationships
            EntityDescriptor.setup_relationships()


class EntityDescriptor(object):
    '''
    EntityDescriptor describes fields and options needed for table creation.
    '''
    
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

        #CHECKME: this is a workaround for the "current" descriptor/target
        # property ugliness. The problem is that this workaround is ugly too.
        # I'm not sure if this is a safe practice. It works but...?
#        setattr(self.module, entity.__name__, entity)
        self.metadata = getattr(self.module, 'metadata', elixir.metadata)
        self.initialized = False
        self.autoload = None
        self.auto_primarykey = True
        self.shortnames = False
        self.tablename = None
        self.extension = None
        
        entity.table = None
        entity.mapper = None
    
    def setup_options(self):
        '''
        Setup any values that might depend on using_options (the tablename)
        '''
        
        entity = self.entity
        
        if not self.tablename:
            if self.shortnames:
                self.tablename = entity.__name__.lower()
            else:
                modulename = entity.__module__.replace('.', '_')
                tablename = "%s_%s" % (modulename, entity.__name__)
                self.tablename = tablename.lower()
    
    def setup(self):
        '''
        Create tables, keys, columns that have been specified so far and assign 
        a mapper. Will be called when an instance of the entity is created or a 
        mapper is needed to access one or many instances of the entity.
        '''
        
        if not self.primary_keys and self.auto_primarykey:
            self.create_auto_primary_key()
        
        if not self.entity.mapper:
            self.setup_mapper()
        
        EntityDescriptor.uninitialized_rels.update(
            self.relationships.values())
    
    def setup_mapper(self):
        '''
        Initializes and assign a mapper to the given entity, which needs a table
        defined, so it calls setup_table.
        '''
        
        if self.entity.mapper:
            return
        
        session = getattr(self.module, 'session', elixir.objectstore)
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
        
        if self.extension:
            kwargs['extension'] = self.extension
        
        assign_mapper(session.context, self.entity, table, **kwargs)
        elixir.metadatas.add(self.metadata)
    
    def setup_table(self):
        '''
        Create a SQLAlchemy table-object with all columns that have been defined
        up to this point.
        '''
        
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
        self.entity.table = table
        return table
    
    def create_auto_primary_key(self):
        '''
        Creates a primary key
        '''
        
        assert not self.primary_keys and self.auto_primarykey
        
        if isinstance(self.auto_primarykey, basestring):
            colname = self.auto_primarykey
        else:
            colname = DEFAULT_AUTO_PRIMARYKEY_NAME
        
        self.add_field(Field(DEFAULT_AUTO_PRIMARYKEY_TYPE,
                             colname=colname, primary_key=True))
        
    def add_field(self, field):
        self.fields[field.colname] = field
        
        if field.primary_key:
            self.primary_keys.append(field)
        
        table = self.entity.table
        if table:
            table.append_column(field.column)
    
    #FIXME: to remove. it's better to just use SA directly
    def add_constraint(self, constraint):
        self.constraints.append(constraint)
        
        table = self.entity.table
        if table:
            table.append_constraint(constraint)
        
    def get_inverse_relation(self, rel):
        '''
        Return the inverse relation of rel, if any, None otherwise.
        '''

        matching_rel = None
        for other_rel in self.relationships.itervalues():
            if other_rel.is_inverse(rel):
                if matching_rel is None:
                    matching_rel = other_rel
                else:
                    raise Exception(
                            "Several relations match as inverse of the '%s' "
                            "relation in class '%s'. You should specify "
                            "inverse relations manually by using the inverse "
                            "keyword."
                            % (rel.name, rel.entity.__name__) 
                          )
        return matching_rel

    @classmethod
    def setup_relationships(cls):
        for relationship in list(EntityDescriptor.uninitialized_rels):
            if relationship.setup():
                EntityDescriptor.uninitialized_rels.remove(relationship)

