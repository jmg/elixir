"""
Test the associable statement generator
"""

from sqlalchemy import create_engine, and_
from elixir     import *
from elixir.ext.associable import associable


def setup(self):
#    metadata.bind = create_engine('sqlite:///', echo=True)
    metadata.bind = 'sqlite:///'

class TestOrders(object):
    def teardown(self):
        cleanup_all(True)
    
    def test_empty(self):
        class Foo(Entity):
            pass

        class Bar(Entity):
            pass

        is_fooable = associable(Foo)
        is_barable = associable(Bar)

        class Quux(Entity):
            is_fooable()
            is_barable()

        setup_all(True)

    def test_basic(self):
        class Address(Entity):
            has_field('street', String(130))
            has_field('city', String)
            using_options(shortnames=True)

        class Comment(Entity):
            has_field('id', Integer, primary_key=True)
            has_field('name', Unicode)
            has_field('text', String)

        is_addressable = associable(Address, 'addresses')
        is_commentable = associable(Comment, 'comments')

        class Person(Entity):
            has_field('id', Integer, primary_key=True)
            has_field('name', Unicode)
            has_many('orders', of_kind='Order')
            using_options(shortnames=True)
            is_addressable()
            is_commentable()

        class Order(Entity):
            has_field('order_num', Integer, primary_key=True)
            has_field('item_count', Integer)
            belongs_to('person', of_kind='Person')
            using_options(shortnames=True)
            is_addressable('address', uselist=False)

        setup_all(True)

        home = Address(street='123 Elm St.', city='Spooksville')
        work = Address(street='243 Hooper st.', city='Cupertino')
        user = Person(name='Jane Doe')
        user.addresses.append(home)
        user.addresses.append(work)

        neworder = Order(item_count=4)
        neworder.address = home
        user.orders.append(neworder)

        session.flush()
        session.clear()

        # Queries using the added helpers
        people = Person.select_by_addresses(city='Cupertino')
        assert len(people) == 1

        streets = [adr.street for adr in people[0].addresses]
        assert '243 Hooper st.' in streets
        assert '123 Elm St.' in streets
        
        people = Person.select_addresses(and_(Address.c.street=='132 Elm St',
                                              Address.c.city=='Smallville'))
        assert len(people) == 0

    def test_with_forward_ref(self):
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

        setup_all(True)

        art = Article(title='Hope Soars')

        session.flush()
        session.clear()
