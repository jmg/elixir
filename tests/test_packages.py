"""
    simple test case
"""

from elixir import *
import elixir

def teardown():
    cleanup_all()

class TestPackages(object):
    def setup(self):
        metadata.connect('sqlite:///')
    
    def teardown(self):
        drop_all()
        objectstore.clear()
    
    def test_packages(self):
        # This is an ugly workaround because when nosetest is run globally (ie
        # either on the tests directory or in the "trunk" directory, it imports
        # all modules, including a and b and thus their entities are
        # immediately setup but then the other tests clear all mappers, and 
        # when we get here, this tests doesn't reinit those because the modules
        # are not reimported. 
        # In short, one more reason to use delay_setup by default. 
        # Note that even if we set delay setup in this particular test, before
        # the module imports, it'll fail because we'd need to set delay_setup
        # before the a and b modules are imported by nosetests.
        import sys
        sys.modules.pop('tests.a', None)
        sys.modules.pop('tests.b', None)

        from tests.a import A
        from tests.b import B
        create_all()

        a = A(name='a1')
        b = B(name='b1')

        b.a.append(a)

        objectstore.flush()

