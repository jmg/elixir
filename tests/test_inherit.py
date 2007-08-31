"""
    simple test case
"""

from elixir import *
import elixir

def setup():
    metadata.bind = 'sqlite:///'
#    metadata.bind.echo = True
    elixir.options_defaults['shortnames'] = True

def do_tst(inheritance, polymorphic, with_rel, expected_res):
    class A(Entity):
        has_field('data1', String(20))
        using_options(inheritance=inheritance, polymorphic=polymorphic)

    class B(A):
        has_field('data2', String(20))
        if with_rel:
            has_many('many_c', of_kind='C', inverse='some_b')        
        using_options(inheritance=inheritance, polymorphic=polymorphic)

    class C(B):
        has_field('data3', String(20))
        if with_rel:
            belongs_to('some_b', of_kind='B', inverse='many_c')
        using_options(inheritance=inheritance, polymorphic=polymorphic)

    class D(A):
        has_field('data4', String(20))
        using_options(inheritance=inheritance, polymorphic=polymorphic)

    setup_all(True)

    A(data1='a1')
    B(data1='b1', data2='b2')
    C(data1='c1', data2='c2', data3='c3')
    D(data1='d1', data4='d4')

    objectstore.flush()
    objectstore.clear()

    res = {}
    for class_ in (A, B, C, D):
        res[class_.__name__] = class_.q.all()
        res[class_.__name__].sort(key=lambda o: o.__class__.__name__) 

    for query_class in ('A', 'B', 'C', 'D'):
        assert len(res[query_class]) == len(expected_res[query_class])
        for real, expected in zip(res[query_class], expected_res[query_class]):
            assert real.__class__.__name__ == expected


class TestInheritance(object):
    def teardown(self):
        cleanup_all(True)

    def test_singletable_inheritance(self):
        do_tst('single', False, True, {
            'A': ('A', 'A', 'A', 'A'),
            'B': ('B', 'B', 'B', 'B'),
            'C': ('C', 'C', 'C', 'C'),
            'D': ('D', 'D', 'D', 'D'),
        })

    def test_polymorphic_singletable_inheritance(self):
        do_tst('single', True, True, {
            'A': ('A', 'B', 'C', 'D'),
            'B': ('B', 'C'),
            'C': ('C',),
            'D': ('D',),
        })

    def test_concrete_inheritance(self):
        # concrete fails when there are relationships involved !
        do_tst('concrete', False, False, {
            'A': ('A',),
            'B': ('B',),
            'C': ('C',),
            'D': ('D',),
        })

    def test_multitable_inheritance(self):
        do_tst('multi', False, True, {
            'A': ('A', 'A', 'A', 'A'),
            'B': ('B', 'B'),
            'C': ('C',),
            'D': ('D',),
        })
 
    def test_polymorphic_multitable_inheritance(self):
        do_tst('multi', True, True, {
            'A': ('A', 'B', 'C', 'D'),
            'B': ('B', 'C'),
            'C': ('C',),
            'D': ('D',),
        })

