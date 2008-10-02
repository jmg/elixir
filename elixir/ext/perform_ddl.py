'''
A table DDL plugin for Elixir.

Entities having the perform_ddl statement, will automatically execute the
DDL statement given here, at the given moment: before or after the table
creation in SQL.

Invoke as: perform_ddl(when_to_execute, ddl_statement, ddl_arg=None)

Each statement will be executed 'before-create', or 'after-create' the table,
depending on your when_to_execute parameter.
In the ddl statement given, you may use the special '%(fullname)s' construct,
that will be replaced with the real table name including schema, if unknown
to you. Also, self explained '%(table)s' and '%(schema)s' may be used here.
If the statement is a callable, and you wish to invoke it with an argument,
you may supply it as the third argument.
Finally the statement or statement returning function may consist of or return
a sequence of strings, in which case, all the sequence members will be executed
in turn.

You would use this extension to handle non elixir sql statemts, like triggers
etc, or, like me, to autopopulate this table.
If the column names should be used, use the colname value, if given.
'''

from elixir.statements     import Statement
from elixir.properties     import EntityBuilder
from sqlalchemy            import DDL

__all__ = ['perform_ddl']
__doc_all__ = []

#
# the perform_ddl statement
#

class PerformDDLEntityBuilder(EntityBuilder):

    def __init__(self, entity, when, statement, on=None, context=None):
        self.entity = entity
        self.when = when
        self.statement = statement
        self.on = on
        self.context = context

    def after_table(self):
        statement = self.statement
        if callable(statement):
            statement = statement()
        if not isinstance(statement, list):
            statement = [statement]
        for s in statement:
            ddl = DDL(s, self.on, self.context)
            ddl.execute_at(self.when, self.entity.table)

perform_ddl = Statement(PerformDDLEntityBuilder)

