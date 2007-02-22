import sys

__pudge_all__ = []

STATEMENTS = '__elixir_statements__'

class Statement(object):    
    '''
    DSL-style syntax
    
    A ``Statement`` object represents a DSL term.
    '''
    
    def __init__(self, target):
        '''
        target is the class which will handle this statement
        '''
        self.target = target
    
    def __call__(self, *args, **kwargs):
        # jam this statement into the class's statement list
        class_locals = sys._getframe(1).f_locals
        statements = class_locals.setdefault(STATEMENTS, [])
        statements.append((self, args, kwargs))
        
    def process(cls, entity):
        '''
        Apply all statements to the given entity.
        '''
        # loop over all statements in the class's statement list 
        # and apply them, i.e. instanciate the corresponding classes
        for statement, args, kwargs in getattr(entity, STATEMENTS):
            statement.target(entity, *args, **kwargs)
    process = classmethod(process)
