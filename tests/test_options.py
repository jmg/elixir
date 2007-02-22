"""
    test options
"""

from sqlalchemy import create_engine, UniqueConstraint 
from sqlalchemy.exceptions import SQLError
from elixir     import *

#TODO: complete this test. 

# The order_by option is already tested in test_order_by.py

class Record(Entity):
    with_fields(
        title = Field(Unicode(30)),
        artist = Field(Unicode(30)),
        year = Field(Integer)
    )
    
    using_options(tablename="records")

class TestOptions(object):
    def setup(self):
        engine = create_engine('sqlite:///')
        metadata.connect(engine)
        create_all()
    
    def teardown(self):
        cleanup_all()
    
class TestTableOptions(object):
    def setup(self):
        global Person

        class Person(Entity):
            has_field('firstname', Unicode(30))
            has_field('surname', Unicode(30))

            using_table_options(UniqueConstraint('firstname', 'surname'))

        engine = create_engine('sqlite:///')
        metadata.connect(engine)
        create_all()

    def test_table_options(self):
        homer = Person(firstname="Homer", surname='Simpson')
        bart = Person(firstname="Bart", surname='Simpson')

        objectstore.flush()

        homer2 = Person(firstname="Homer", surname='Simpson')

        raised = False
        try:
            objectstore.flush()
        except SQLError:
            raised = True

        assert raised

        objectstore.clear()

    def teardown(self):
        cleanup_all()

