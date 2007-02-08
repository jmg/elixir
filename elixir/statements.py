__pudge_all__ = []

class Statement(object):    
    '''
    DSL-style syntax
    
    A ``Statement`` object represents a DSL term.
    '''
    
    statements = []
    
    def __init__(self, target):
        self.target = target
    
    def __call__(self, *args, **kwargs):
        Statement.statements.append((self, args, kwargs))
    
    @classmethod
    def process(cls, entity):
        '''
        Apply all statements to the given entity.
        '''
        
        for statement, args, kwargs in Statement.statements:
            statement.target(entity, *args, **kwargs)
        Statement.statements = []
