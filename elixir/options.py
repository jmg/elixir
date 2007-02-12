'''
Option statements for Elixir entities

=======
Options
=======

This module provides DSL statements for defining options on your Elixir
entities.  There are three different kinds of options that can be set 
up, and for this there are three different statements: using_options_,
using_table_options_ and using_mapper_options_. Alternatively, options can be
set on all Elixir entities by modifying the `options_defaults` dictionary
before defining any entity.

`using_options`
---------------
The 'using_options' DSL statement allows you to set up some additional
behaviors on your model objects, including table names, ordering, and
more.  To specify an option, simply supply the option as a keyword 
argument onto the statement, as follows:

::

    class Person(Entity):
        has_field('name', Unicode(64))

        using_options(shortnames=True, order_by='name')

The list of supported arguments are as follows:

+---------------------+-------------------------------------------------------+
| Option Name         | Description                                           |
+=====================+=======================================================+
| ``metadata``        | Specify a custom MetaData                             |
+---------------------+-------------------------------------------------------+
| ``autoload``        | Automatically load column definitions from the        |
|                     | existing database table.  For now, it does **not**    |
|                     | work for ``has_and_belongs_to_many`` relationships.   |
|                     | Using autoloaded tables implies setting               |
|                     | ``delay_setup`` to ``True`` before defining your      |
|                     | entities.                                             |
+---------------------+-------------------------------------------------------+
| ``tablename``       | Specify a custom tablename                            |
+---------------------+-------------------------------------------------------+
| ``shortnames``      | Usually tablenames include the full module-path       |
|                     | to the entity, but lower-cased and separated by       |
|                     | underscores ("_"), eg.: "project1_model_myentity"     |
|                     | for an entity named "MyEntity" in the module          |
|                     | "project1.model".  If shortnames is True, the         |
|                     | tablename will just be the entity's classname         |
|                     | lower-cased, ie. "myentity".                          |
+---------------------+-------------------------------------------------------+
| ``auto_primarykey`` | If given as string, it will represent the             |
|                     | auto-primary-key's column name.  If this option       |
|                     | is True, it will allow auto-creation of a primary     |
|                     | key if there's no primary key defined for the         |
|                     | corresponding entity.  If this option is False,       |
|                     | it will disallow auto-creation of a primary key.      |
+---------------------+-------------------------------------------------------+
| ``order_by``        | How to order select results. Either a string or a     |
|                     | list of strings, composed of the field name,          |
|                     | optionally lead by a minus (descending order).        |
+---------------------+-------------------------------------------------------+

For examples, please refer to the examples and unit tests.


`using_table_options`
---------------------
The 'using_table_options' DSL statement allows you to set up some 
additional options on your entity table. It is meant only to handle the 
options which are not supported directly by the 'using_options' statement.
By opposition to the 'using_options' statement, these options are passed 
directly to the underlying SQLAlchemy Table object (as keyword arguments) 
without any processing.

For further information, please refer to the `SQLAlchemy table's documentation <http://www.sqlalchemy.org/docs/docstrings.myt
#docstrings_sqlalchemy.schema_Table>`_.

`using_mapper_options`
----------------------
The 'using_mapper_options' DSL statement allows you to set up some 
additional options on your entity mapper. It is meant only to handle the 
options which are not supported directly by the 'using_options' statement.
By opposition to the 'using_options' statement, these options are passed 
directly to the underlying SQLAlchemy mapper (as keyword arguments) 
without any processing.

For further information, please refer to the `SQLAlchemy mapper 
function's documentation <http://www.sqlalchemy.org/docs/adv_datamapping.myt
#advdatamapping_mapperoptions>`_.
'''

from elixir.statements import Statement

__all__ = ['using_options', 'using_table_options', 'using_mapper_options',
           'options_defaults']

__pudge_all__ = ['options_defaults']

options_defaults = dict(
    autoload=None,
    shortnames=False,
    auto_primarykey=True,
    mapper_options=dict(),
    table_options=dict(),
)

class UsingOptions(object):    
    valid_options = (
        'metadata',
        'autoload',
        'tablename',
        'shortnames',
        'auto_primarykey',
        'order_by',
    )
    
    def __init__(self, entity, *args, **kwargs):
        desc = entity._descriptor
        
        for kwarg in kwargs:
            if kwarg in UsingOptions.valid_options:
                setattr(desc, kwarg, kwargs[kwarg])


class UsingTableOptions(object):    
    def __init__(self, entity, *args, **kwargs):
        entity._descriptor.table_options.update(kwargs)


class UsingMapperOptions(object):
    def __init__(self, entity, *args, **kwargs):
        entity._descriptor.mapper_options.update(kwargs)


using_options = Statement(UsingOptions)
using_table_options = Statement(UsingTableOptions)
using_mapper_options = Statement(UsingMapperOptions)
