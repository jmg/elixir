import sys

__pudge_all__ = []

STATEMENTS = '__elixir_statements__'

class Statement(object):    
    '''
    DSL-style syntax
    
    A ``Statement`` object represents a DSL term.
    '''
    
    def __init__(self, target, when='init'):
        '''
        target is the class which will handle this statement. For example, the
        BelongsTo class handles the belongs_to statement.
        '''
        self.target = target
        self.when = when
    
    def __call__(self, *args, **kwargs):
        # jam this statement into one of the class's statement lists
        class_locals = sys._getframe(1).f_locals
        statement_map = class_locals.setdefault(STATEMENTS, {})
        statements = statement_map.setdefault(self.when, [])
        statements.append((self, args, kwargs))
    
    @classmethod
    def finalize(cls, entity, when='init'):
        statement_map = getattr(entity, STATEMENTS, {})
        statements = statement_map.get(when, [])
        for statement, args, kwargs in statements:
            getattr(statement.target, 'finalize', lambda x: None)(entity)
    
    @classmethod
    def process(cls, entity, when):
        '''
        Apply all statements to the given entity.
        '''
        # loop over all statements in the class's statement list named "when"
        # and apply them, i.e. instanciate the corresponding classes
        statement_map = getattr(entity, STATEMENTS, {})
        statements = statement_map.get(when, [])
        for statement, args, kwargs in statements:
            statement.target(entity, *args, **kwargs)
