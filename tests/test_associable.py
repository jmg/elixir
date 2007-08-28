"""
Test the associable statement generator
"""

from sqlalchemy import create_engine, and_
from elixir     import *
from elixir.ext.associable import associable

class Address(Entity):
    has_field('street', String(130))
    has_field('city', String)
    using_options(shortnames=True)

is_addressable = associable(Address, 'addresses')

class Person(Entity):
    has_field('id', Integer, primary_key=True)
    has_field('name', Unicode)
    has_many('orders', of_kind='Order')
    using_options(shortnames=True)
    is_addressable()

class Order(Entity):
    has_field('order_num', Integer, primary_key=True)
    has_field('item_count', Integer)
    belongs_to('person', of_kind='Person')
    using_options(shortnames=True)
    is_addressable('address', uselist=False)

class TestOrders(object):
    def setup(self):
        engine = create_engine('sqlite:///', echo=True)
        metadata.connect(engine)
        create_all()
    
    def teardown(self):
        cleanup_all()
    
    def test_bidirectional(self):
        home = Address(street='123 Elm St.', city='Spooksville')
        work = Address(street='243 Hooper st.', city='Cupertino')
        user = Person(name='Jane Doe')
        user.addresses.append(home)
        user.addresses.append(work)

        neworder = Order(item_count=4)
        neworder.address = home
        user.orders.append(neworder)

        objectstore.flush()
        objectstore.clear()

        # Queries using the added helpers
        people = Person.select_by_addresses(city='Cupertino')
        assert len(people) > 0
        assert people[0].addresses[1].street == '243 Hooper st.'
        assert people[0].addresses[0].street == '123 Elm St.'
        
        peopl = Person.select_addresses(and_(Address.c.street=='132 Elm St',
                                        Address.c.city=='Smallville'))
        assert len(people) > 0
        