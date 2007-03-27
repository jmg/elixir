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
| ``required``         | Specify whether or not this field can be set to None |
|                      | (left without a value). Defaults to ``False``,       |
|                      | unless the field is a primary key.                   |
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
| ``ondelete``         | Value for the foreign key constraint ondelete clause.|
|                      | May be one of: ``cascade``, ``restrict``,            |
|                      | ``set null``, or ``set default``.                    |
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

If the entity containg your ``has_and_belongs_to_many`` relationship is 
autoloaded, you **must** specify at least one of either the ``remote_side`` or
``local_side`` argument.

In addition to the order_by_ keyword argument, and the other keyword arguments
inherited from SQLAlchemy, ``has_and_belongs_to_many`` relationships accept 
the following optional (keyword) arguments:

+--------------------+--------------------------------------------------------+
| Option Name        | Description                                            |
+====================+========================================================+
| ``tablename``      | Specify a custom name for the intermediary table. This |
|                    | can be used both when the tables needs to be created   |
|                    | and when the table is autoloaded/reflected from the    |
|                    | database.                                              |
+--------------------+--------------------------------------------------------+
| ``remote_side``    | A column name or list of column names specifying       |
|                    | which column(s) in the intermediary table are used     |
|                    | for the "remote" part of a self-referential            |
|                    | relationship. This argument has an effect only when    |
|                    | your entities are autoloaded.                          |
+--------------------+--------------------------------------------------------+
| ``local_side``     | A column name or list of column names specifying       |
|                    | which column(s) in the intermediary table are used     |
|                    | for the "local" part of a self-referential             |
|                    | relationship. This argument has an effect only when    |
|                    | your entities are autoloaded.                          |
+--------------------+--------------------------------------------------------+

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
        self.entity = entity
        self.name = name
        self.of_kind = kwargs.pop('of_kind')
        self.inverse_name = kwargs.pop('inverse', None)
        
        self._target = None
        self._inverse = None
        
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
                              % (self.inverse_name, self.target.__name__))
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
        self.colname = kwargs.pop('colname', [])
        if self.colname and not isinstance(self.colname, list):
            self.colname = [self.colname]

        self.column_kwargs = kwargs.pop('column_kwargs', {})
        if 'required' in kwargs:
            self.column_kwargs['nullable'] = not kwargs.pop('required')

        self.constraint_kwargs = kwargs.pop('constraint_kwargs', {})
        if 'use_alter' in kwargs:
            self.constraint_kwargs['use_alter'] = kwargs.pop('use_alter')
        
        if 'ondelete' in kwargs:
            self.constraint_kwargs['ondelete'] = kwargs.pop('ondelete')
        
        self.foreign_key = list()
        self.primaryjoin_clauses = list()
        super(BelongsTo, self).__init__(entity, name, *args, **kwargs)
    
    def create_keys(self):
        '''
        Find all primary keys on the target and create foreign keys on the 
        source accordingly.
        '''

        source_desc = self.entity._descriptor
        target_desc = self.target._descriptor

        if source_desc.autoload:
            #TODO: test if this works when colname is a list
            if self.colname:
                self.primaryjoin_clauses = \
                    _build_join_clauses(self.entity.table, 
                                        self.colname, None, 
                                        self.target.table)[0]
                if not self.primaryjoin_clauses:
                    raise Exception(
                        "Couldn't find a foreign key constraint in table "
                        "'%s' using the following columns: %s."
                        % (self.entity.table.name, ', '.join(self.colname)))
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
                           self.target.__name__))

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

                # build the list of local columns which will be part of
                # the foreign key
                self.foreign_key.append(field.column)

                # store the names of those columns
                fk_colnames.append(colname)

                # build the list of columns the foreign key will point to
                fk_refcols.append("%s.%s" % (target_desc.entity.table.name,
                                             pk_col.name))

                # build up the primary join. This is needed when you have 
                # several belongs_to relations between two objects
                self.primaryjoin_clauses.append(field.column == pk_col)
            
            # In some databases (at lease MySQL) the constraint name needs to 
            # be unique for the whole database, instead of per table.
            fk_name = "%s_%s_fk" % (self.entity.table.name, 
                                    '_'.join(fk_colnames))
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

        if self.primaryjoin_clauses:
            kwargs['primaryjoin'] = and_(*self.primaryjoin_clauses)
        kwargs['uselist'] = False
        
        self.property = relation(self.target, **kwargs)
        self.entity.mapper.add_property(self.name, self.property)


class HasOne(Relationship):
    uselist = False

    def create_keys(self):
        # make sure an inverse relationship exists
        if self.inverse is None:
            raise Exception(
                      "Couldn't find any relationship in '%s' which "
                      "match as inverse of the '%s' relationship "
                      "defined in the '%s' entity. If you are using "
                      "inheritance you "
                      "might need to specify inverse relationships "
                      "manually by using the inverse keyword."
                      % (self.target.__name__, self.name,
                         self.entity.__name__))
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
            #FIXME: IF this code is of any use, it will probably break for
            # autoloaded tables
            kwargs['remote_side'] = self.inverse.foreign_key
        
        if self.inverse.primaryjoin_clauses:
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
        self.local_side = kwargs.pop('local_side', [])
        if self.local_side and not isinstance(self.local_side, list):
            self.local_side = [self.local_side]
        self.remote_side = kwargs.pop('remote_side', [])
        if self.remote_side and not isinstance(self.remote_side, list):
            self.remote_side = [self.remote_side]
        self.secondary_table = None
        self.primaryjoin_clauses = list()
        self.secondaryjoin_clauses = list()
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
           
            # First, we compute the name of the table. Note that some of the 
            # intermediary variables are reused later for the constraint 
            # names.
            
            # We use the name of the relation for the first entity 
            # (instead of the name of its primary key), so that we can 
            # have two many-to-many relations between the same objects 
            # without having a table name collision. 
            source_part = "%s_%s" % (e1_desc.tablename, self.name)

            # And we use only the name of the table of the second entity
            # when there is no inverse, so that a many-to-many relation 
            # can be defined without an inverse.
            if self.inverse:
                target_part = "%s_%s" % (e2_desc.tablename, self.inverse.name)
            else:
                target_part = e2_desc.tablename
            
            if self.user_tablename:
                tablename = self.user_tablename
            else:
                # We need to keep the table name consistent (independant of 
                # whether this relation or its inverse is setup first).
                if self.inverse and e1_desc.tablename < e2_desc.tablename:
                    tablename = "%s__%s" % (target_part, source_part)
                else:
                    tablename = "%s__%s" % (source_part, target_part)

            if e1_desc.autoload:
                self._reflect_table(tablename)
            else:
                # We pre-compute the names of the foreign key constraints 
                # pointing to the source (local) entity's table and to the 
                # target's table

                # In some databases (at lease MySQL) the constraint names need 
                # to be unique for the whole database, instead of per table.
                source_fk_name = "%s_fk" % source_part
                if self.inverse:
                    target_fk_name = "%s_fk" % target_part
                else:
                    target_fk_name = "%s_inverse_fk" % source_part

                columns = list()
                constraints = list()

                joins = (self.primaryjoin_clauses, self.secondaryjoin_clauses)
                for num, desc, fk_name in ((0, e1_desc, source_fk_name), 
                                           (1, e2_desc, target_fk_name)):
                    fk_colnames = list()
                    fk_refcols = list()
                
                    for key in desc.primary_keys:
                        pk_col = key.column
                        
                        colname = '%s_%s' % (desc.tablename, pk_col.name)

                        # In case we have a many-to-many self-reference, we 
                        # need to tweak the names of the columns so that we 
                        # don't end up with twice the same column name.
                        if self.entity is self.target:
                            colname += str(num + 1)

                        col = Column(colname, pk_col.type)
                        columns.append(col)

                        # Build the list of local columns which will be part 
                        # of the foreign key.
                        fk_colnames.append(colname)

                        # Build the list of columns the foreign key will point
                        # to.
                        fk_refcols.append(desc.tablename + '.' + pk_col.name)

                        # Build join clauses (in case we have a self-ref)
                        if self.entity is self.target:
                            joins[num].append(col == pk_col)
                    
                    constraints.append(
                        ForeignKeyConstraint(fk_colnames, fk_refcols,
                                             name=fk_name))

                args = columns + constraints
                
                self.secondary_table = Table(tablename, e1_desc.metadata, 
                                             *args)

    def _reflect_table(self, tablename):
        if not self.target._descriptor.autoload:
            raise Exception(
                "Entity '%s' is autoloaded and its '%s' "
                "has_and_belongs_to_many relationship points to "
                "the '%s' entity which is not autoloaded"
                % (self.entity.__name__, self.name,
                   self.target.__name__))
                
        self.secondary_table = Table(tablename, 
                                     self.entity._descriptor.metadata,
                                     autoload=True)

        # In the case we have a self-reference, we need to build join clauses
        if self.entity is self.target:
            #CHECKME: maybe we should try even harder by checking if that 
            # information was defined on the inverse relationship)
            if not self.local_side and not self.remote_side:
                raise Exception(
                    "Self-referential has_and_belongs_to_many "
                    "relationships in autoloaded entities need to have at "
                    "least one of either 'local_side' or 'remote_side' "
                    "argument specified. The '%s' relationship in the '%s' "
                    "entity doesn't have either."
                    % (self.name, self.entity.__name__))

            self.primaryjoin_clauses, self.secondaryjoin_clauses = \
                _build_join_clauses(self.secondary_table, 
                                    self.local_side, self.remote_side, 
                                    self.entity.table)

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


def _build_join_clauses(local_table, local_cols1, local_cols2, target_table):
    primary_join, secondary_join = [], []
    cols1 = local_cols1[:]
    cols1.sort()
    cols1 = tuple(cols1)

    if local_cols2 is not None:
        cols2 = local_cols2[:]
        cols2.sort()
        cols2 = tuple(cols2)
    else:
        cols2 = None
    constraint_map = {}
    for constraint in local_table.constraints:
        if isinstance(constraint, ForeignKeyConstraint):
            use_constraint = False
            fk_colnames = []
            for fk in constraint.elements:
                fk_colnames.append(fk.parent.name)
                if fk.references(target_table):
                    use_constraint = True
            if use_constraint:
                fk_colnames.sort()
                constraint_map[tuple(fk_colnames)] = constraint

    # Either the fk column names match explicitely with the columns given for
    # one of the joins (primary or secondary), or we assume the current
    # columns match because the columns for this join were not given and we
    # know the other join is either not used (is None) or has an explicit 
    # match.
    for cols, constraint in constraint_map.iteritems():
        if cols == cols1 or (cols != cols2 and 
                             not cols1 and (cols2 in constraint_map or
                                            cols2 is None)):
            join = primary_join
        elif cols == cols2 or (cols2 == () and cols1 in constraint_map):
            join = secondary_join
        else:
            continue
        for fk in constraint.elements:
            join.append(fk.parent == fk.column)
    return primary_join, secondary_join


belongs_to = Statement(BelongsTo)
has_one = Statement(HasOne)
has_many = Statement(HasMany)
has_and_belongs_to_many = Statement(HasAndBelongsToMany)
