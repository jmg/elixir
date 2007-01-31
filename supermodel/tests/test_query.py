'''
simple test case for a DSL-like Query syntax
'''

from sqlalchemy import create_engine
from supermodel import has_field, has_many, belongs_to, has_and_belongs_to_many
from supermodel import Entity, metadata, objectstore, Unicode, Integer
from supermodel import create_all, drop_all
from supermodel.query import Query, selects, where, ordered_by


class Director(Entity):
    has_field('name', Unicode(60))
    has_many('movies', of_kind='Movie', inverse='director')

class Movie(Entity):    
    has_field('title', Unicode(50))
    has_field('year', Integer)
    belongs_to('director', of_kind='Director', inverse='movies')
    has_and_belongs_to_many('actors', of_kind='Actor', inverse='movies')
    
class Actor(Entity):
    has_field('name', Unicode(60))
    has_and_belongs_to_many('movies', of_kind='Movie', inverse='actors')


class TestMovies(object):
    def setup(self):
        engine = create_engine('sqlite:///')
        metadata.connect(engine)
        create_all()
        
        brunner = Movie(title="Blade Runner", year=1982)
        alien = Movie(title="Alien", year=1979)
        swars = Movie(title="Star Wars", year=1977)
        
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
    
    def teardown(self):
        drop_all()
    
    def test_query(self):
        class DirectorsQuery(Query):
            selects(Director.c.id, Director.c.name, Movie.c.id, Movie.c.title)
            where(Director.c.name != 'George Lucas')
            ordered_by(Movie.c.title, Director.c.name)
        
        count = 0
        for row in DirectorsQuery():
            director = Director.get(row[0])
            movie = Movie.get(row[2])
            
            assert director.name == row[1]
            assert movie.title == row[3]
            
            count += 1
        assert count == 3
        
        count = 0
        for row in DirectorsQuery(Movie.c.title != 'Blade Runner'):
            director = Director.get(row[0])
            movie = Movie.get(row[2])
            
            assert director.name == row[1]
            assert movie.title == row[3]
            
            count += 1
        assert count == 2