from elixir import *
from elixir.ext.encrypted import acts_as_encrypted
 

def setup():
    global Person, Pet
    
    class Person(Entity):
        has_field('name', Unicode)
        has_field('password', Unicode)
        has_field('ssn', Unicode)
        has_many('pets', of_kind='Pet')
        acts_as_encrypted(for_fields=['password', 'ssn'], with_secret='secret')

    class Pet(Entity):
        has_field('name', Unicode)
        has_field('codename', Unicode)
        acts_as_encrypted(for_fields=['codename'], with_secret='secret2')
        belongs_to('owner', of_kind='Person')

    
    metadata.bind = 'sqlite:///'


def teardown():
    cleanup_all()


class TestEncryption(object):
    def setup(self):
        create_all()
    
    def teardown(self):
        drop_all()
        objectstore.clear()
    
    def test_encryption(self):    
        jonathan = Person(
            name=u'Jonathan LaCour', 
            password=u's3cr3tw0RD', 
            ssn=u'123-45-6789'
        )
        winston = Pet(
            name='Winston',
            codename='Pug/Shih-Tzu Mix'
        )
        nelson = Pet(
            name='Nelson',
            codename='Pug'
        )
        jonathan.pets = [winston, nelson]

        objectstore.flush(); objectstore.clear()

        p = Person.q.get_by(name='Jonathan LaCour')
        assert p.password == 's3cr3tw0RD'
        assert p.ssn == '123-45-6789'
        assert p.pets[0].name == 'Winston'
        assert p.pets[0].codename == 'Pug/Shih-Tzu Mix'
        assert p.pets[1].name == 'Nelson'
        assert p.pets[1].codename == 'Pug'

        p.password = 'N3wpAzzw0rd'

        objectstore.flush(); objectstore.clear()

        p = Person.q.get_by(name='Jonathan LaCour')
        assert p.password == 'N3wpAzzw0rd'
        p.name = 'Jon LaCour'

        objectstore.flush(); objectstore.clear()