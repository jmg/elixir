from elixir.py23compat import *

def test_set():
    s = set(range(10) + range(5,11))
    assert s == set(range(11))

def test_sort_list_with_key():
    l = ['foo', 'Fool', 'bar', 'Bark']
    sort_list(l, key=str.lower)
    assert l == ['bar', 'Bark', 'foo', 'Fool']

def test_sort_list_with_key_and_reverse():
    l = ['foo', 'Fool', 'bar', 'Bark']
    sort_list(l, key=str.lower)
    rl = list(l)
    rl.reverse()
    sort_list(l, key=str.lower, reverse=True)
    assert l == rl

def test_sorted():
    l = ['foo', 'Fool', 'bar', 'Bark']
    sl = sorted(l)
    assert l != sl
    l.sort()
    assert l == sl

def test_docstrings():
    import elixir.py23compat
    import doctest

    failed, total = doctest.testmod(elixir.py23compat, verbose=False)
    assert not failed
