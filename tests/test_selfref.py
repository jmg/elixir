"""
    simple test case
"""

from sqlalchemy import create_engine
from elixir     import *


class TestSelfRef(object):
    def setup(self):
        engine = create_engine('sqlite:///')
        metadata.connect(engine)
    
    def teardown(self):
        cleanup_all()
    
    def test_belongs_to_selfref(self):
        class Person(Entity):
            with_fields(
                name = Field(Unicode(30))
            )
            
            belongs_to('father', of_kind='Person', inverse='children')
            has_many('children', of_kind='Person', inverse='father')

        create_all()

        grampa = Person(name="Abe")
        homer = Person(name="Homer")
        bart = Person(name="Bart")
        lisa = Person(name="Lisa")
        
        grampa.children.append(homer)        
        homer.children.append(bart)
        lisa.father = homer
        
        objectstore.flush()
        objectstore.clear()
        
        p = Person.get_by(name="Homer")
        
        print "%s is %s's child." % (p.name, p.father.name)        
        print "His children are: %s." % (
                " and ".join(c.name for c in p.children))
        
        assert p in p.father.children
        assert p.father is Person.get_by(name="Abe")
        assert p is Person.get_by(name="Lisa").father

    def test_has_and_belongs_to_many_selfref(self):
        class Person(Entity):
            with_fields(
                name = Field(Unicode(30))
            )
            
            has_and_belongs_to_many('friends', of_kind='Person')

        create_all()

        barney = Person(name="Barney")
        homer = Person(name="Homer", friends=[barney])
        barney.friends.append(homer)

        objectstore.flush()
        objectstore.clear()
        
        homer = Person.get_by(name="Homer")
        barney = Person.get_by(name="Barney")

        assert homer in barney.friends
        assert barney in homer.friends

class TestMultiSelfRef(object):
    def setup(self):
        engine = create_engine('sqlite:///')
        metadata.connect(engine)
    
    def teardown(self):
        cleanup_all()

    def test_belongs_to_multiple_selfref(self):
        # define a self-referential table with several relations
        class TreeNode(Entity):
            has_field('name', String(50), nullable=False)

            belongs_to('parent', of_kind='TreeNode')
            has_many('children', of_kind='TreeNode', inverse='parent')
            belongs_to('root', of_kind='TreeNode')

            def __str__(self):
                return self._getstring(0)

            def _getstring(self, level):
                s = '  ' * level + \
                    "%s (%s,%s,%s, %d)" % (self.name, self.id, self.parent_id,
                                           self.root_id, id(self)) + \
                    '\n'
                s += ''.join([n._getstring(level+1) for n in self.children])
                return s

        create_all()

        node2 = TreeNode(name='node2')
        node2.children.append(TreeNode(name='subnode1'))
        node2.children.append(TreeNode(name='subnode2'))
        node = TreeNode(name='rootnode')
        node.children.append(TreeNode(name='node1'))
        node.children.append(node2)
        node.children.append(TreeNode(name='node3'))
            
        objectstore.flush()
        objectstore.clear()
        
        root = TreeNode.get_by(name='rootnode')
        print root

if __name__ == '__main__':
    test = TestSelfRef()
    test.setup()
    test.test_belongs_to_selfref()
    test.teardown()        
    test.setup()
    test.test_has_and_belongs_to_many_selfref()
    test.teardown()        

    test = TestMultiSelfRef()
    test.setup()
    test.test_belongs_to_multiple_selfref()
    test.teardown()        
