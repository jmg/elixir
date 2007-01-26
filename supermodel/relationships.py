import sys
from sqlalchemy import relation, ForeignKeyConstraint, Column, Table, \
                       backref, class_mapper, and_
from sqlalchemy.util import to_set
from supermodel.statements import Statement
from supermodel.fields import Field
from supermodel.entity import EntityDescriptor


class Relationship(object):
    """
        Base class for relationships
    """
    
    def __init__(self, entity, name, *args, **kwargs):
        self.name = name
        self.of_kind = kwargs.pop('of_kind')
        self.inverse_name = kwargs.pop('inverse', None)
        
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
        
        #CHECKME: is this useful?
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
            # if not, try the same module as the source
            else: 
                module = self.entity._descriptor.module
            
            try:
                self._target = getattr(module, classname)
            except AttributeError:
                #CHECKME: this is really ugly. Do we really need that?
                e = EntityDescriptor.current.entity
                if classname == e.__name__ or \
                        self.of_kind == e.__module__ +'.'+ e.__name__:
                    self._target = e
                else:
                    return None
        
        return self._target
    
    @property
    def inverse(self):
        #TODO: we should use a different value for when an inverse was searched
        # for but none was found than when it hasn't been searched for yet so
        # that we don't do the whole search again
        if not self._inverse:
            if self.inverse_name:
                desc = self.target._descriptor
                inverse = desc.relationships[self.inverse_name]
                assert self.match_type_of(inverse)
            else:
                inverse = self.target._descriptor.get_inverse_relation(self)
        
            if inverse:
                self._inverse = inverse
                inverse._inverse = self
        
        return self._inverse
    
    def match_type_of(self, other):
        t1, t2 = type(self), type(other)
    
        if t1 is HasAndBelongsToMany:
            return t1 is t2
        elif t1 in (HasOne, HasMany):
            return t2 is BelongsTo
        elif t1 is BelongsTo:
            return t2 in (HasMany, HasOne)
        else:
            return False

    def is_inverse(self, other):
        return other is not self and \
               self.match_type_of(other) and \
               self.entity == other.target and \
               other.entity == self.target and \
               (self.inverse_name == other.name or not self.inverse_name) and \
               (other.inverse_name == self.name or not other.inverse_name)

class BelongsTo(Relationship):
    def create_keys(self):
        """
            Find all primary keys on the target and create
            foreign keys on the source accordingly 
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
        self.primaryjoin_clauses = list()

        for key in target_desc.primary_keys:
            pk_col = key.column
            refcol = target_desc.tablename + '.' + pk_col.name
            #CHECKME: why do we use a Field here instead of directly using a 
            # Column
            field = Field(pk_col.type, colname=self.name + '_' + pk_col.name,
                          index=True)
            
            self.foreign_key.append(field)
            refcolumns.append(refcol)
            columns.append(field.column.name)
            source_desc.add_field(field)

            # build up the primary join. This is needed when you have several
            # belongs_to relations between two objects
            self.primaryjoin_clauses.append(field.column == pk_col)
        
        # TODO: better constraint-naming?
        source_desc.add_constraint(ForeignKeyConstraint(
                                        columns, refcolumns,
                                        name=self.name +'_fk',
                                        use_alter=True))
    
    def create_properties(self):
        kwargs = self.kwargs
        
        if self.entity is self.target:
            cols = [k.column for k in self.target._descriptor.primary_keys]
            kwargs['remote_side'] = cols

        kwargs['primaryjoin'] = and_(*self.primaryjoin_clauses)
        
        #CHECKME: is this of any use?
#        if self.inverse:
#            kwargs['backref'] = self.inverse.name
        
        kwargs['uselist'] = False
        
        self.property = relation(self.target, **kwargs)
        self.entity.mapper.add_property(self.name, self.property)


class HasOne(Relationship):
    uselist = False

    def create_keys(self):
        # make sure the inverse is set up because it creates the
        # foreign key we'll need
        self.inverse.setup()
    
    def create_properties(self):
        kwargs = self.kwargs
        
        if self.entity is self.target:
            kwargs['post_update'] = True
            kwargs['remote_side'] = [f.column
                                        for f in self.inverse.foreign_key]
        
        kwargs['primaryjoin'] = and_(*self.inverse.primaryjoin_clauses)
        #CHECKME: is this of any use?
#        kwargs['backref'] = self.inverse.name
        #FIXME: this is *BAD*
        kwargs['post_update'] = True
        kwargs['uselist'] = self.uselist
        
        self.property = relation(self.target, **kwargs)
        self.entity.mapper.add_property(self.name, self.property)


class HasMany(HasOne):
    uselist = True


class HasAndBelongsToMany(Relationship):
    def create_tables(self):
        if self.inverse:
            if self.inverse.secondary:
                self.secondary = self.inverse.secondary
                self.primaryjoin_clauses = self.inverse.secondaryjoin_clauses
                self.secondaryjoin_clauses = self.inverse.primaryjoin_clauses

        if not self.secondary:
            e1_desc = self.entity._descriptor
            e2_desc = self.target._descriptor
            
            columns = list()
            constraints = list()

            #CHECKME: it might be better to only compute joins when we have a
            # self reference. The thing is I'm unsure it's only usefull in that
            # case. I think it's also usefull when you have several many-to-many
            # relations between the same objects. I'll have to test that...
            # no it's not since the tables are different. It would only if the
            # tables where the same, but I'm not sure if it has some sense to be
            # in that situation.
#            if self.entity is self.target:
#                print "many2many self ref detected"
            self.primaryjoin_clauses = list()
            self.secondaryjoin_clauses = list()

            for desc, join_name in ((e1_desc, 'primary'), 
                                    (e2_desc, 'secondary')):
                fk_colnames = list()
                fk_refcols = list()
            
                for key in desc.primary_keys:
                    pk_col = key.column
                    
                    colname = '%s_%s' % (desc.tablename, pk_col.name)

                    # In case we have many-to-many self-reference, we need
                    # to tweak the names of the columns corresponding to one 
                    # of the entities so that we don't end up with twice the 
                    # same column name.

                    # If we are in that case, we test whether we are in the 
                    # second iteration or not
                    if self.entity is self.target and \
                       (join_name == 'secondary'):
                        colname += '2'

                    col = Column(colname, pk_col.type)
                    columns.append(col)

                    # build the list of columns which will be part of the 
                    # foreign key
                    fk_colnames.append(colname)

                    # build the list of columns the foreign key will point to
                    fk_refcols.append(desc.tablename + '.' + pk_col.name)

                    # build join clauses
                    join_list = getattr(self, join_name+'join_clauses')
                    join_list.append(col == pk_col)
                
                # TODO: better constraint-naming?
                #FIXME: using use_alter systematically is no good
                constraints.append(
                    ForeignKeyConstraint(fk_colnames, fk_refcols,
                                         name=desc.tablename + '_fk', 
                                         use_alter=True))
        
            # In the table name code below, we use the name of the relation
            # for the first entity (instead of the name of its primary key), 
            # so that we can have two many-to-many relations between the same
            # objects without having a table name collision. On the other hand,
            # we use the name of the primary key for the second entity 
            # (instead of the inverse relation's name) so that a many-to-many
            # relation can be defined without inverse.
            e2_pk_name = '_'.join([key.column.name for key in
                                   e2_desc.primary_keys])
            tablename = "%s_%s__%s_%s" % (e1_desc.tablename, self.name,
                                          e2_desc.tablename, e2_pk_name)

            args = columns + constraints
            self.secondary = Table(tablename, e1_desc.metadata, *args)
    
    def create_properties(self):
        kwargs = self.kwargs

        if self.target is self.entity:
            kwargs['primaryjoin'] = and_(*self.primaryjoin_clauses)
            kwargs['secondaryjoin'] = and_(*self.secondaryjoin_clauses)

        m = self.entity.mapper
        #FIXME: using post_update systematically is *really* not good
        m.add_property(self.name,
                       relation(self.target, secondary=self.secondary,
                                uselist=True, post_update=True, **kwargs))


belongs_to = Statement(BelongsTo)
has_one = Statement(HasOne)
has_many = Statement(HasMany)
has_and_belongs_to_many = Statement(HasAndBelongsToMany)

