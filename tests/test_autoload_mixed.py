from elixir import *

def setup():
    metadata.connect('sqlite:///')

def teardown():
    cleanup_all()

class TestAutoloadMixed(object):
    def setup(self):
        conn = metadata.engine.connect()
        conn.execute("""CREATE TABLE user
        (user_id INTEGER PRIMARY KEY AUTOINCREMENT)""")
        conn.close()
        
    def test_belongs_to(self):
        global User, Item

        class User(Entity):
            using_options(tablename='user', autoload=True)

        class Item(Entity):
            belongs_to('owner', of_kind='User')

        create_all()

        assert Item.table.c['owner_user_id'].foreign_key.column.name == 'user_id'

