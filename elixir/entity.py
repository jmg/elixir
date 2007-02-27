'''
Entity baseclass, metaclass and descriptor
'''

from sqlalchemy                     import Table, Integer, desc, deferred
from sqlalchemy.ext.assignmapper    import assign_mapper
from elixir.statements              import Statement
from elixir.fields                  import Field
from elixir.options                 import options_defaults

try:
    set
except NameError:
    from sets import Set as set

import sys
import elixir


__all__ = ['Entity']

__pudge_all__ = __all__

DEFAULT_AUTO_PRIMARYKEY_NAME = "id"
DEFAULT_AUTO_PRIMARYKEY_TYPE = Integer


class EntityDescriptor(object):
    '''
    EntityDescriptor describes fields and options needed for table creation.
    '''
    
    uninitialized_rels = set()
    current = None
    
    def __init__(self, entity):
        entity.table = None
        entity.mapper = None

        self.entity = entity
        self.module = sys.modules[entity.__module__]

        self.primary_keys = list()

        self.parent = None
        for base in entity.__bases__:
            if issubclass(base, Entity) and base is not Entity:
                if self.parent:
                    raise Exception('%s entity inherits from several entities,'
                                    ' and this is not supported.' 
                                    % self.entity.__name__)
                else:
                    self.parent = base

        self.fields = dict()
        self.relationships = dict()
        self.constraints = list()

        #CHECKME: this is a workaround for the "current" descriptor/target
        # property ugliness. The problem is that this workaround is ugly too.
        # I'm not sure if this is a safe practice. It works but...?
#        setattr(self.module, entity.__name__, entity)

        # set default value for options
        self.order_by = None
        self.tablename = None
        self.table_args = list()
        self.metadata = getattr(self.module, 'metadata', elixir.metadata)

        for option in ('inheritance', 
                       'autoload', 'shortnames', 'auto_primarykey'):
            setattr(self, option, options_defaults[option])

        for option_dict in ('mapper_options', 'table_options'):
            setattr(self, option_dict, options_defaults[option_dict].copy())
    
    def setup_options(self):
        '''
        Setup any values that might depend on using_options. For example, the 
        tablename or the metadata.
        '''
        elixir.metadatas.add(self.metadata)

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
        Create tables, keys, columns that have been specified so far and 
        assign a mapper. Will be called when an instance of the entity is 
        created or a mapper is needed to access one or many instances of the 
        entity. It will try to initialize the entity's relationships (along 
        with any delayed relationship) but some of them might be delayed.
        '''
        if elixir.delay_setup:
            elixir.delayed_entities.add(self)
            return

        self.setup_table()
        self.setup_mapper()

        # This marks all relations of the entity (or, at least those which 
        # have been added so far by statements) as being uninitialized
        EntityDescriptor.uninitialized_rels.update(
            self.relationships.values())

        # try to setup all uninitialized relationships
        EntityDescriptor.setup_relationships()
    
    def translate_order_by(self, order_by):
        if isinstance(order_by, basestring):
            order_by = [order_by]
        
        order = list()
        for field in order_by:
            col = self.fields[field.strip('-')].column
            if field.startswith('-'):
                col = desc(col)
            order.append(col)
        return order

    def setup_mapper(self):
        '''
        Initializes and assign an (empty!) mapper to the entity.
        '''
        if self.entity.mapper:
            return
        
        session = getattr(self.module, 'session', elixir.objectstore)
        
        kwargs = self.mapper_options
        if self.order_by:
            kwargs['order_by'] = self.translate_order_by(self.order_by)
        
        if self.parent:
            if self.inheritance == 'single':
                # at this point, we don't know whether the parent relationships
                # have already been processed or not. Some of them might be, 
                # some other might not.
                if not self.parent.mapper:
                    self.parent._descriptor.setup_mapper()
                kwargs['inherits'] = self.parent.mapper

        properties = dict()
        for field in self.fields.itervalues():
            if field.deferred:
                group = None
                if isinstance(field.deferred, basestring):
                    group = field.deferred
                properties[field.column.name] = deferred(field.column,
                                                         group=group)

        assign_mapper(session.context, self.entity, self.entity.table,
                      properties=properties, **kwargs)


    def setup_table(self):
        '''
        Create a SQLAlchemy table-object with all columns that have been 
        defined up to this point.
        '''
        if self.entity.table:
            return
        
        if self.parent:
            if self.inheritance == 'single':
                # reuse the parent's table
                if not self.parent.table:
                    self.parent._descriptor.setup_table()
                    
                self.entity.table = self.parent.table 
                self.primary_keys = self.parent._descriptor.primary_keys

                # re-add the entity fields to the parent entity so that they
                # are added to the parent's table (whether the parent's table
                # is setup already or not).
                for field in self.fields.itervalues():
                    self.parent._descriptor.add_field(field)

                return
#            elif self.inheritance == 'concrete':
                # do not reuse parent table, but copy all fields
                # the problem is that, at this points, all "plain" fields
                # are known, but not those generated by relations
#                for field in self.fields.itervalues():
#                    self.add_field(field)

        if not self.autoload:
            if not self.primary_keys and self.auto_primarykey:
                self.create_auto_primary_key()

        # create list of columns and constraints
        args = [field.column for field in self.fields.itervalues()] \
                    + self.constraints + self.table_args
        
        # specify options
        kwargs = self.table_options

        if self.autoload:
            kwargs['autoload'] = True
       
        self.entity.table = Table(self.tablename, self.metadata, 
                                  *args, **kwargs)
    
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
    
    def add_constraint(self, constraint):
        self.constraints.append(constraint)
        
        table = self.entity.table
        if table:
            table.append_constraint(constraint)
        
    def get_inverse_relation(self, rel, reverse=False):
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
                            "relation in entity '%s'. You should specify "
                            "inverse relations manually by using the inverse "
                            "keyword."
                            % (rel.name, rel.entity.__name__) 
                          )
        # When a matching inverse is found, we check that it has only
        # one relation matching as its own inverse. We don't need the result
        # of the method though. But we do need to be careful not to start an
        # infinite recursive loop.
        if matching_rel and not reverse:
            rel.entity._descriptor.get_inverse_relation(matching_rel, True)

        return matching_rel

    @property
    def all_relationships(self):
        if self.parent:
            res = self.parent._descriptor.all_relationships
        else:
            res = dict()
        res.update(self.relationships)
        return res

    def setup_relationships(cls):
        for relationship in list(EntityDescriptor.uninitialized_rels):
            if relationship.setup():
                EntityDescriptor.uninitialized_rels.remove(relationship)
    setup_relationships = classmethod(setup_relationships)


class Entity(object):
    '''
    The base class for all entities
    
    All Elixir model objects should inherit from this class. Statements can
    appear within the body of the definition of an entity to define its
    fields, relationships, and other options.
    
    Here is an example:

    ::
    
        class Person(Entity):
            has_field('name', Unicode(128))
            has_field('birthdate', DateTime, default=datetime.now)
    
    Please note, that if you don't specify any primary keys, Elixir will
    automatically create one called ``id``.
    
    For further information, please refer to the provided examples or
    tutorial.
    '''
    
    class __metaclass__(type):
        def __init__(cls, name, bases, dict_):
            # only process subclasses of Entity, not Entity itself
            if bases[0] is object:
                return

            # create the entity descriptor
            desc = cls._descriptor = EntityDescriptor(cls)
            EntityDescriptor.current = desc
            
            # process statements
            Statement.process(cls)
            
            # setup misc options here (like tablename etc.)
            desc.setup_options()
            
            # create table & assign (empty) mapper
            desc.setup()

