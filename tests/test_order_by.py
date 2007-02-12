"""
    test options
"""

from sqlalchemy import create_engine
from elixir     import *


class Record(Entity):
    has_field('title', Unicode(30))
    has_field('year', Integer)
    belongs_to('artist', of_kind='Artist')
    has_and_belongs_to_many('genres', of_kind='Genre')

    # order titles descending by year, then by title
    using_options(order_by=['-year', 'title'])

    def __str__(self):
        return "%s - %s (%d)" % (self.artist.name, self.title, self.year)

class Artist(Entity):
    has_field('name', Unicode(30))
    has_many('records', of_kind='Record', order_by=['year', '-title'])

class Genre(Entity):
    has_field('name', Unicode(30))
    has_and_belongs_to_many('records', of_kind='Record', 
                            order_by='-title')
    
class TestOptions(object):
    def setup(self):
        engine = create_engine('sqlite:///')
#        engine.echo = True
        metadata.connect(engine)
        create_all()
    
        artist = Artist(name="Dream Theater")
        genre = Genre(name="Progressive metal")
        titles = (
            ("A Change Of Seasons", 1995),
            ("Awake", 1994),
            ("Falling Into Infinity", 1997),
            ("Images & Words", 1992),
            ("Metropolis Pt. 2: Scenes From A Memory", 1999),
            ("Octavarium", 2005),
            # 2005 is a mistake to make the test more interesting
            ("Six Degrees Of Inner Turbulence", 2005), 
            ("Train Of Thought", 2003),
            ("When Dream And Day Unite", 1989)
        )
        
        for title, year in titles:
            Record(title=title, artist=artist, year=year, genres=[genre])
        
        objectstore.flush()
        objectstore.clear()

    def teardown(self):
        # we don't use cleanup_all because setup and teardown are called for 
        # each test, and since the class is not redefined, it will not be
        # reinitialized so we can't kill it
        drop_all()
    
    def test_mapper_order_by(self):
        records = Record.select()

        print "-year, +title"
        for record in records:
            print record

        assert records[0].year == 2005
        assert records[2].year >= records[5].year
        assert records[3].year >= records[4].year
        assert records[-1].year == 1989

    def test_has_many_order_by(self):
        records = Artist.get_by(name="Dream Theater").records

        print "+year, -title"
        for record in records:
            print record

        assert records[0].year == 1989
        assert records[2].year <= records[5].year
        assert records[3].year <= records[4].year
        assert records[-1].title == 'Octavarium'
        assert records[-1].year == 2005

    def test_has_and_belongs_to_many_order_by(self):
        records = Genre.get_by(name="Progressive metal").records

        print "-title"
        for record in records:
            print record

        assert records[0].year == 1989
        assert records[2].title >= records[5].title
        assert records[3].title >= records[4].title
        assert records[-1].year == 1995

