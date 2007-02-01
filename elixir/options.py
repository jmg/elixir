from supermodel.statements import Statement


class UsingOptions(object):
    """
        Specifies all fields of an entity
    """
    
    options = [
        'metadata',
        'autoload',
        'auto_primarykey',
        'tablename',
        'shortnames',
        'order_by',
        'extension'
    ]
    
    def __init__(self, entity, *args, **kwargs):
        """
            arguments include:
            metadata:           Specify a custom MetaData
            autoload:           automatically load column definitions
                                from the existing database table
            tablename:          Specify a custom tablename
            shortnames:         Usually tablenames include the full
                                module-path to the entity, but lower-cased and
                                separated by underscores ("_"), eg.:
                                "project1_model_myentity", for an entity named
                                "MyEntity" in the module "project1.model".
                                If shortnames is True, the tablename will just
                                be the entity's classname lower-cased, 
                                ie. "myentity".
            auto_primarykey:    If given as string, it will represent the
                                auto-primary-key's column name
                                if bool(auto_primarykey) evaluates
                                
                                True: Allow auto-creation of a primary key,
                                      if there's no primary key defined for
                                      the corresponding entity
                                
                                False: Disallow auto-creation of a primary key
            order_by:           How to order select results. Either a string
                                or a list of strings, composed of the field
                                name, optionally lead by a minus (descending
                                order)
            extension:          Use one or more MapperExtensions
        """
        
        desc = entity._descriptor
        
        for i in UsingOptions.options:
            if kwargs.has_key(i):
                setattr(desc, i, kwargs[i])


using_options = Statement(UsingOptions)
