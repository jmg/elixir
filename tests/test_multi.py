"""
    simple test case
"""

import sqlalchemy
import datetime

from elixir import *

#-----------

class TestMultiBelongsTo(object):
    def setup(self):
        global Person, Animal
        
        #---------------------------------------
        # classes for the multi belongs_to test

        class Person(Entity):
            has_field('name', Unicode(32))
            
            has_many('pets', of_kind='Animal', inverse='owner')
            has_many('animals', of_kind='Animal', inverse='feeder')
            
            def __str__(self):
                s = '%s\n' % self.name.encode('utf-8')  
                for pet in self.pets:
                    s += '  * pet: %s\n' % pet.name
                return s

        class Animal(Entity):
            has_field('name', String(15))
            has_field('color', String(15))
            
            belongs_to('owner', of_kind='Person')
            belongs_to('feeder', of_kind='Person')

        engine = sqlalchemy.create_engine('sqlite:///')
        metadata.connect(engine)
        create_all()
    
    def teardown(self):
        cleanup_all()
    
    def test_belongs_to_multi_ref(self):
        snowball = Animal(name="Snowball II", color="grey")
        slh = Animal(name="Santa's Little Helper")
        homer = Person(name="Homer", animals=[snowball, slh], pets=[slh])
        lisa = Person(name="Lisa", pets=[snowball])
        
        objectstore.flush()
        objectstore.clear()
        
        homer = Person.get_by(name="Homer")
        lisa = Person.get_by(name="Lisa")
        
        print homer

        assert len(homer.animals) == 2
        assert homer == lisa.pets[0].feeder
        assert homer == slh.owner

class TestMultiHasAndBelongsToMany(object):
    def setup(self):
        global Article, Tag

        class Article(Entity):
            has_field('title', String(100))

            has_and_belongs_to_many('editor_tags', of_kind='Tag')
            has_and_belongs_to_many('user_tags', of_kind='Tag')
            
        class Tag(Entity):
            has_field('name', String(20), primary_key=True)

        engine = sqlalchemy.create_engine('sqlite:///')
        metadata.connect(engine)
        create_all()

    def teardown(self):
        cleanup_all()

    def test_has_and_belongs_to_many_multi_ref(self):
        physics = Tag(name='Physics')
        a1 = Article(
                title="The Foundation of the General Theory of Relativity",
                editor_tags=[Tag(name='Good'), physics],
                user_tags=[Tag(name='Complex'), Tag(name='Einstein'), physics],
             )

        objectstore.flush()
        objectstore.clear()
        
        articles = Article.select()
        physics = Tag.get_by(name='Physics')
        good = Tag.get_by(name='Good')

        assert len(articles) == 1
        assert physics in articles[0].editor_tags 
        assert physics in articles[0].user_tags
        assert good in articles[0].editor_tags

if __name__ == '__main__':
    test = TestMultiBelongsTo()
    test.setup()
    test.test_belongs_to_multi_ref()
    test.teardown()

    test = TestMultiHasAndBelongsToMany()
    test.setup()
    test.test_has_and_belongs_to_many_multi_ref()
    test.teardown()
