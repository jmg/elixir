"""
test one to many relationships
"""

from elixir import *

def setup():
    metadata.bind = 'sqlite:///'

class TestOneToMany(object):
    def teardown(self):
        cleanup_all(True)
    
    def test_simple(self):
        class A(Entity):
            name = Field(String(60))
            bs = OneToMany('B')

        class B(Entity):
            name = Field(String(60))
            a = ManyToOne('A')

        setup_all(True)

        a1 = A(name='a1')
        b1 = B(name='b1', a=a1)

        # does it work before a flush? (does the backref work?)
        assert b1 in a1.bs

        session.flush()
        session.clear()

        b = B.query.one()
        a = b.a

        assert b in a.bs

    def test_selfref(self):
        class Person(Entity):
            name = Field(String(30))
            
            father = ManyToOne('Person', inverse='children')
            children = OneToMany('Person', inverse='father')

        setup_all(True)

        grampa = Person(name="Abe")
        homer = Person(name="Homer")
        bart = Person(name="Bart")
        lisa = Person(name="Lisa")
        
        grampa.children.append(homer)        
        homer.children.append(bart)
        lisa.father = homer
        
        session.flush()
        session.clear()
        
        p = Person.get_by(name="Homer")
        
        print "%s is %s's child." % (p.name, p.father.name)        
        print "His children are: %s." % (
                " and ".join([c.name for c in p.children]))
        
        assert p in p.father.children
        assert p.father is Person.get_by(name="Abe")
        assert p is Person.get_by(name="Lisa").father

    def test_multiple_selfref(self):
        # define a self-referential table with several relations

        class TreeNode(Entity):
            name = Field(String(50), required=True)

            parent = ManyToOne('TreeNode')
            children = OneToMany('TreeNode', inverse='parent')
            root = ManyToOne('TreeNode')

            def __str__(self):
                return self._getstring(0)

            def _getstring(self, level):
                s = '  ' * level + \
                    "%s (%s,%s,%s, %d)" % (self.name, self.id, self.parent_id,
                                           self.root_id, id(self)) + \
                    '\n'
                s += ''.join([n._getstring(level+1) for n in self.children])
                return s

        setup_all(True)

        node2 = TreeNode(name='node2')
        node2.children.append(TreeNode(name='subnode1'))
        node2.children.append(TreeNode(name='subnode2'))
        node = TreeNode(name='rootnode')
        node.children.append(TreeNode(name='node1'))
        node.children.append(node2)
        node.children.append(TreeNode(name='node3'))
            
        session.flush()
        session.clear()
        
        root = TreeNode.get_by(name='rootnode')
        print root

    def test_has_many_syntax(self):
        class Person(Entity):
            has_field('name', String(30))
            has_many('pets', of_kind='Animal')

        class Animal(Entity):
            has_field('name', String(30))
            belongs_to('owner', of_kind='Person')

        setup_all(True)
        
        santa = Person(name="Santa Claus")
        rudolph = Animal(name="Rudolph", owner=santa)
        
        session.flush()
        session.clear()
      
        santa = Person.get_by(name="Santa Claus")

        assert Animal.get_by(name="Rudolph") in santa.pets
