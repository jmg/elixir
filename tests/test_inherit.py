"""
    simple test case
"""

from elixir import *
import elixir
from elixir.py23compat import sort_list

def setup():
    metadata.bind = 'sqlite:///'
#    metadata.bind = 'postgres://@/test'
#    metadata.bind.echo = True
    elixir.options_defaults['shortnames'] = True

def teardown():
    elixir.options_defaults['shortnames'] = False

def do_tst(inheritance, polymorphic, expected_res):
    class A(Entity):
        using_options(inheritance=inheritance, polymorphic=polymorphic)
        data1 = Field(String(20))

    class B(A):
        using_options(inheritance=inheritance, polymorphic=polymorphic)
        data2 = Field(String(20))
        some_e = ManyToOne('E')

    class C(B):
        using_options(inheritance=inheritance, polymorphic=polymorphic)
        data3 = Field(String(20))

    class D(A):
        using_options(inheritance=inheritance, polymorphic=polymorphic)
        data4 = Field(String(20))

    class E(A):
        using_options(inheritance=inheritance, polymorphic=polymorphic)
        many_b = OneToMany('B')

    setup_all(True)

    A(data1='a1')
    B(data1='b1', data2='b2')
    C(data1='c1', data2='c2', data3='c3')
    D(data1='d1', data4='d4')
    E(data1='e1')

    session.commit()
    session.clear()

    res = {}
    for class_ in (A, B, C, D, E):
        res[class_.__name__] = class_.query.all()
        sort_list(res[class_.__name__], key=lambda o: o.__class__.__name__)

    for query_class in ('A', 'B', 'C', 'D', 'E'):
#        print res[query_class], expected_res[query_class]
        assert len(res[query_class]) == len(expected_res[query_class])
        for real, expected in zip(res[query_class], expected_res[query_class]):
            assert real.__class__.__name__ == expected


class TestInheritance(object):
    def teardown(self):
        cleanup_all(True)

    # this is related to SA ticket 866
    # http://www.sqlalchemy.org/trac/ticket/866
    # the problem was caused by the fact that the attribute-based syntax left
    # the class-attributes in place after initialization (in Elixir 0.4).
    def test_missing_value(self):
        class A(Entity):
            pass

        class B(A):
            name = Field(String(30))
            other = Field(Text)

        setup_all()
        create_all()

        b1 = B(name="b1") # no value for other

        session.commit()

    def test_delete_parent(self):
        class A(Entity):
            using_options(inheritance='multi')

        class B(A):
            using_options(inheritance='multi')
            name = Field(String(30))

        setup_all(True)

        b1 = B(name='b1')

        session.commit()

        A.table.delete().execute()

        # this doesn't work on sqlite (because it relies on the database
        # enforcing the foreign key constraint cascade rule).
#        assert not B.table.select().execute().fetchall()

    def test_inheritance_wh_schema(self):
        # I can only test schema stuff on postgres
        if metadata.bind.name != 'postgres':
            print "schema test skipped"
            return

        class A(Entity):
            using_options(inheritance="multi")
            using_table_options(schema="test")

            row_id = Field(Integer, primary_key=True)
            thing1 = Field(String(20))

        class B(A):
            using_options(inheritance="multi")
            using_table_options(schema="test")

            thing2 = Field(String(20))

        setup_all(True)

    def test_inverse_matching_on_parent(self):
        options_defaults['inheritance'] = 'multi'

        class Person(Entity):
            using_options(inheritance='multi')

            name = Field(UnicodeText)

        class Parent(Person):
            using_options(inheritance='multi')
            childs = ManyToMany('Child', tablename='child_parent',
                                inverse='parents')

        class Child(Person):
            using_options(inheritance='multi')

            parents = ManyToMany('Parent', tablename='child_parent',
                                 inverse='childs')

        setup_all()

    def test_singletable_inheritance(self):
        do_tst('single', False, {
            'A': ('A', 'A', 'A', 'A', 'A'),
            'B': ('B', 'B', 'B', 'B', 'B'),
            'C': ('C', 'C', 'C', 'C', 'C'),
            'D': ('D', 'D', 'D', 'D', 'D'),
            'E': ('E', 'E', 'E', 'E', 'E')
        })

    def test_polymorphic_singletable_inheritance(self):
        do_tst('single', True, {
            'A': ('A', 'B', 'C', 'D', 'E'),
            'B': ('B', 'C'),
            'C': ('C',),
            'D': ('D',),
            'E': ('E',),
        })

    def test_concrete_inheritance(self):
        do_tst('concrete', False, {
            'A': ('A',),
            'B': ('B',),
            'C': ('C',),
            'D': ('D',),
            'E': ('E',),
        })

#    def test_polymorphic_concrete_inheritance(self):
        # to get this test to work, I need to duplicate parent relationships in
        # the children. The problem is that the properties are setup post
        # mapper setup, so I'll need to add some logic into the add_property
        # method which I'm reluctant to do.
#        do_tst('concrete', True, {
#            'A': ('A', 'B', 'C', 'D', 'E'),
#            'B': ('B', 'C'),
#            'C': ('C',),
#            'D': ('D',),
#            'E': ('E',),
#        })

    def test_multitable_inheritance(self):
        do_tst('multi', False, {
            'A': ('A', 'A', 'A', 'A', 'A'),
            'B': ('B', 'B'),
            'C': ('C',),
            'D': ('D',),
            'E': ('E',),
        })

    def test_polymorphic_multitable_inheritance(self):
        do_tst('multi', True, {
            'A': ('A', 'B', 'C', 'D', 'E'),
            'B': ('B', 'C'),
            'C': ('C',),
            'D': ('D',),
            'E': ('E',),
        })

