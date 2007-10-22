"""
    simple test case
"""

from elixir import *


class TestSelfRef(object):
    def setup(self):
        metadata.bind = 'sqlite:///'
    
    def teardown(self):
        cleanup_all()
    

class TestMultiSelfRef(object):
    def setup(self):
        metadata.bind = 'sqlite:///'
    
    def teardown(self):
        cleanup_all()


