'''
Elixir package

A declarative layer on top of SQLAlchemy, which is intended to replace the
ActiveMapper SQLAlchemy extension, and the TurboEntity project.  Elixir is a
fairly thin wrapper around SQLAlchemy, which provides the ability to define
model objects following the Active Record design pattern, and using a DSL
syntax similar to that of the Ruby on Rails ActiveRecord system.

Elixir does not intend to replace SQLAlchemy's core features, but instead
focuses on providing a simpler syntax for defining model objects when you do
not need the full expressiveness of SQLAlchemy's manual mapper definitions.

For an example of how to use Elixir, please refer to the examples directory
and the unit tests. The examples directory includes a TurboGears application
with full identity support called 'videostore'.
'''

import sqlalchemy

from sqlalchemy.types import *

from elixir.options import using_options, using_table_options, \
                           using_mapper_options, options_defaults
from elixir.entity import Entity, EntityMeta, EntityDescriptor, Objectstore
from elixir.fields import has_field, with_fields, Field
from elixir.relationships import belongs_to, has_one, has_many, \
                                 has_and_belongs_to_many
from elixir.relationships import ManyToOne, OneToOne, OneToMany, ManyToMany
from elixir.properties import has_property
from elixir.statements import Statement

try:
    set
except NameError:
    from sets import Set as set

__version__ = '0.4.0'

__all__ = ['Entity', 'EntityMeta', 'Field', 'has_field', 'with_fields',
           'has_property', 
           'belongs_to', 'has_one', 'has_many', 'has_and_belongs_to_many',
           'ManyToOne', 'OneToOne', 'OneToMany', 'ManyToMany',
           'using_options', 'using_table_options', 'using_mapper_options',
           'options_defaults', 'metadata', 'objectstore', 'session',
           'create_all', 'drop_all',
           'setup_all', 'cleanup_all'] + sqlalchemy.types.__all__

__pudge_all__ = ['create_all', 'drop_all',
                 'setup_all', 'cleanup_all',
                 'metadata', 'objectstore']

# default metadata
metadata = sqlalchemy.MetaData()

# default session
try: 
    from sqlalchemy.orm import scoped_session
    session = scoped_session(sqlalchemy.orm.create_session)
except ImportError: 
    # Not on version 0.4 of sqlalchemy
    from sqlalchemy.ext.sessioncontext import SessionContext
    session = Objectstore(SessionContext(sqlalchemy.orm.create_session))

# backward-compatible name
objectstore = session


metadatas = set()

def create_all(engine=None):
    'Create all necessary tables for all declared entities'
    for md in metadatas:
        md.create_all(bind=engine)


def drop_all(engine=None):
    'Drop all tables for all declared entities'
    for md in metadatas:
        md.drop_all(bind=engine)

_delayed_entities = list()

def setup_entities(entities):
    '''Setup all entities passed in entities'''

    for entity in entities:
        desc = entity._descriptor
        entity._ready = False
        del sqlalchemy.orm.mapper_registry[entity._class_key]

        md = desc.metadata

        # the fake table could have already been removed (namely in a 
        # single table inheritance scenario)
        md.tables.pop(entity._table_key, None)

        # restore original table iterator if not done already
        if hasattr(md.table_iterator, '_non_elixir_patched_iterator'):
            md.table_iterator = \
                md.table_iterator._non_elixir_patched_iterator

    for method_name in (
            'setup_autoload_table', 'create_pk_cols', 'setup_relkeys',
            'before_table', 'setup_table', 'setup_reltables', 'after_table',
            'setup_events',
            'before_mapper', 'setup_mapper', 'after_mapper',
            'setup_properties',
            'finalize'):
        for entity in entities:
            method = getattr(entity._descriptor, method_name)
            method()

def setup_all(create_tables=False):
    '''Setup the table and mapper for all entities which have been delayed.

    This is called automatically when any of your entities is first accessed,
    instanciated (called) or the create_all method of a metadata containing
    entities is called.
    '''
    if not _delayed_entities:
        return

    try:
        setup_entities(_delayed_entities)
    finally:
        # make sure that even if we fail to initialize, we don't leave junk for
        # others
        del _delayed_entities[:]

    # issue the "CREATE" SQL statements
    if create_tables:
        create_all()


def cleanup_all(drop_tables=False):
    '''Clear all mappers, clear the session, and clear all metadatas. 
    Optionally drops the tables.
    '''
    if drop_tables:
        drop_all()
        
    for md in metadatas:
        md.clear()
    metadatas.clear()

    objectstore.clear()
    sqlalchemy.orm.clear_mappers()



