"""
    simple test case
"""

from sqlalchemy import create_engine
from elixir     import *

class Director(Entity):
    with_fields(
        name = Field(Unicode(60))
    )
    
    has_many('movies', of_kind='Movie', inverse='director')
    
    using_options(shortnames=True)


class Movie(Entity):
    """
        simple movie class
    """
    
    # columns
    with_fields(
        title = Field(Unicode(50)),
        year = Field(Integer)
    )
    
    # relationships
    belongs_to('director', of_kind="Director", inverse='movies')
    
    has_and_belongs_to_many('actors', of_kind="Actor", inverse='movies')
    has_one('media', of_kind='Media', inverse='movie')
    
    # options
    using_options(tablename="movies_table")


class Actor(Entity):
    with_fields(
        name = Field(Unicode(60))
    )
    
    has_and_belongs_to_many('movies', of_kind="Movie", inverse="actors")


class Media(Entity):
    with_fields(
        number = Field(Integer, primary_key=True)
    )
    
    belongs_to('movie', of_kind='Movie', inverse='media')
    

class TestMovies(object):
    def setup(self):
        engine = create_engine('sqlite:///')
        metadata.connect(engine)
        create_all()
    
    def teardown(self):
        cleanup_all()
    
    def test_bidirectional(self):
        brunner = Movie(title="Blade Runner", year=1982)
        alien = Movie(title="Alien", year=1979)
        swars = Movie(title="Star Wars", year=1977)
        
        brunner.media = Media(number=1)
        m = Media(number=7)
        m.movie = alien
        
        rscott = Director(name="Ridley Scott")
        glucas = Director(name="George Lucas")
        
        hford = Actor(name="Harrison Ford")
        mhamill = Actor(name="Mark Hamill")
        sweaver = Actor(name="Sigourney Weaver")
        
        rscott.movies.append(brunner) 
        rscott.movies.append(alien)
        swars.director = glucas
        
        swars.actors.append(hford)
        swars.actors.append(mhamill)
        alien.actors.append(sweaver)
        brunner.actors.append(hford)
        
        objectstore.flush()
        objectstore.clear()
        
        # directors
        assert Movie.get_by(title="Alien").director is Director.get_by(name="Ridley Scott")
        assert Director.get_by(name="Ridley Scott").name == "Ridley Scott"
        assert Movie.get_by(title="Alien").director.name == "Ridley Scott"
        assert Movie.get_by(title="Star Wars").director is Director.get_by(name="George Lucas")
        
        # movie
        assert Movie.get_by(title="Blade Runner").year == 1982
        assert Movie.get_by(title="Alien").year == 1979
        
        # actors
        assert Actor.get_by(name="Harrison Ford") in Movie.get_by(title="Blade Runner").actors
        assert Actor.get_by(name="Harrison Ford") in Movie.get_by(title="Star Wars").actors
        assert Movie.get_by(title="Star Wars") in Actor.get_by(name="Mark Hamill").movies
        assert Movie.get_by(title="Blade Runner") in Actor.get_by(name="Harrison Ford").movies
        
        # media
        assert Movie.get_by(title="Blade Runner").media is Media.get_by(number=1)
        assert Movie.get_by(title="Blade Runner").media.number is Media.get_by(number=1).number
        assert Actor.get_by(name="Sigourney Weaver") in Media.get_by(number=7).movie.actors

