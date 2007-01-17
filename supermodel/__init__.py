"""
    SuperModel
    
    A declarative layer on top of SQLAlchemy
"""

import sqlalchemy
from sqlalchemy.types import *

from supermodel.entity import Entity, EntityDescriptor
from supermodel.fields import Field, has_field, with_fields
from supermodel.relationships import belongs_to, has_one, has_many, \
                                     has_and_belongs_to_many
from supermodel.options import using_options

import sqlalchemy
from sqlalchemy.ext.sessioncontext import SessionContext

__all__ = ['Entity', 'Field', 'has_field', 'with_fields', 'belongs_to', 'has_one',
           'has_many', 'has_and_belongs_to_many', 'using_options',
           'create_all', 'drop_all'] + sqlalchemy.types.__all__


# connect
metadata = sqlalchemy.DynamicMetaData('supermodel')

try:
    objectstore = sqlalchemy.objectstore
except AttributeError:
    # thread local SessionContext
    class Objectstore(object):
        def __init__(self, *args, **kwargs):
            self.context = SessionContext(*args, **kwargs)
        def __getattr__(self, name):
            return getattr(self.context.current, name)
        session = property(lambda s:s.context.current)
    
    objectstore = Objectstore(sqlalchemy.create_session)

metadatas = set()

def create_all():
    """Create all necessary tables for all declared entities"""
    for md in metadatas:
        md.create_all()

def drop_all():
    """Drop all tables for all declared entities"""
    for md in metadatas:
        md.drop_all()
