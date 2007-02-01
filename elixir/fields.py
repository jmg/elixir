from sqlalchemy             import Column
from elixir.statements      import Statement

__all__ = [
    'has_field',
    'with_fields',
    'Field'
]


class Field(object):
    
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
    Specifies one field of an entity
    '''
    
    def __init__(self, entity, name, *args, **kwargs):
        field = Field(*args, **kwargs)
        field.colname = name
        entity._descriptor.add_field(field)


class WithFields(object):
    '''
    Specifies all fields of an entity at once
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