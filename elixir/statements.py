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
        target is the class which will handle this statement. For example, the
        BelongsTo class handles the belongs_to statement.
        '''
        self.target = target
    
    def __call__(self, *args, **kwargs):
        # jam this statement into the class's statement list
        class_locals = sys._getframe(1).f_locals
        statements = class_locals.setdefault(STATEMENTS, [])
        statements.append((self, args, kwargs))
    
    @classmethod
    def process(cls, entity, when=None):
        '''
        Apply all statements to the given entity.
        '''
        # loop over all statements in the class's statement list
        # and apply them, i.e. instanciate the corresponding classes
        statements = getattr(entity, STATEMENTS, [])
        for num, statement in enumerate(statements):
            # replace the statement "definition tuple" by its instance
            if isinstance(statement, tuple):
                statement, args, kwargs = statement
                statements[num] = statement.target(entity, *args, **kwargs)
            else:
                # otherwise, call the corresponding method
                if when and hasattr(statement, when):
                    getattr(statement, when)()

