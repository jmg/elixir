from elixir import *

class B(Entity):
    has_field('name', String(30))
    has_many('as_', of_kind='tests.a.A')

