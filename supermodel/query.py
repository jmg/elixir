from supermodel.statements import Statement
from sqlalchemy import select, and_


class Query(object):
    __selects__     = None
    __where__       = None
    __group_by__    = None
    __order_by__    = None
    
    class __metaclass__(type):
        def __init__(cls, name, bases, dict_):
            Statement.process(cls)
    
    def __init__(self, *args):
        where = list(args)
        if self.__where__: where.extend(self.__where__)
        if len(where) == 1: where = where[0]
        elif len(where) > 1: where = and_(*where)
        else: where = None
        
        self.where = where
        self.selects = self.__selects__
        self.groupby = self.__group_by__
        self.orderby = self.__order_by__
    
    def __iter__(self):
        results = select(self.selects, self.where, 
                         group_by=self.groupby, order_by=self.orderby)
        for result in results.execute():
            yield result


class Selects(object):
    def __init__(self, target, *args):
        target.__selects__ = args

class Where(object):
    def __init__(self, target, *args):
        target.__where__ = args

class GroupBy(object):
    def __init__(self, target, *args):
        target.__group_by__ = args

class OrderBy(object):
    def __init__(self, target, *args):
        target.__order_by__ = args


selects = Statement(Selects)
where = Statement(Where)
grouped_by = Statement(GroupBy)
ordered_by = Statement(OrderBy)