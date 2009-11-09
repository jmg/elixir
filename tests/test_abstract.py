"""
test inheritance with abstract entities
"""

import re

from elixir import *
import elixir

def camel_to_underscore(entity):
    return re.sub(r'(.+?)([A-Z])+?', r'\1_\2', entity.__name__).lower()

def setup():
    metadata.bind = 'sqlite://'
    elixir.options_defaults['shortnames'] = True

class TestAbstractInheritance(object):
    def teardown(self):
        cleanup_all(True)

    def test_abstract_alone(self):
        class AbstractPerson(Entity):
            using_options(abstract=True)

            firstname = Field(String(30))
            lastname = Field(String(30))

        setup_all(True)

        assert not hasattr(AbstractPerson, 'table')

    def test_inheritance(self):
        class AbstractPerson(Entity):
            using_options(abstract=True)

            firstname = Field(String(30))
            lastname = Field(String(30))

        class AbstractEmployed(AbstractPerson):
            using_options(abstract=True)

            corporation = Field(String(30))

        class Employed(AbstractEmployed):
            service = Field(String(30))

        class Citizen(AbstractPerson):
            country = Field(String(30))

        setup_all(True)

        assert not hasattr(AbstractPerson, 'table')
        assert not hasattr(AbstractEmployed, 'table')
        assert hasattr(Employed, 'table')
        assert hasattr(Citizen, 'table')

        assert 'firstname' in Employed.table.columns
        assert 'lastname' in Employed.table.columns
        assert 'corporation' in Employed.table.columns
        assert 'service' in Employed.table.columns

        assert 'firstname' in Citizen.table.columns
        assert 'lastname' in Citizen.table.columns
        assert 'corporation' not in Citizen.table.columns
        assert 'country' in Citizen.table.columns

    def test_simple_relation(self):
        class Page(Entity):
            title = Field(String(30))
            content = Field(String(30))
            comments = OneToMany('Comment')

        class AbstractAttachment(Entity):
            using_options(abstract=True)

            page = ManyToOne('Page')
            is_spam = Field(Boolean())

        class Comment(AbstractAttachment):
            message = Field(String(100))

        setup_all(True)

        p1 = Page(title="My title", content="My content")
        p1.comments.append(Comment(message='My first comment', is_spam=False))

        assert p1.comments[0].page == p1
        session.commit()

    def test_simple_relation_abstract_wh_multiple_children(self):
        class Page(Entity):
            title = Field(String(30))
            content = Field(String(30))
            comments = OneToMany('Comment')
            links = OneToMany('Link')

        class AbstractAttachment(Entity):
            using_options(abstract=True)

            page = ManyToOne('Page')
            is_spam = Field(Boolean())

        class Link(AbstractAttachment):
            url = Field(String(30))

        class Comment(AbstractAttachment):
            message = Field(String(100))

        setup_all(True)

        p1 = Page(title="My title", content="My content")
        p1.comments.append(Comment(message='My first comment', is_spam=False))
        p1.links.append(Link(url="My url", is_spam=True))

        assert p1.comments[0].page == p1
        session.commit()

    def test_multiple_inheritance(self):
        class AbstractDated(Entity):
            using_options(abstract=True)
            using_options_defaults(tablename=camel_to_underscore)

            #TODO: add defaults
            created_date = Field(DateTime)
            modified_date = Field(DateTime)

        class AbstractContact(Entity):
            using_options(abstract=True)
            using_options_defaults(identity=camel_to_underscore)

            first_name = Field(Unicode(50))
            last_name = Field(Unicode(50))

        class DatedContact(AbstractContact, AbstractDated):
            pass

        setup_all(True)

        assert 'created_date' in DatedContact.table.columns
        assert 'modified_date' in DatedContact.table.columns
        assert 'first_name' in DatedContact.table.columns
        assert 'last_name' in DatedContact.table.columns
        assert DatedContact._descriptor.identity == 'dated_contact'
        assert DatedContact.table.name == 'dated_contact'

        contact1 = DatedContact(first_name=u"Guido", last_name=u"van Rossum")
        session.commit()

    def test_mixed_inheritance(self):
        class AbstractDated(Entity):
            using_options(abstract=True)
            using_options_defaults(tablename=camel_to_underscore)

            #TODO: add defaults
            created_date = Field(DateTime)
            modified_date = Field(DateTime)

        class AbstractContact(Entity):
            using_options(abstract=True)
            using_options_defaults(identity=camel_to_underscore)

            first_name = Field(Unicode(50))
            last_name = Field(Unicode(50))

        class Contact(AbstractContact):
            using_options(inheritance='multi')

        class DatedContact(AbstractDated, Contact):
            using_options(inheritance='multi')

        setup_all(True)

        assert 'created_date' in DatedContact.table.columns
        assert 'modified_date' in DatedContact.table.columns
        assert DatedContact._descriptor.identity == 'dated_contact'
        assert DatedContact.table.name == 'dated_contact'

        contact1 = DatedContact(first_name=u"Guido", last_name=u"van Rossum")
        session.commit()

