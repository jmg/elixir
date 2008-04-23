"""
    test the deep-set functionality
"""

import sqlalchemy as sa, elixir as el

def setup():
    el.metadata.bind = 'sqlite:///'
    global Table1, Table2, Table3
    class Table1(el.Entity):
        name = el.Field(el.String(30))
        tbl2s = el.OneToMany('Table2')
        tbl3 = el.OneToOne('Table3')
    class Table2(el.Entity):
        name = el.Field(el.String(30))
        tbl1 = el.ManyToOne(Table1)
    class Table3(el.Entity):
        name = el.Field(el.String(30))
        tbl1 = el.ManyToOne(Table1)
    el.setup_all()
    el.create_all()

def test_set_attr():
    t1 = Table1()
    t1.from_dict(dict(name='test1'))
    assert t1.name == 'test1'

def test_nonset_attr():
    t1 = Table1(name='test2')
    t1.from_dict({})
    assert t1.name == 'test2'

def test_set_rel():
    t1 = Table1()
    t1.from_dict(dict(tbl3={'name':'bob'}))
    assert t1.tbl3.name == 'bob'

def test_remove_rel():
    t1 = Table1()
    t1.tbl3 = Table3()
    t1.from_dict(dict(tbl3=None))
    assert t1.tbl3 is None

def test_update_rel():
    t1 = Table1()
    t1.tbl3 = Table3(name='fred')
    t1.from_dict(dict(tbl3={'name':'bob'}))
    assert t1.tbl3.name == 'bob'

def test_extend_list():
    t1 = Table1()
    t1.from_dict(dict(tbl2s=[{'name':'test3'}]))
    assert len(t1.tbl2s) == 1
    assert t1.tbl2s[0].name == 'test3'

def test_truncate_list():
    t1 = Table1()
    t2 = Table2()
    t1.tbl2s.append(t2)
    el.session.flush()
    t1.from_dict(dict(tbl2s=[]))
    assert len(t1.tbl2s) == 0

def test_update_list_item():
    t1 = Table1()
    t2 = Table2()
    t1.tbl2s.append(t2)
    el.session.flush()
    t1.from_dict(dict(tbl2s=[{'id':t2.id, 'name':'test4'}]))
    assert len(t1.tbl2s) == 1
    assert t1.tbl2s[0].name == 'test4'

def test_invalid_update():
    t1 = Table1()
    t2 = Table2()
    t1.tbl2s.append(t2)
    el.session.flush()
    try:
        t1.from_dict(dict(tbl2s=[{'id':t2.id+1}]))
        assert False
    except sa.exceptions.ArgumentError:
        pass

def test_to():
    t1 = Table1(id=50, name='test1')
    assert t1.to_dict() == {'id':50, 'name':'test1'}

def test_to_deep():
    t1 = Table1(id=51, name='test2')
    assert t1.to_dict(deep={'tbl2s':{}}) == \
            {'id':51, 'name':'test2', 'tbl2s':[]}

def test_to_deep2():
    t1 = Table1(id=52, name='test3')
    t2 = Table2(id=50, name='test4')
    t1.tbl2s.append(t2)
    el.session.flush()
    assert t1.to_dict(deep={'tbl2s':{}}) == \
            {'id':52, 'name':'test3', 'tbl2s':[{'id':50, 'name':'test4'}]}

def test_to_deep3():
    t1 = Table1(id=53, name='test2')
    t1.tbl3 = Table3(id=50, name='wobble')
    el.session.flush()
    assert t1.to_dict(deep={'tbl3':{}}) == \
            {'id':53, 'name':'test2', 'tbl3':{'id':50,'name':'wobble'}}
