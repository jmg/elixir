from sqlalchemy.orm.mapper  import MapperExtension, EXT_PASS
from elixir.statements import Statement

import sys
import types


class EventMapperExtension(MapperExtension):
    def __init__(self):
        self.decorated_methods = set()
    
    def handle_event(self, event, instance):
        for item in instance.__class__.__dict__.values():
            if type(item) == types.FunctionType:
                if item in self.decorated_methods:
                    if event in item.events:
                        item(instance)
    
    def before_insert(self, mapper, connection, instance):
        self.handle_event('before_insert', instance)
        return EXT_PASS
        
    def before_update(self, mapper, connection, instance):
        self.handle_event('before_update', instance)
        return EXT_PASS
        
    def after_update(self, mapper, connection, instance):
        self.handle_event('after_update', instance)
        return EXT_PASS
        
    def after_insert(self, mapper, connection, instance):
        self.handle_event('after_insert', instance)
        return EXT_PASS
        
    def before_delete(self, mapper, connection, instance):
        self.handle_event('before_delete', instance)
        return EXT_PASS
        
    def after_delete(self, mapper, connection, instance):
        self.handle_event('after_delete', instance)
        return EXT_PASS


event_mapper_extension = EventMapperExtension()


class RespondsToEvents(object):
        
    def __init__(self, entity, for_fields=[], with_secret='abcdef'):
        # first, make sure that the entity's mapper has our mapper extension
        extensions = entity._descriptor.mapper_options.get('extension', [])
        if type(extensions) is not types.ListType:
            extensions = [extensions]
        if event_mapper_extension not in extensions:
            extensions.append(event_mapper_extension)
            entity._descriptor.mapper_options['extension'] = extensions

responds_to_events = Statement(RespondsToEvents)


def create_decorator(event_name):
    def decorator(func):
        event_mapper_extension.decorated_methods.add(func)
        if not hasattr(func, 'events'):
            func.events = []
        func.events.append(event_name)
        return func
    return decorator


before_insert = create_decorator('before_insert')
before_update = create_decorator('before_update')
after_update  = create_decorator('after_update')
after_insert  = create_decorator('after_insert')
before_delete = create_decorator('before_delete')
after_delete  = create_decorator('after_delete')
