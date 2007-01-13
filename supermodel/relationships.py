import sys
from sqlalchemy import relation, ForeignKeyConstraint, Column, Table, \
                       backref, class_mapper
from sqlalchemy.util import to_set
from supermodel.statements import Statement
from supermodel.fields import Field
from supermodel.entity import EntityDescriptor


class Relationship(object):
    """
        Base class for relationships
    """
    
    def __init__(self, entity, *args, **kwargs):
        self.name = args[0]
        self.of_kind = kwargs.pop('of_kind')
        self.inverse_name = kwargs.pop('as', None)
        
        self.entity = entity
        self._target = None
        
        self.initialized = False
        self.secondary = None
        self._inverse = None
        self.foreign_key = None
        
        self.foreign_key = kwargs.pop('foreign_key', None)
        if self.foreign_key and not isinstance(self.foreign_key, list):
            self.foreign_key = [self.foreign_key]
        
        self.property = None # sqlalchemy property
        
        self.args = args
        self.kwargs = kwargs
        
        self.entity._descriptor.relationships[self.name] = self
    
    def create_keys(self):
        """
            Subclasses (ie. concrete relationships) may
            override this method to create foreign keys
        """
        pass
    
    def create_tables(self):
        """
            Subclasses (ie. concrete relationships) may
            override this method to create secondary tables
        """
        pass
    
    def create_properties(self):
        """
            Subclasses (ie. concrete relationships) may
            override this method to add properties to the
            involved entities
        """
        pass
    
    def setup(self):
        """
            Sets up the relationship, creates foreign keys
            and secondary tables
        """
        
        if not self.target:
            return False
        
        self.create_keys()
        self.create_tables()
        self.create_properties()
        
        return True
    
    @property
    def target(self):
        if not self._target:
            path = self.of_kind.rsplit('.', 1)
            classname = path.pop()

            # full qualified entity name?
            if path:
                module = sys.modules[path.pop()]
            else: # if not, try the same module as the source
                module = self.entity._descriptor.module
            
            try:
                self._target = getattr(module, classname)
            except AttributeError:
                e = EntityDescriptor.current.entity
                if classname == e.__name__ or \
                        self.of_kind == e.__module__ +'.'+ e.__name__:
                    self._target = e
                else:
                    return None
        
        return self._target
    
    def get_inverse(self):
        if not self._inverse:
            if not self.inverse_name:
                # TODO: automatically figure out inverses in non-ambiguous
                #       situations
                return None
        
            inverse = self.target._descriptor.relationships[self.inverse_name]
        
            if isinstance(self, BelongsTo):
                assert isinstance(inverse, HasOne) or \
                            isinstance(inverse, HasMany)
            elif isinstance(self, HasOne) or isinstance(self, HasMany):
                assert isinstance(inverse, BelongsTo)
            elif isinstance(self, HasAndBelongsToMany):
                assert isinstance(inverse, HasAndBelongsToMany)
        
            self._inverse = inverse
            inverse.inverse = self
        
        return self._inverse
    
    def set_inverse(self, inverse):
        self._inverse = inverse
    
    inverse = property(get_inverse, set_inverse)
        

class BelongsTo(Relationship):
    def create_keys(self):
        """
            Find all primary keys on the target and accordingly create
            foreign keys on the source
        """
        source_desc = self.entity._descriptor
        target_desc = self.target._descriptor
        
        refcolumns = []
        columns = []
        
        if self.foreign_key:
            self.foreign_key = [source_desc.fields[k]
                                    for k in self.foreign_key 
                                        if isinstance(k, basestring)]
            return
        
        self.foreign_key = []
        for key in target_desc.primary_keys:
            keycol = key.column
            refcol = target_desc.tablename + '.' + keycol.name
            field = Field(keycol.type, colname=self.name + '_' + keycol.name,
                          index=True)
            
            self.foreign_key.append(field)
            refcolumns.append(refcol)
            columns.append(field.column.name)
            source_desc.add_field(field)
        
        # TODO: better constraint-naming?
        source_desc.add_constraint(ForeignKeyConstraint(
                                        columns, refcolumns,
                                        name=self.name +'_fk',
                                        use_alter=True))
    
    def create_properties(self):
        kwargs = dict()
        
        if self.entity is self.target:
            cols = [k.column for k in self.target._descriptor.primary_keys]
            kwargs['remote_side'] = cols
        
        if self.inverse:
            kwargs['backref'] = self.inverse.name
        
        kwargs['uselist'] = False
        
        self.property = relation(self.target, **kwargs)
        self.entity.mapper.add_property(self.name, self.property)


class HasOne(Relationship):
    def create_keys(self):
        # make sure the inverse is set up because it creates the
        # foreign key we'll need
        self.inverse.setup()
    
    def create_properties(self, uselist=False):
        kwargs = dict()
        
        if self.entity is self.target:
            kwargs['post_update'] = True
            kwargs['remote_side'] = [f.column
                                        for f in self.inverse.foreign_key]
        
        kwargs['backref'] = self.inverse.name
        kwargs['post_update'] = True
        kwargs['uselist'] = uselist
        
        self.property = relation(self.target, **kwargs)
        self.entity.mapper.add_property(self.name, self.property)


class HasMany(HasOne):
    def create_properties(self):
        super(HasMany, self).create_properties(uselist=True)


class HasAndBelongsToMany(Relationship):
    def create_tables(self):
        t1_desc = self.entity._descriptor
        t2_desc = self.target._descriptor
        
        columns = list()
        constraints = list()
        
        if self.inverse:
            if isinstance(self.inverse, basestring):
                self.inverse = t2_desc.relationships[self.inverse]
            
            if self.inverse.secondary:
                self.secondary = self.inverse.secondary

        if not self.secondary:
            for t in [t1_desc, t2_desc]:
                cols = list()
                refcols = list()
            
                for key in t.primary_keys:
                    keycol = key.column
                    refcol = t.tablename + '.' + keycol.name
                    col = Column(t.tablename +'_' + keycol.name, keycol.type)
                    cols.append(col.name)
                    columns.append(col)
                    refcols.append(refcol)
                
                # TODO: better constraint-naming?
                constraints.append(
                    ForeignKeyConstraint(cols, refcols,
                                    name=t.tablename + '_fk', use_alter=True))
        
            tablename = "%s_%s__%s_%s" % (t1_desc.tablename, self.name,
                                          t2_desc.tablename,
                                          self.inverse.name)

            args = columns + constraints
            self.secondary = Table(tablename, t1_desc.metadata, *args)
    
    def create_properties(self):
        m = self.entity.mapper
        m.add_property(self.name,
                       relation(self.target, secondary=self.secondary,
                                uselist=True, post_update=True))


belongs_to = Statement(BelongsTo)
has_one = Statement(HasOne)
has_many = Statement(HasMany)
has_and_belongs_to_many = Statement(HasAndBelongsToMany)

