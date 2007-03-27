========
Examples
========

---------------
The Video Store
---------------

The Elixir source distribution includes a sample web application that uses the
`TurboGears <http://www.turbogears.org/>`_ web application framework. The
application builds upon the tutorial's Movie model to create a simple store for
buying movies.

The Video Store sample application also includes an example of how to use Elixir
with the TurboGears "identity" framework for security and authorization.  If 
you are planning to use Elixir with your TurboGears application, and need to
support authorization using identity, you can use this model as a basis:

::

    from turbogears.database    import metadata, session
    from elixir                 import Unicode, DateTime, String, Integer
    from elixir                 import Entity, has_field, using_options
    from elixir                 import has_many, belongs_to, has_and_belongs_to_many
    from sqlalchemy             import ForeignKey
    from datetime               import datetime

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
        belongs_to('user', of_kind='User', colname='user_id', use_alter=True)
        using_options(tablename='visit_identity')

    class Group(Entity):
        has_field('group_id', Integer, primary_key=True)
        has_field('group_name', Unicode(16), unique=True)
        has_field('display_name', Unicode(255))
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


More Elixir examples are coming soon, and we would appreciate any additional
sample applications that you could provide to illustrate more complex mappings.

