from elixir.statements import Statement

__all__ = [
    'using_options'
]


class UsingOptions(object):
    '''
    The 'using_options' DSL statement allows you to set up some additional
    behaviors on your model objects, including table names, ordering, and
    more.  To specify an option, simply supply the option as a keyword 
    argument onto the statement, as follows:
    
        class Person(Entity):
            has_field('name', Unicode(64))
            using_options(shortnames=True, order_by='name')
    
    The list of supported arguments are as follows:
    
        * metadata:         Specify a custom MetaData.
    
        * autoload:         Automatically load column definitions from the 
                            existing database table.
    
        * tablename:        Specify a custom tablename.
    
        * shortnames:       Usually tablenames include the full module-path to 
                            the entity, but lower-cased and separated by 
                            underscores ("_"), eg.: "project1_model_myentity", 
                            for an entity named "MyEntity" in the module 
                            "project1.model".  If shortnames is True, the 
                            tablename will just be the entity's classname 
                            lower-cased, ie. "myentity".
                                    
        * auto_primarykey:  If given as string, it will represent the 
                            auto-primary-key's column name.  If this option is
                        
                                True: Allow auto-creation of a primary key,
                                      if there's no primary key defined for
                                      the corresponding entity.
                            
                                False: Disallow auto-creation of a primary key.
                            
        * order_by:         How to order select results. Either a string or a 
                            list of strings, composed of the field name, 
                            optionally lead by a minus (descending order).
                        
        * extension:        Use one or more MapperExtensions.
        * mapper_options:   Pass additional keyword arguments to the entity
                            mapper.
        * table_options:    Pass additional keyword arguments to the entity 
                            table.
    '''
    
    valid_options = (
        'metadata',
        'autoload',
        'tablename',
        'shortnames',
        'auto_primarykey',
        'order_by',
        'extension',
        'mapper_options',
        'table_options'
    )
    
    def __init__(self, entity, *args, **kwargs):
        desc = entity._descriptor
        
        for kwarg in kwargs:
            if kwarg in UsingOptions.valid_options:
                setattr(desc, kwarg, kwargs[kwarg])


using_options = Statement(UsingOptions)
