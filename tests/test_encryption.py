from elixir import *
from elixir.ext.encrypted import acts_as_encrypted
 

def setup():
    global Person, Pet
    
    class Person(Entity):
        name = Field(Unicode)
        password = Field(Unicode)
        ssn = Field(Unicode)
        pets = OneToMany('Pet')
        acts_as_encrypted(for_fields=['password', 'ssn'], with_secret='secret')

    class Pet(Entity):
        name = Field(Unicode)
        codename = Field(Unicode)
        acts_as_encrypted(for_fields=['codename'], with_secret='secret2')
        owner = ManyToOne('Person')

    
    metadata.bind = 'sqlite:///'


def teardown():
    cleanup_all()


class TestEncryption(object):
    def setup(self):
        create_all()
    
    def teardown(self):
        drop_all()
        session.clear()
    
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

        session.flush(); session.clear()

        p = Person.get_by(name='Jonathan LaCour')
        assert p.password == 's3cr3tw0RD'
        assert p.ssn == '123-45-6789'
        assert p.pets[0].name == 'Winston'
        assert p.pets[0].codename == 'Pug/Shih-Tzu Mix'
        assert p.pets[1].name == 'Nelson'
        assert p.pets[1].codename == 'Pug'

        p.password = 'N3wpAzzw0rd'

        session.flush(); session.clear()

        p = Person.get_by(name='Jonathan LaCour')
        assert p.password == 'N3wpAzzw0rd'
        p.name = 'Jon LaCour'

        session.flush(); session.clear()
