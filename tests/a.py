from elixir import *

class A(Entity):
    has_field('name', String(30))
    belongs_to('b', of_kind='tests.b.B')

