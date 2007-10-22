from elixir import *

class B(Entity):
    name = Field(String(30))
    as_ = OneToMany('tests.a.A')

