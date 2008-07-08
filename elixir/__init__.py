'''
Elixir package

A declarative layer on top of the `SQLAlchemy library
<http://www.sqlalchemy.org/>`_. It is a fairly thin wrapper, which provides
the ability to create simple Python classes that map directly to relational
database tables (this pattern is often referred to as the Active Record design
pattern), providing many of the benefits of traditional databases
without losing the convenience of Python objects.

Elixir is intended to replace the ActiveMapper SQLAlchemy extension, and the
TurboEntity project but does not intend to replace SQLAlchemy's core features,
and instead focuses on providing a simpler syntax for defining model objects
when you do not need the full expressiveness of SQLAlchemy's manual mapper
definitions.
'''

try:
    set
except NameError:
    from sets import Set as set

import sys
import warnings

from py23compat import rsplit

import sqlalchemy
from sqlalchemy.types import *

from elixir.options import using_options, using_table_options, \
                           using_mapper_options, options_defaults
from elixir.entity import Entity, EntityMeta, EntityDescriptor, \
                          setup_entities, cleanup_entities
from elixir.fields import has_field, with_fields, Field
from elixir.relationships import belongs_to, has_one, has_many, \
                                 has_and_belongs_to_many, \
                                 ManyToOne, OneToOne, OneToMany, ManyToMany
from elixir.properties import has_property, GenericProperty, ColumnProperty, \
                              Synonym
from elixir.statements import Statement


__version__ = '0.6.0'

__all__ = ['Entity', 'EntityMeta', 'EntityCollection', 'entities',
           'Field', 'has_field', 'with_fields',
           'has_property', 'GenericProperty', 'ColumnProperty', 'Synonym',
           'belongs_to', 'has_one', 'has_many', 'has_and_belongs_to_many',
           'ManyToOne', 'OneToOne', 'OneToMany', 'ManyToMany',
           'using_options', 'using_table_options', 'using_mapper_options',
           'options_defaults', 'metadata', 'session',
           'create_all', 'drop_all',
           'setup_all', 'cleanup_all',
           'setup_entities', 'cleanup_entities'] + \
           sqlalchemy.types.__all__

__doc_all__ = ['create_all', 'drop_all',
               'setup_all', 'cleanup_all',
               'metadata', 'session']

# default session
session = sqlalchemy.orm.scoped_session(sqlalchemy.orm.sessionmaker())

# default metadata
metadata = sqlalchemy.MetaData()

metadatas = set()

# default entity collection
class EntityCollection(list):
    def __init__(self):
        # _entities is a dict of entities for each frame where there are
        # entities defined.
        self._entities = {}
#        self._entity_map = {}
        list.__init__(self)

    def map_entity(self, entity):
        self.append(entity)

        key = entity.__name__

#        if key in self._entity_map:
#            warnings.warn('An entity named `%s` is already registered!' % key)

        # 3 is because map_entity is called by:
        # EntityDescriptor::setup_options (which is called by)
        # EntityMeta::__init__
        # which is called when the entity is defined
        caller_frame = sys._getframe(3)
        cid = entity._caller = id(caller_frame)
        caller_entities = self._entities.setdefault(cid, {})
        caller_entities[key] = entity

        # Append all entities which are currently visible by the entity. This
        # will find more entities only if some of them where imported from
        # another module.
        for ent in [e for e in caller_frame.f_locals.values()
                         if isinstance(e, EntityMeta)]:
            caller_entities[ent.__name__] = ent

#        self._entity_map[key] = entity

    def resolve(self, key, entity=None):
        '''
        Resolve a key to an Entity. The optional `entity` argument is the
        "source" entity when resolving relationship targets.
        '''
        path = rsplit(key, '.', 1)
        classname = path.pop()
        #XXX: use eval()?

        if path:
            # Do we have a fully qualified entity name?
            module = sys.modules[path.pop()]
            return getattr(module, classname, None)
        else:
            # If not, try the list of entities of the "caller" of the
            # source class. Most of the time, this will be the module
            # the class is defined in. But it could also be a method
            # (inner classes).
            caller_entities = self._entities[entity._caller]
            return caller_entities[classname]

    def __getattr__(self, key):
        print "GLOBALS", globals().keys()
        print "LOCALS", locals().keys()
        return self.resolve(key)
#        return self._entity_map.get(key)

entities = EntityCollection()


def create_all(*args, **kwargs):
    '''Create the necessary tables for all declared entities'''
    for md in metadatas:
        md.create_all(*args, **kwargs)


def drop_all(*args, **kwargs):
    '''Drop tables for all declared entities'''
    for md in metadatas:
        md.drop_all(*args, **kwargs)


def setup_all(create_tables=False, *args, **kwargs):
    '''Setup the table and mapper of all entities in the default entity
    collection.

    This is called automatically if any entity of the collection is configured
    with the `autosetup` option and it is first accessed,
    instanciated (called) or the create_all method of a metadata containing
    tables from any of those entities is called.
    '''
    setup_entities(entities)

    # issue the "CREATE" SQL statements
    if create_tables:
        create_all(*args, **kwargs)


def cleanup_all(drop_tables=False, *args, **kwargs):
    '''Clear all mappers, clear the session, and clear all metadatas.
    Optionally drops the tables.
    '''
    session.rollback()
    session.clear()
    session.close()

    cleanup_entities(entities)

    sqlalchemy.orm.clear_mappers()
    entities._entities = {}
    del entities[:]

    if drop_tables:
        drop_all(*args, **kwargs)

    for md in metadatas:
        md.clear()
    metadatas.clear()


