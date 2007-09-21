"""
    simple test case
"""

from elixir import *

#-----------

class TestMultiBelongsTo(object):
    def setup(self):
        metadata.bind = 'sqlite:///'
    
    def teardown(self):
        cleanup_all()
    
    def test_belongs_to_multi_ref(self):
        class A(Entity):
            has_field('name', String(32))
            
            has_many('brel1', of_kind='B', inverse='arel1')
            has_many('brel2', of_kind='B', inverse='arel2')
            
        class B(Entity):
            has_field('name', String(15))
            
            belongs_to('arel1', of_kind='A')
            belongs_to('arel2', of_kind='A')

        setup_all(True)

        b1 = B(name="b1")
        b2 = B(name="b2")
        a1 = A(name="a1", brel1=[b1, b2], brel2=[b2])
        a2 = A(name="a2", brel2=[b1])
        
        objectstore.flush()
        objectstore.clear()
        
        a1 = A.get_by(name="a1")
        a2 = A.get_by(name="a2")
        b1 = B.get_by(name="b1")
        
        assert len(a1.brel1) == 2
        assert a1 == a2.brel2[0].arel1
        assert a2 == b1.arel2

class TestMultiHasAndBelongsToMany(object):
    def setup(self):
        global Article, Tag

        class Article(Entity):
            has_field('title', String(100))

            has_and_belongs_to_many('editor_tags', of_kind='Tag')
            has_and_belongs_to_many('user_tags', of_kind='Tag')
            
        class Tag(Entity):
            has_field('name', String(20), primary_key=True)

        metadata.bind = 'sqlite:///'
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
        
        articles = Article.query().all()
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
