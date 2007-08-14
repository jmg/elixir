'''
Entity baseclass, metaclass and descriptor
'''

from sqlalchemy                     import Table, Integer, String, desc,\
                                           ForeignKey
from sqlalchemy.orm                 import deferred, Query, MapperExtension
from sqlalchemy.ext.assignmapper    import assign_mapper
from sqlalchemy.util                import OrderedDict
import sqlalchemy
from elixir.statements              import Statement
from elixir.fields                  import Field
from elixir.options                 import options_defaults

try:
    set
except NameError:
    from sets import Set as set

import sys
import warnings

import elixir
import inspect

__pudge_all__ = ['Entity', 'EntityMeta']

DEFAULT_AUTO_PRIMARYKEY_NAME = "id"
DEFAULT_AUTO_PRIMARYKEY_TYPE = Integer
DEFAULT_VERSION_ID_COL = "row_version"
DEFAULT_POLYMORPHIC_COL_NAME = "row_type"
DEFAULT_POLYMORPHIC_COL_SIZE = 20
DEFAULT_POLYMORPHIC_COL_TYPE = String(DEFAULT_POLYMORPHIC_COL_SIZE)

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

        self.has_pk = False

        self.parent = None
        self.children = []

        for base in entity.__bases__:
            if issubclass(base, Entity) and base is not Entity:
                if self.parent:
                    raise Exception('%s entity inherits from several entities,'
                                    ' and this is not supported.' 
                                    % self.entity.__name__)
                else:
                    self.parent = base
                    self.parent._descriptor.children.append(entity)

        self.fields = OrderedDict()
        #TODO Ordered
        self.relationships = dict()
        self.delayed_properties = dict()
        self.constraints = list()

        # set default value for options
        self.order_by = None
        self.table_args = list()
        self.metadata = getattr(self.module, 'metadata', elixir.metadata)

        for option in ('inheritance', 'polymorphic',
                       'autoload', 'tablename', 'shortnames', 
                       'auto_primarykey',
                       'version_id_col'):
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
        if self.inheritance == 'concrete' and self.polymorphic:
            raise NotImplementedError("Polymorphic concrete inheritance is "
                                      "not yet implemented.")

        if self.parent:
            if self.inheritance == 'single':
                self.tablename = self.parent._descriptor.tablename

        if not self.tablename:
            if self.shortnames:
                self.tablename = entity.__name__.lower()
            else:
                modulename = entity.__module__.replace('.', '_')
                tablename = "%s_%s" % (modulename, entity.__name__)
                self.tablename = tablename.lower()
        elif callable(self.tablename):
            self.tablename = self.tablename(entity)
    
    def setup_events(self):
        # create a list of callbacks for each event
        methods = {}
        for name, func in inspect.getmembers(self.entity, inspect.ismethod):
            if hasattr(func, '_elixir_events'):
                for event in func._elixir_events:
                    event_methods = methods.setdefault(event, [])
                    event_methods.append(func)
        
        if not methods:
            return
        
        # transform that list into methods themselves
        for event in methods:
            methods[event] = self.make_proxy_method(methods[event])
        
        # create a custom mapper extension class, tailored to our entity
        ext = type('EventMapperExtension', (MapperExtension,), methods)()
        
        # then, make sure that the entity's mapper has our mapper extension
        self.add_mapper_extension(ext)
    
    def make_proxy_method(self, methods):
        def proxy_method(self, mapper, connection, instance):
            for func in methods:
                func(instance)
        return proxy_method
    
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
        
        if self.version_id_col:
            kwargs['version_id_col'] = self.fields[self.version_id_col].column

        if self.inheritance in ('single', 'concrete', 'multi'):
            if self.parent and \
               not (self.inheritance == 'concrete' and not self.polymorphic):
                kwargs['inherits'] = self.parent.mapper

            if self.polymorphic:
                if self.children and not self.parent:
                    kwargs['polymorphic_on'] = \
                        self.fields[self.polymorphic].column
                    if self.inheritance == 'multi':
                        children = self._get_children()
                        join = self.entity.table
                        for child in children:
                            join = join.outerjoin(child.table)
                        kwargs['select_table'] = join
                    
                if self.children or self.parent:
                    #TODO: make this customizable (both callable and string)
                    #TODO: include module name
                    kwargs['polymorphic_identity'] = \
                        self.entity.__name__.lower()

                if self.inheritance == 'concrete':
                    kwargs['concrete'] = True

        properties = dict()
        for field in self.fields.itervalues():
            if field.deferred:
                group = None
                if isinstance(field.deferred, basestring):
                    group = field.deferred
                properties[field.column.name] = deferred(field.column,
                                                         group=group)

        for name, prop in self.delayed_properties.iteritems():
            properties[name] = self.evaluate_property(prop)
        self.delayed_properties.clear()

        if 'primary_key' in kwargs:
            cols = self.entity.table.c
            kwargs['primary_key'] = [getattr(cols, colname) for
                colname in kwargs['primary_key']]

        if self.parent and self.inheritance == 'single':
            args = []
        else:
            args = [self.entity.table]

        assign_mapper(session.context, self.entity, properties=properties, 
                      *args, **kwargs)

    def _get_children(self):
        children = self.children[:]
        for child in self.children:
            children.extend(child._descriptor._get_children())
        return children

    def evaluate_property(self, prop):
        if callable(prop):
            return prop(self.entity.table.c)
        else:
            return prop

    def add_property(self, name, prop):
        if self.entity.mapper:
            prop_value = self.evaluate_property(prop)
            self.entity.mapper.add_property(name, prop_value)
        else:
            self.delayed_properties[name] = prop
    
    def add_mapper_extension(self, extension):
        extensions = self.mapper_options.get('extension', [])
        if not isinstance(extensions, list):
            extensions = [extensions]
        extensions.append(extension)
        self.mapper_options['extension'] = extensions
    
    def setup_table(self):
        '''
        Create a SQLAlchemy table-object with all columns that have been 
        defined up to this point.
        '''
        if self.entity.table:
            return
        
        if self.parent:
            if self.inheritance == 'single':
                # we know the parent is setup before the child
                self.entity.table = self.parent.table 

                # re-add the entity fields to the parent entity so that they
                # are added to the parent's table (whether the parent's table
                # is already setup or not).
                for field in self.fields.itervalues():
                    self.parent._descriptor.add_field(field)

                return
            elif self.inheritance == 'concrete':
               # copy all fields from parent table
               for field in self.parent._descriptor.fields.itervalues():
                    self.add_field(field.copy())

        if self.polymorphic and self.inheritance in ('single', 'multi') and \
           self.children and not self.parent:
            if not isinstance(self.polymorphic, basestring):
                self.polymorphic = DEFAULT_POLYMORPHIC_COL_NAME
                
            self.add_field(Field(DEFAULT_POLYMORPHIC_COL_TYPE, 
                                 colname=self.polymorphic))

        if self.version_id_col:
            if not isinstance(self.version_id_col, basestring):
                self.version_id_col = DEFAULT_VERSION_ID_COL
            self.add_field(Field(Integer, colname=self.version_id_col))

        # create list of columns and constraints
        args = [field.column for field in self.fields.itervalues()] \
                    + self.constraints + self.table_args
        
        # specify options
        kwargs = self.table_options

        if self.autoload:
            kwargs['autoload'] = True
       
        self.entity.table = Table(self.tablename, self.metadata, 
                                  *args, **kwargs)


    def create_pk_cols(self):
        """
        Create primary_key columns. That is, add columns from belongs_to
        relationships marked as being a primary_key and then adds a primary 
        key to the table if it hasn't already got one and needs one. 
        
        This method is "semi-recursive" in that it calls the create_keys 
        method on BelongsTo relationships and those in turn call create_pk_cols
        on their target. It shouldn't be possible to have an infinite loop 
        since a loop of primary_keys is not a valid situation.
        """
        for rel in self.relationships.itervalues():
            rel.create_keys(True)

        if not self.autoload:
            if self.parent and self.inheritance == 'multi':
                # add foreign keys to the parent's primary key columns 
                parent_desc = self.parent._descriptor
                for pk_col in parent_desc.primary_keys:
                    colname = "%s_%s" % (self.parent.__name__.lower(),
                                         pk_col.name)
                    field = Field(pk_col.type, ForeignKey(pk_col), 
                                  colname=colname, primary_key=True)
                    self.add_field(field)
            if not self.has_pk and self.auto_primarykey:
                self.create_auto_primary_key()


    def create_auto_primary_key(self):
        '''
        Creates a primary key
        '''
        
        if isinstance(self.auto_primarykey, basestring):
            colname = self.auto_primarykey
        else:
            colname = DEFAULT_AUTO_PRIMARYKEY_NAME
        
        self.add_field(Field(DEFAULT_AUTO_PRIMARYKEY_TYPE,
                             colname=colname, primary_key=True))
        
    def add_field(self, field):
        self.fields[field.colname] = field
        
        if field.primary_key:
            self.has_pk = True

        # we don't want to trigger setup_all too early
        table = type.__getattribute__(self.entity, 'table')
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
                            % (rel.name, rel.entity.__name__))
        # When a matching inverse is found, we check that it has only
        # one relation matching as its own inverse. We don't need the result
        # of the method though. But we do need to be careful not to start an
        # infinite recursive loop.
        if matching_rel and not reverse:
            rel.entity._descriptor.get_inverse_relation(matching_rel, True)

        return matching_rel

    def primary_keys(self):
        if self.autoload:
            return [col for col in self.entity.table.primary_key.columns]
        else:
            return [field.column for field in self.fields.itervalues() if
                    field.primary_key]
    primary_keys = property(primary_keys)

    def all_relationships(self):
        if self.parent:
            res = self.parent._descriptor.all_relationships
        else:
            res = dict()
        res.update(self.relationships)
        return res
    all_relationships = property(all_relationships)


class TriggerProxy(object):
    def __init__(self, class_, attrname, setupfunc):
        self.class_ = class_
        self.attrname = attrname
        self.setupfunc = setupfunc

    def __getattr__(self, name):
        self.setupfunc()
        proxied_attr = getattr(self.class_, self.attrname)
        return getattr(proxied_attr, name)

    def __repr__(self):
        proxied_attr = getattr(self.class_, self.attrname)
        return "<TriggerProxy (%s)>" % (self.class_.__name__)

class EntityMeta(type):
    """
    Entity meta class. 
    You should only use this if you want to define your own base class for your
    entities (ie you don't want to use the provided 'Entity' class).
    """
    _ready = False
    _entities = {}

    def __init__(cls, name, bases, dict_):
        # only process subclasses of Entity, not Entity itself
        if bases[0] is object:
            return

        cid = cls._caller = id(sys._getframe(1))
        caller_entities = EntityMeta._entities.setdefault(cid, {})
        caller_entities[name] = cls

        # create the entity descriptor
        desc = cls._descriptor = EntityDescriptor(cls)

        # process statements. Needed before the proxy for metadata
        Statement.process(cls)

        # setup misc options here (like tablename etc.)
        desc.setup_options()

        # create trigger proxies
        # TODO: support entity_name... or maybe not. I'm not sure it makes 
        # sense in Elixir.
        cls.setup_proxy()

    def setup_proxy(cls, entity_name=None):
        #TODO: move as much as possible of those "_private" values to the
        # descriptor, so that we don't mess the initial class.
        cls._class_key = sqlalchemy.orm.mapperlib.ClassKey(cls, entity_name)

        tablename = cls._descriptor.tablename
        schema = cls._descriptor.table_options.get('schema', None)
        cls._table_key = sqlalchemy.schema._get_table_key(tablename, schema)

        elixir._delayed_descriptors.append(cls._descriptor)
        
        mapper_proxy = TriggerProxy(cls, 'mapper', elixir.setup_all)
        table_proxy = TriggerProxy(cls, 'table', elixir.setup_all)

        sqlalchemy.orm.mapper_registry[cls._class_key] = mapper_proxy
        md = cls._descriptor.metadata
        md.tables[cls._table_key] = table_proxy

        # We need to monkeypatch the metadata's table iterator method because 
        # otherwise it doesn't work if the setup is triggered by the 
        # metadata.create_all().
        # This is because ManyToMany relationships add tables AFTER the list 
        # of tables that are going to be created is "computed" 
        # (metadata.tables.values()).
        # see:
        # - table_iterator method in MetaData class in sqlalchemy/schema.py 
        # - visit_metadata method in sqlalchemy/ansisql.py
        original_table_iterator = md.table_iterator
        if not hasattr(original_table_iterator, 
                       '_non_elixir_patched_iterator'):
            def table_iterator(*args, **kwargs):
                elixir.setup_all()
                return original_table_iterator(*args, **kwargs)
            table_iterator.__doc__ = original_table_iterator.__doc__
            table_iterator._non_elixir_patched_iterator = \
                original_table_iterator
            md.table_iterator = table_iterator

        cls._ready = True

    def __getattribute__(cls, name):
        if type.__getattribute__(cls, "_ready"):
            #TODO: we need to add all assign_mapper methods
            if name in ('c', 'table', 'mapper'):
                elixir.setup_all()
        return type.__getattribute__(cls, name)

    def __call__(cls, *args, **kwargs):
        elixir.setup_all()
        return type.__call__(cls, *args, **kwargs)

    def q(cls):
        return Query(cls, session=elixir.objectstore.session)
    q = property(q)


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

    __metaclass__ = EntityMeta

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def get_by(cls, *args, **kwargs):
#        warnings.warn("The get_by method on the class is deprecated."
#                      "You should use cls.query.get_by", DeprecationWarning,
#                      stacklevel=2)
        return cls.q.get_by(*args, **kwargs)
    get_by = classmethod(get_by)

    def select(cls, *args, **kwargs):
#        warnings.warn("The select method on the class is deprecated."
#                      "You should use cls.query.select", DeprecationWarning,
#                      stacklevel=2)
        return cls.q.select(*args, **kwargs)
    select = classmethod(select)


