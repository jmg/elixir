from turbogears.database    import metadata, session
from elixir                 import Unicode, DateTime, String, Integer
from elixir                 import Entity, has_field, using_options
from elixir                 import has_many, belongs_to, has_and_belongs_to_many
from sqlalchemy             import ForeignKey
from datetime               import datetime


#
# application model
#

class Director(Entity):
    has_field('name', Unicode(60))
    has_many('movies', of_kind='Movie', inverse='director')
    using_options(tablename='directors')


class Movie(Entity):
    has_field('title', Unicode(60))
    has_field('description', Unicode(512))
    has_field('releasedate', DateTime)
    belongs_to('director', of_kind='Director', inverse='movies')
    has_and_belongs_to_many('actors', of_kind='Actor', inverse='movies', tablename='movie_casting')
    using_options(tablename='movies')


class Actor(Entity):
    has_field('name', Unicode(60))
    has_and_belongs_to_many('movies', of_kind='Movie', inverse='actors', tablename='movie_casting')
    using_options(tablename='actors')
   

#
# identity model
# 

class Visit(Entity):
    has_field('visit_key', String(40), primary_key=True)
    has_field('created', DateTime, nullable=False, default=datetime.now)
    has_field('expiry', DateTime)
    using_options(tablename='visit')
    
    @classmethod
    def lookup_visit(cls, visit_key):
        return Visit.get(visit_key)

class VisitIdentity(Entity):
    has_field('visit_key', String(40), primary_key=True)
    has_field('user_id', Integer, ForeignKey('tg_user.user_id', name='user_id_fk', use_alter=True), index=True)
    using_options(tablename='visit_identity')

class Group(Entity):
    has_field('group_id', Integer, primary_key=True)
    has_field('group_name', Unicode(16), unique=True)
    has_field('display_name', Unicode(255)),
    has_field('created', DateTime, default=datetime.now)
    has_and_belongs_to_many('users', of_kind='User', inverse='groups')
    has_and_belongs_to_many('permissions', of_kind='Permission', inverse='groups')
    using_options(tablename='tg_group')

class User(Entity):
    has_field('user_id', Integer, primary_key=True)
    has_field('user_name', Unicode(16), unique=True)
    has_field('email_address', Unicode(255), unique=True)
    has_field('display_name', Unicode(255))
    has_field('password', Unicode(40))
    has_field('created', DateTime, default=datetime.now)
    has_and_belongs_to_many('groups', of_kind='Group', inverse='users')
    using_options(tablename='tg_user')
    
    @property
    def permissions(self):
        perms = set()
        for g in self.groups:
            perms = perms | set(g.permissions)
        return perms

class Permission(Entity):
    has_field('permission_id', Integer, primary_key=True)
    has_field('permission_name', Unicode(16), unique=True)
    has_field('description', Unicode(255))
    has_and_belongs_to_many('groups', of_kind='Group', inverse='permissions')
    using_options(tablename='permission')
