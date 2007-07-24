from elixir import *

class B(Entity):
    has_field('name', String(30))
    has_many('a', of_kind='tests.a.A')

