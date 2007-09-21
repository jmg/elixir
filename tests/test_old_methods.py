"""
    simple test case
"""

from elixir import *

#-----------

class TestOldMethods(object):
    def setup(self):
        metadata.bind = 'sqlite:///'
    
    def teardown(self):
        cleanup_all()
    
    def test_get(self):
        class A(Entity):
            has_field('name', Unicode(32))

        setup_all(True)

        a1 = A(name="a1")
        
        objectstore.flush()
        objectstore.clear()
        
        assert A.get(1).name == "a1"


