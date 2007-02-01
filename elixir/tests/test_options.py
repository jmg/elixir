"""
    test options
"""

import nose
from sqlalchemy import create_engine
from supermodel import *
from supermodel import metadata, objectstore


class Record(Entity):
    with_fields(
        title = Field(Unicode(30)),
        artist = Field(Unicode(30)),
        year = Field(Integer)
    )
    
    # order titles descending by year, then by artist, then by title
    using_options(tablename="records", order_by=['-year', 'artist', 'title'])


class TestOptions(object):
    def setup(self):
        engine = create_engine('sqlite:///')
        metadata.connect(engine)
        create_all()
    
    def teardown(self):
        drop_all()
    
    def test_order_by(self):
        artist = "Dream Theater"
        titles = (
            ("A Change Of Seasons", 1995),
            ("Awake", 1994),
            ("Falling Into Infinity", 1997),
            ("Images & Words", 1992),
            ("Metropolis Pt. 2: Scenes From A Memory", 1999),
            ("Octavarium", 2005),
            ("Six Degrees Of Inner Turbulence", 2002),
            ("Train Of Thought", 2003),
            ("When Dream And Day Unite", 1989)
        )
        
        for title, year in titles:
            Record(title=title, artist=artist, year=year)
        
        # TODO: add more artists & albums
        
        objectstore.flush()
        objectstore.clear()
        
        records = Record.select()

        assert records[2].year >= records[5].year
        assert records[3].year >= records[4].year
        assert records[0].year == 2005
        assert records[-1].year == 1989
        
        