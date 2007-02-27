'''
Relationship statements for Elixir entities

=============
Relationships
=============

This module provides support for defining relationships between your Elixir 
entities.  Elixir supports the following types of relationships: belongs_to_,
has_one_, has_many_ and has_and_belongs_to_many_. 

The first argument to all those statements is the name of the relationship, the
second is the 'kind' of object you are relating to (it is usually given using
the ``of_kind`` keyword). 

Additionally, if you want a bidirectionnal relationship, you should define the
inverse relationship on the other entity explicitly (as opposed to how
SQLAlchemy's backrefs are defined). In non-ambiguous situations, Elixir will 
match relationships together automatically. If there are several relationships
of the same type between two entities, Elixir is not able to determine which 
relationship is the inverse of which, so you have to disambiguate the 
situation by giving the name of the inverse relationship in the ``inverse`` 
keyword argument.

Following these "common" arguments, any number of additional keyword arguments
can be specified for advanced behavior. The keyword arguments are passed on to 
the SQLAlchemy ``relation`` function. Please refer to the `SQLAlchemy relation 
function's documentation <http://www.sqlalchemy.org/docs/adv_datamapping.myt
#advdatamapping_properties_relationoptions>`_ for further detail about which 
keyword arguments are supported, but you should keep in mind, the following 
keyword arguments are taken care of by Elixir and should not be used: 
``uselist``, ``remote_side``, ``secondary``, ``primaryjoin`` and 
``secondaryjoin``.

.. _order_by:

Also, as for standard SQLAlchemy relations, the ``order_by`` keyword argument 
can be used to sort the results given by accessing a relation field (this only
makes sense for has_many and has_and_belongs_to_many relationships). The value
of that argument is different though: you can either use a string or a list of 
strings, each corresponding to the name of a field in the target entity. These
field names can optionally be prefixed by a minus (for descending order).

Here is a detailed explanation of each relation type:

`belongs_to`
------------

Describes the child's side of a parent-child relationship.  For example, 
a `Pet` object may belong to its owner, who is a `Person`.  This could be
expressed like so:

::

    class Pet(Entity):
        belongs_to('owner', of_kind='Person')

Behind the scene, assuming the primary key of the `Person` entity is 
an integer column named `id`, the ``belongs_to`` relationship will 
automatically add an integer column named `owner_id` to the entity, with a 
foreign key referencing the `id` column of the `Person` entity.

In addition to the keyword arguments inherited from SQLAlchemy's relation 
function, ``belongs_to`` relationships accept the following optional arguments
which will be directed to the created column:

+----------------------+------------------------------------------------------+
| Option Name          | Description                                          |
+======================+======================================================+
| ``colname``          | Specify a custom column name.                        |
+----------------------+------------------------------------------------------+
| ``nullable``         | True if this column should allow nulls. Defaults to  |
|                      | True unless this column is a primary key column.     |
+----------------------+------------------------------------------------------+
| ``column_kwargs``    | A dictionary holding any other keyword argument you  |
|                      | might want to pass to the Column.                    |
+----------------------+------------------------------------------------------+

The following optional arguments are also supported to customize the
ForeignKeyConstraint that is created:

+----------------------+------------------------------------------------------+
| Option Name          | Description                                          |
+======================+======================================================+
| ``use_alter``        | If True, SQLAlchemy will add the constraint in a     |
|                      | second SQL statement (as opposed to within the       |
|                      | create table statement). This permits to define      |
|                      | tables with a circular foreign key dependency        |
|                      | between them.                                        |
+----------------------+------------------------------------------------------+
| ``constraint_kwargs``| A dictionary holding any other keyword argument you  |
|                      | might want to pass to the Constraint.                |
+----------------------+------------------------------------------------------+

`has_one`
---------

Describes the parent's side of a parent-child relationship when there is only
one child.  For example, a `Car` object has one gear stick, which is 
represented as a `GearStick` object. This could be expressed like so:

::

    class Car(Entity):
        has_one('gear_stick', of_kind='GearStick', inverse='car')

    class GearStick(Entity):
        belongs_to('car', of_kind='Car')

Note that an ``has_one`` relationship **cannot exist** without a corresponding 
``belongs_to`` relationship in the other way. This is because the ``has_one``
relationship needs the foreign_key created by the ``belongs_to`` relationship.

`has_many`
----------

Describes the parent's side of a parent-child relationship when there can be
several children.  For example, a `Person` object has many children, each of
them being a `Person`. This could be expressed like so:

::

    class Person(Entity):
        belongs_to('parent', of_kind='Person')
        has_many('children', of_kind='Person')

Note that an ``has_many`` relationship **cannot exist** without a 
corresponding ``belongs_to`` relationship in the other way. This is because the
``has_many`` relationship needs the foreign key created by the ``belongs_to`` 
relationship.

`has_and_belongs_to_many`
-------------------------

Describes a relationship in which one kind of entity can be related to several
objects of the other kind but the objects of that other kind can be related to
several objects of the first kind.  For example, an `Article` can have several
tags, but the same `Tag` can be used on several articles.

::

    class Article(Entity):
        has_and_belongs_to_many('tags', of_kind='Tag')

    class Tag(Entity):
        has_and_belongs_to_many('articles', of_kind='Article')

Behind the scene, the ``has_and_belongs_to_many`` relationship will 
automatically create an intermediate table to host its data.

Note that you don't necessarily need to define the inverse relationship.  In
our example, even though we want tags to be usable on several articles, we 
might not be interested in which articles correspond to a particular tag.  In
that case, we could have omitted the `Tag` side of the relationship.

In addition to the order_by_ keyword argument, and the other keyword arguments
inherited from SQLAlchemy, ``has_and_belongs_to_many`` relationships accept an
optional ``tablename`` keyword argument, used to specify a custom name for the
intermediary table which will be created.

'''

from sqlalchemy         import relation, ForeignKeyConstraint, Column, \
                               Table, and_
from elixir.statements  import Statement
from elixir.fields      import Field
from elixir.entity      import EntityDescriptor

import sys


__all__ = ['belongs_to', 'has_one', 'has_many', 'has_and_belongs_to_many']

__pudge_all__ = []

class Relationship(object):
    '''
    Base class for relationships.
    '''
    
    def __init__(self, entity, name, *args, **kwargs):
        self.name = name
        self.of_kind = kwargs.pop('of_kind')
        self.inverse_name = kwargs.pop('inverse', None)
        
        self.entity = entity
        self._target = None
        
        self._inverse = None
        self.foreign_key = kwargs.pop('foreign_key', None)
        if self.foreign_key and not isinstance(self.foreign_key, list):
            self.foreign_key = [self.foreign_key]
        
        self.property = None # sqlalchemy property
        
        #TODO: unused for now
        self.args = args
        self.kwargs = kwargs
        
        self.entity._descriptor.relationships[self.name] = self
    
    def create_keys(self):
        '''
        Subclasses (ie. concrete relationships) may override this method to 
        create foreign keys.
        '''
    
    def create_tables(self):
        '''
        Subclasses (ie. concrete relationships) may override this method to 
        create secondary tables.
        '''
    
    def create_properties(self):
        '''
        Subclasses (ie. concrete relationships) may override this method to add 
        properties to the involved entities.
        '''
    
    def setup(self):
        '''
        Sets up the relationship, creates foreign keys and secondary tables.
        '''

        if not self.target:
            return False

        if self.property:
            return True

        self.create_keys()
        self.create_tables()
        self.create_properties()
        
        return True
    
    def target(self):
        if not self._target:
            path = self.of_kind.rsplit('.', 1)
            classname = path.pop()

            if path:
                # do we have a fully qualified entity name?
                module = sys.modules[path.pop()]
            else: 
                # if not, try the same module as the source
                module = self.entity._descriptor.module

            self._target = getattr(module, classname, None)
            if not self._target:
                # This is ugly but we need it because the class which is
                # currently being defined (we have to keep in mind we are in 
                # its metaclass code) is not yet available in the module
                # namespace, so the getattr above fails. And unfortunately,
                # this doesn't only happen for the owning entity of this
                # relation since we might be setting up a deferred relation.
                e = EntityDescriptor.current.entity
                if classname == e.__name__ or \
                        self.of_kind == e.__module__ +'.'+ e.__name__:
                    self._target = e
                else:
                    return None
        
        return self._target
    target = property(target)
    
    def inverse(self):
        if not self._inverse:
            if self.inverse_name:
                desc = self.target._descriptor
                # we use all_relationships so that relationships from parent
                # entities are included too
                inverse = desc.all_relationships.get(self.inverse_name, None)
                if inverse is None:
                    raise Exception(
                              "Couldn't find a relationship named '%s' in "
                              "entity '%s' or its parent entities." 
                              % (self.inverse_name, self.target.__name__)
                          )
                assert self.match_type_of(inverse)
            else:
                inverse = self.target._descriptor.get_inverse_relation(self)

            if inverse:
                self._inverse = inverse
                inverse._inverse = self
        
        return self._inverse
    inverse = property(inverse)
    
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
    '''
    
    '''
    
    def __init__(self, entity, name, *args, **kwargs):
        self.colname = kwargs.pop('colname', None)
        self.column_kwargs = kwargs.pop('column_kwargs', {})
        if 'required' in kwargs:
            self.column_kwargs['nullable'] = not kwargs.pop('required')

        self.constraint_kwargs = kwargs.pop('constraint_kwargs', {})
        if 'use_alter' in kwargs:
            self.contraint_kwargs['use_alter'] = kwargs.pop('use_alter')
        
        if self.colname and not isinstance(self.colname, list):
            self.colname = [self.colname]
        super(BelongsTo, self).__init__(entity, name, *args, **kwargs)
    
    def create_keys(self):
        '''
        Find all primary keys on the target and create foreign keys on the 
        source accordingly.
        '''
        
        source_desc = self.entity._descriptor
        target_desc = self.target._descriptor
        
        # convert strings to column instances
        if self.foreign_key:
            #FIXME: this will fail. Because if we specify a foreign_key
            # as argument, it will not create the necessary column
            self.foreign_key = [source_desc.fields[k].column
                                   for k in self.foreign_key 
                                       if isinstance(k, basestring)]
            return

        self.foreign_key = list()
        self.primaryjoin_clauses = list()

        if source_desc.autoload:
            if not self.colname:
                raise Exception(
                        "Entity '%s' is autoloaded but relation '%s' has no "
                        "column name specified. You should specify it by "
                        "using the colname keyword."
                        % (self.entity.__name__, self.name)
                      )

            #TODO: test if this works when colname is a list
            for colname in self.colname:
                for col in self.entity.table.columns:
                    if col.name == colname:
                        # We need to take the first foreign key, but 
                        # foreign_keys is an util.OrderedSet which doesn't 
                        # support indexation.
                        fk_iter = iter(col.foreign_keys)
                        fk = fk_iter.next()
                        self.primaryjoin_clauses.append(col == fk.column)

            if not self.primaryjoin_clauses:
                raise Exception("Column '%s' not found in table '%s'" 
                                % (self.colname, self.entity.table.name))
        else:
            fk_refcols = list()
            fk_colnames = list()

            if self.colname and \
               len(self.colname) != len(target_desc.primary_keys):
                raise Exception(
                        "The number of column names provided in the colname "
                        "keyword argument of the '%s' relationship of the "
                        "'%s' entity is not the same as the number of columns "
                        "of the primary key of '%s'."
                        % (self.name, self.entity.__name__, 
                           self.target.__name__)
                      )

            for key_num, key in enumerate(target_desc.primary_keys):
                pk_col = key.column

                if self.colname:
                    colname = self.colname[key_num]
                else:
                    colname = '%s_%s' % (self.name, pk_col.name)

                # we use a Field here instead of using a Column directly 
                # because of add_field 
                field = Field(pk_col.type, colname=colname, index=True, 
                              **self.column_kwargs)
                source_desc.add_field(field)

                self.foreign_key.append(field.column)

                # build the list of local columns which will be part of
                # the foreign key
                fk_colnames.append(colname)

                # build the list of columns the foreign key will point to
                fk_refcols.append("%s.%s" % (target_desc.entity.table.name,
                                             pk_col.name))

                # build up the primary join. This is needed when you have 
                # several belongs_to relations between two objects
                self.primaryjoin_clauses.append(field.column == pk_col)
            
            # In some databases (at lease MySQL) the constraint name needs to 
            # be unique for the whole database, instead of per table.
            fk_name = "%s_%s_fk" % (self.entity.table.name, self.name)
            source_desc.add_constraint(ForeignKeyConstraint(
                                            fk_colnames, fk_refcols,
                                            name=fk_name,
                                            **self.constraint_kwargs))
    
    def create_properties(self):
        kwargs = self.kwargs
        
        if self.entity.table is self.target.table:
            if self.entity._descriptor.autoload:
                cols = [col for col in self.target.table.primary_key.columns]
            else:
                cols = [k.column for k in self.target._descriptor.primary_keys]
            kwargs['remote_side'] = cols

        kwargs['primaryjoin'] = and_(*self.primaryjoin_clauses)
        kwargs['uselist'] = False
        
        self.property = relation(self.target, **kwargs)
        self.entity.mapper.add_property(self.name, self.property)


class HasOne(Relationship):
    uselist = False

    def create_keys(self):
        # make sure the inverse exists
        if self.inverse is None:
            raise Exception(
                      "Couldn't find any relationship in '%s' which "
                      "match as inverse of the '%s' relationship "
                      "defined in the '%s' entity. If you are using "
                      "inheritance you "
                      "might need to specify inverse relationships "
                      "manually by using the inverse keyword."
                      % (self.target.__name__, self.name,
                         self.entity.__name__)
                  )
        # make sure it is set up because it creates the foreign key we'll need
        self.inverse.setup()
    
    def create_properties(self):
        kwargs = self.kwargs
        
        #TODO: for now, we don't break any test if we remove those 2 lines.
        # So, we should either complete the selfref test to prove that they
        # are indeed useful, or remove them. It might be they are indeed
        # useless because of the primaryjoin, and that the remote_side is
        # already setup in the other way (belongs_to).
        if self.entity.table is self.target.table:
            kwargs['remote_side'] = self.inverse.foreign_key
        
        kwargs['primaryjoin'] = and_(*self.inverse.primaryjoin_clauses)
        kwargs['uselist'] = self.uselist
        
        self.property = relation(self.target, **kwargs)
        self.entity.mapper.add_property(self.name, self.property)


class HasMany(HasOne):
    uselist = True

    def create_properties(self):
        if 'order_by' in self.kwargs:
            self.kwargs['order_by'] = \
                self.target._descriptor.translate_order_by(
                    self.kwargs['order_by'])

        super(HasMany, self).create_properties()


class HasAndBelongsToMany(Relationship):
    def __init__(self, entity, name, *args, **kwargs):
        self.user_tablename = kwargs.pop('tablename', None)
        self.secondary_table = None
        super(HasAndBelongsToMany, self).__init__(entity, name, 
                                                  *args, **kwargs)

    def create_tables(self):
        if self.inverse:
            if self.inverse.secondary_table:
                self.secondary_table = self.inverse.secondary_table
                self.primaryjoin_clauses = self.inverse.secondaryjoin_clauses
                self.secondaryjoin_clauses = self.inverse.primaryjoin_clauses

        if not self.secondary_table:
            e1_desc = self.entity._descriptor
            e2_desc = self.target._descriptor
            
            if e1_desc.autoload:
                if not self.user_tablename:
                    raise Exception(
                        "Entity '%s' is autoloaded but relation '%s' has no "
                        "secondary table name specified. You should specify "
                        "it by using the tablename keyword."
                        % (self.entity.__name__, self.name)
                    )

            # We use the name of the relation for the first entity 
            # (instead of the name of its primary key), so that we can 
            # have two many-to-many relations between the same objects 
            # without having a table name collision. 
            source_part = "%s_%s" % (e1_desc.tablename, self.name)

            # And we use the name of the primary key for the second entity
            # when there is no inverse, so that a many-to-many relation 
            # can be defined without an inverse.
            if self.inverse:
                e2_name = self.inverse.name
            else:
                e2_name = '_'.join([key.column.name for key in
                                    e2_desc.primary_keys])
            target_part = "%s_%s" % (e2_desc.tablename, e2_name)
            
            if self.user_tablename:
                tablename = self.user_tablename
            else:
                # we need to keep the table name consistent (independant of 
                # whether this relation or its inverse is setup first)
                if self.inverse and e1_desc.tablename < e2_desc.tablename:
                    tablename = "%s__%s" % (target_part, source_part)
                else:
                    tablename = "%s__%s" % (source_part, target_part)

            # In some databases (at lease MySQL) the constraint names need 
            # to be unique for the whole database, instead of per table.
            source_fk_name = "%s_fk" % source_part
            if self.inverse:
                target_fk_name = "%s_fk" % target_part
            else:
                target_fk_name = "%s_inverse_fk" % source_part

            columns = list()
            constraints = list()

            self.primaryjoin_clauses = list()
            self.secondaryjoin_clauses = list()

            for num, desc, join_name, fk_name in (
                    ('1', e1_desc, 'primary', source_fk_name), 
                    ('2', e2_desc, 'secondary', target_fk_name)):
                fk_colnames = list()
                fk_refcols = list()
            
                for key in desc.primary_keys:
                    pk_col = key.column
                    
                    colname = '%s_%s' % (desc.tablename, pk_col.name)

                    # In case we have a many-to-many self-reference, we need
                    # to tweak the names of the columns so that we don't end 
                    # up with twice the same column name.
                    if self.entity is self.target:
                        colname += num

                    col = Column(colname, pk_col.type)
                    columns.append(col)

                    # build the list of local columns which will be part of
                    # the foreign key
                    fk_colnames.append(colname)

                    # build the list of columns the foreign key will point to
                    fk_refcols.append(desc.tablename + '.' + pk_col.name)

                    # build join clauses
                    join_list = getattr(self, join_name+'join_clauses')
                    join_list.append(col == pk_col)
                
                constraints.append(
                    ForeignKeyConstraint(fk_colnames, fk_refcols,
                                         name=fk_name))


            args = columns + constraints
            
            self.secondary_table = Table(tablename, e1_desc.metadata, *args)
    
    def create_properties(self):
        kwargs = self.kwargs

        if self.target is self.entity:
            kwargs['primaryjoin'] = and_(*self.primaryjoin_clauses)
            kwargs['secondaryjoin'] = and_(*self.secondaryjoin_clauses)

        if 'order_by' in kwargs:
            kwargs['order_by'] = \
                self.target._descriptor.translate_order_by(kwargs['order_by'])

        self.property = relation(self.target, secondary=self.secondary_table,
                                 uselist=True, **kwargs)
        self.entity.mapper.add_property(self.name, self.property)

    def is_inverse(self, other):
        return super(HasAndBelongsToMany, self).is_inverse(other) and \
               (self.user_tablename == other.user_tablename or 
                (not self.user_tablename and not other.user_tablename))


belongs_to              = Statement(BelongsTo)
has_one                 = Statement(HasOne)
has_many                = Statement(HasMany)
has_and_belongs_to_many = Statement(HasAndBelongsToMany)
