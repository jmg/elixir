"""
Test the associable statement generator with a delayed import name
"""

from sqlalchemy import create_engine, and_
from elixir     import *
from elixir.ext.associable import associable


class Checkout(Entity):
    belongs_to('by', of_kind='Villian', ondelete='cascade')
    has_field('stamp', DateTime)

can_checkout = associable(Checkout, 'checked_out')

class Article(Entity):
    has_field('title', Unicode)
    has_field('content', Unicode)
    can_checkout('checked_out_by', uselist=False)
    using_options(tablename='article')

class Villian(Entity):
    has_field('name', Unicode)
    using_options(tablename='villian')


class TestOrders(object):
    def setup(self):
        engine = create_engine('sqlite:///', echo=True)
        metadata.connect(engine)
        create_all()
    
    def teardown(self):
        cleanup_all()
    
    def test_basic(self):
        art = Article(title='Hope Soars')
        objectstore.flush()
        objectstore.clear()
