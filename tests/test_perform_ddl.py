from elixir import *
from elixir.ext.perform_ddl import perform_ddl

def setup():
    metadata.bind = "sqlite:///"

class TestPerformDDL(object):
    def teardown(self):
        cleanup_all(True)

    def test_one(self):
        class Movie(Entity):
            title = Field(Unicode(30), primary_key=True)
            year = Field(Integer)

            perform_ddl('after-create',
                        "insert into %(fullname)s values ('Alien', 1979)")

        setup_all(True)
        assert Movie.query.count() == 1

    def test_several(self):
        class Movie(Entity):
            title = Field(Unicode(30), primary_key=True)
            year = Field(Integer)

            perform_ddl('after-create',
                        ["insert into %(fullname)s values ('Alien', 1979)",
                         "insert into %(fullname)s " +
                            "values ('Star Wars', 1977)"])
            perform_ddl('after-create',
                        "insert into %(fullname)s (year, title) " +
                        "values (1982, 'Blade Runner')")

        setup_all(True)
        assert Movie.query.count() == 3
