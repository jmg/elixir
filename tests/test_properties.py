"""
test special properties (eg. column_property, ...)
"""

from sqlalchemy.orm import column_property
from elixir import *

def setup():
    metadata.bind = 'sqlite:///'


class TestSpecialProperties(object):
    def teardown(self):
        cleanup_all()
    
    def test_has_property(self):
        class Tag(Entity):
            has_field('score1', Float)
            has_field('score2', Float)
            has_property('query_score', 
                         lambda c: column_property(
                             (c.score1 * c.score2).label('query_score')))

            query_score2 = GenericProperty( 
                         lambda c: column_property(
                             (c.score1 * c.score2 + 1).label('query_score2')))
            query_score3 = ColumnProperty(lambda c: c.score1 * c.score2 + 2)
            belongs_to('user', of_kind='User')

            @property
            def prop_score(self):
                return self.score1 * self.score2

        class User(Entity):
            has_field('name', String(16))
            has_many('tags', of_kind='Tag', lazy=False) 

        setup_all(True)

        u1 = User(name='joe', tags=[Tag(score1=5.0, score2=3.0), 
                                    Tag(score1=55.0, score2=1.0)])

        u2 = User(name='bar', tags=[Tag(score1=5.0, score2=4.0), 
                                    Tag(score1=50.0, score2=1.0),
                                    Tag(score1=15.0, score2=2.0)])

        session.flush()
        session.clear()
        
        for user in User.query.all():
            for tag in user.tags:
                assert tag.query_score == tag.prop_score
                assert tag.query_score2 == tag.prop_score + 1
                assert tag.query_score3 == tag.prop_score + 2

    def test_deferred(self):
        class A(Entity):
            name = Field(String(20))
            stuff = Field(String, deferred=True)

        setup_all(True)

        A(name='foo')
        session.flush()

    def test_synonym(self):
        class Person(Entity):
            name = Field(String(50), required=True)
            _email = Field(String(20), colname='email', synonym='email')

            def _set_email(self, email):
                Person.email_values.append(email)
                self._email = email

            def _get_email(self):
                Person.email_gets += 1
                return self._email

            email = property(_get_email, _set_email)
            email_values = []
            email_gets = 0

        setup_all(True)

        mrx = Person(name='Mr. X', email='x@y.com')

        assert mrx.email == 'x@y.com'
        assert Person.email_gets == 1

        mrx.email = "x@z.com"

        assert Person.email_values == ['x@y.com', 'x@z.com']

        session.flush()
        session.clear()
       
        p = Person.get_by(email='x@z.com')
        
        assert p.name == 'Mr. X'

