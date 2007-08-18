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

from sqlalchemy.ext.sessioncontext import SessionContext
from sqlalchemy.types import *

from elixir.options import using_options, using_table_options, \
                           using_mapper_options, options_defaults
from elixir.entity import Entity, EntityMeta, EntityDescriptor, Objectstore
from elixir.fields import has_field, with_fields, Field
from elixir.relationships import belongs_to, has_one, has_many, \
                                 has_and_belongs_to_many
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
           'using_options', 'using_table_options', 'using_mapper_options',
           'options_defaults', 'metadata', 'objectstore',
           'create_all', 'drop_all', 'setup_all', 'cleanup_all'] + \
          sqlalchemy.types.__all__

__pudge_all__ = ['create_all', 'drop_all', 'setup_all', 'cleanup_all',
                 'metadata', 'objectstore']

# connect
metadata = sqlalchemy.MetaData()

try:
    # this only happens when the threadlocal extension is used
    objectstore = sqlalchemy.objectstore
except AttributeError:
    objectstore = Objectstore(SessionContext(sqlalchemy.orm.create_session))

metadatas = set()


def create_all(engine=None):
    'Create all necessary tables for all declared entities'
    for md in metadatas:
        md.create_all(bind=engine)


def drop_all(engine=None):
    'Drop all tables for all declared entities'
    for md in metadatas:
        md.drop_all(bind=engine)

_delayed_descriptors = list()

def setup_all(create_tables=False):
    '''Setup the table and mapper for all entities which have been delayed.

    This is called automatically when your entity is first accessed, or ...
    [TODO: complete this]
    '''

    if not _delayed_descriptors:
        return

#TODO: define all those operations as methods on the descriptor
#    for method_name in ('setup_table', 'setup_mapper', 'setup_relkeys', ...):
#        for desc in _delayed_descriptors:
#            method = getattr(desc, method_name)
#            method()
    try:
        for desc in _delayed_descriptors:
            entity = desc.entity
            entity._ready = False
            del sqlalchemy.orm.mapper_registry[entity._class_key]

            md = desc.metadata
            # the table could have already been removed (namely in a single 
            # table inheritance scenario)
            md.tables.pop(entity._table_key, None)

            # restore original table iterator if not done already
            if hasattr(md.table_iterator, '_non_elixir_patched_iterator'):
                md.table_iterator = \
                    md.table_iterator._non_elixir_patched_iterator

        # Make sure autoloaded tables are available so that we can setup 
        # foreign keys to their columns
        for desc in _delayed_descriptors:
            if desc.autoload:
                desc.setup_table()

        for desc in _delayed_descriptors:
            desc.create_pk_cols()

        # Create other columns from belongs_to relationships.
        for desc in _delayed_descriptors:
            for rel in desc.relationships.itervalues():
                rel.create_keys(False)

        for desc in _delayed_descriptors:
            if not desc.autoload:
                desc.setup_table()

        for desc in _delayed_descriptors:
            Statement.process(desc.entity, 'before_table')

        for desc in _delayed_descriptors:
            for rel in desc.relationships.itervalues():
                rel.create_tables()

        for desc in _delayed_descriptors:
            Statement.process(desc.entity, 'after_table')

        for desc in _delayed_descriptors:
            desc.setup_events()
        
        for desc in _delayed_descriptors:
            Statement.process(desc.entity, 'before_mapper')

        for desc in _delayed_descriptors:
            desc.setup_mapper()

        for desc in _delayed_descriptors:
            Statement.process(desc.entity, 'after_mapper')

        for desc in _delayed_descriptors:
            for rel in desc.relationships.itervalues():
                rel.create_properties()

        for desc in _delayed_descriptors:
            Statement.process(desc.entity, 'finalize')

    finally:
        # make sure that even if we fail to initialize, we don't leave junk for
        # others
        del _delayed_descriptors[:]

    # issue the "CREATE" SQL statements
    if create_tables:
        create_all()


def cleanup_all(drop_tables=False):
    '''Drop table and clear mapper for all entities, and clear all metadatas.
    '''
    if drop_tables:
        drop_all()
        
    for md in metadatas:
        md.clear()
    metadatas.clear()

    objectstore.clear()
    sqlalchemy.orm.clear_mappers()

