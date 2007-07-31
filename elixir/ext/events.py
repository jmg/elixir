from sqlalchemy.orm.mapper import MapperExtension
from elixir.statements import Statement

import inspect

class RespondsToEvents(object):
        
    def __init__(self, entity):
        # create a list of callbacks for each event
        methods = {}
        for name, func in inspect.getmembers(entity, inspect.ismethod):
            if hasattr(func, '_elixir_events'):
                for event in func._elixir_events:
                    event_methods = methods.setdefault(event, [])
                    event_methods.append(func)

        if not methods:
            return
        
        # transform that list into methods themselves
        for event in methods:
            methods[event] = self.make_proxy_method(methods[event])

        # create a custom mapper extension class, tailored to our entity
        ext = type('EventMapperExtension', (MapperExtension,), methods)()

        # then, make sure that the entity's mapper has our mapper extension
        extensions = entity._descriptor.mapper_options.get('extension', [])
        if not isinstance(extensions, list):
            extensions = [extensions]
        extensions.append(ext)
        entity._descriptor.mapper_options['extension'] = extensions

    def make_proxy_method(self, methods):
        def proxy_method(self, mapper, connection, instance):
            for func in methods:
                func(instance)
        return proxy_method

responds_to_events = Statement(RespondsToEvents)


def create_decorator(event_name):
    def decorator(func):
        if not hasattr(func, '_elixir_events'):
            func._elixir_events = []
        func._elixir_events.append(event_name)
        return func
    return decorator


before_insert = create_decorator('before_insert')
after_insert = create_decorator('after_insert')
before_update = create_decorator('before_update')
after_update = create_decorator('after_update')
before_delete = create_decorator('before_delete')
after_delete = create_decorator('after_delete')
