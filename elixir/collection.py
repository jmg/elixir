'''
Default entity collection implementation
'''
import sys

from elixir.py23compat import rsplit

# default entity collection
class EntityCollection(list):
    def __init__(self):
        # _entities is a dict of entities keyed on their name.
        self._entities = {}
        list.__init__(self)

    def append(self, entity):
        '''
        Add an entity to the collection.
        '''
        super(EntityCollection, self).append(entity)

        key = entity.__name__
        mapped_entity = self._entities.get(key)
        if mapped_entity:
            if isinstance(mapped_entity, list):
                mapped_entity.append(entity)
            else:
                self._entities[key] = [mapped_entity, entity]
        else:
            self._entities[key] = entity

    def resolve(self, key, entity=None):
        '''
        Resolve a key to an Entity. The optional `entity` argument is the
        "source" entity when resolving relationship targets.
        '''
        path = rsplit(key, '.', 1)
        classname = path.pop()
        if path:
            # Do we have a fully qualified entity name?
            module = sys.modules[path.pop()]
            return getattr(module, classname, None)
        else:
            # Otherwise we look in the entities of this collection
            res = self._entities.get(key, None)
            if res is None:
                if entity:
                    raise Exception("Couldn't resolve target '%s' in '%s'" \
                                    % (key, entity.__name__))
                else:
                    raise Exception("This collection does not contain any "
                                    "entity corresponding to the key '%s'!"
                                    % key)
            elif isinstance(res, list):
                raise Exception("'%s' resolves to several entities, you should "
                                "use the full path (including the full module "
                                "name) to that entity." % key)
            else:
                return res

    def clear(self):
        self._entities = {}
        del self[:]

    def __getattr__(self, key):
        return self.resolve(key)


