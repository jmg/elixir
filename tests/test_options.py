"""
    test options
"""

from sqlalchemy import create_engine
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
    
       
