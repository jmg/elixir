from sqlalchemy import Column
from supermodel.statements import Statement


class Field(object):
    def __init__(self, type, *args, **kwargs):
        self.colname = kwargs.pop('colname', None)
        self.type = type
        self.primary_key = kwargs.get('primary_key', False)
        
        self.args = args
        self.kwargs = kwargs
    
    @property
    def column(self):
        """Returns the corresponding sqlalchemy-column"""
    
        if hasattr(self, '_column'):
            return self._column
        
        self._column = Column(self.colname, self.type,
                              *self.args, **self.kwargs)
        return self._column


class WithFields(object):
    
    """
        Specifies all fields of an entity
    """
    
    def __init__(self, entity, *args, **fields):
        columns = list()
        desc = entity._descriptor
        
        for colname, field in fields.iteritems():
            if not field.colname:
                field.colname = colname
            desc.add_field(field)


with_fields = Statement(WithFields)
