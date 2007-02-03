from sqlalchemy             import Column
from elixir.statements      import Statement

__all__ = [
    'has_field',
    'with_fields',
    'Field'
]


class Field(object):
    '''
    Represents the definition of a 'field' on an entity.
    
    This class represents a column on the table where the entity is stored.
    This object is only used with the ``with_fields`` syntax for defining all
    fields for an entity at the same time. The ``has_field`` syntax does not
    require the manual creation of this object.
    '''
    
    def __init__(self, type, *args, **kwargs):
        self.colname = kwargs.pop('colname', None)
        self.type = type
        self.primary_key = kwargs.get('primary_key', False)
        
        self.args = args
        self.kwargs = kwargs
    
    @property
    def column(self):
        '''
        Returns the corresponding sqlalchemy-column
        '''
    
        if hasattr(self, '_column'):
            return self._column
        
        self._column = Column(self.colname, self.type,
                              *self.args, **self.kwargs)
        return self._column


class HasField(object):
    '''
    Statement object for specifying a single field on an entity.
    
    The first argument is the name of the field, the second is its type, and
    following this any number of keyword arguments can be specified for
    additional behavior. The keyword arguments are passed on to the SQLAlchemy
    ``Column`` object. Please refer to the SQLAlchemy ``Column`` object's
    documentation for further detail about which keyword arguments are
    supported.
    
    Here is a quick example of how to use ``has_field``.
    
    ::
    
        class Person(Entity):
            has_field('id', Integer, primary_key=True)
            has_field('name', String(50))
    '''
    
    def __init__(self, entity, name, *args, **kwargs):
        field = Field(*args, **kwargs)
        field.colname = name
        entity._descriptor.add_field(field)


class WithFields(object):
    '''
    Statement object for specifying all fields on an entity at once.
    
    Each keyword argument to this statement represents one field, which should
    be a Field object. The first argument to a Field object is its type, and
    following this any number of keyword arguments can be specified for
    additional behavior. The keyword arguments are passed on to the SQLAlchemy
    ``Column`` object. Please refer to the SQLAlchemy ``Column`` object's
    documentation for further detail about which keyword arguments are
    supported.
    
    Here is a quick example of how to use ``with_fields``.
    
    ::
    
        class Person(Entity):
            with_fields(
                id = Field(Integer, primary_key=True),
                name = Field(String(50))
            )
    '''
    
    def __init__(self, entity, *args, **fields):
        columns = list()
        desc = entity._descriptor
        
        for colname, field in fields.iteritems():
            if not field.colname:
                field.colname = colname
            desc.add_field(field)


has_field   = Statement(HasField)
with_fields = Statement(WithFields)
