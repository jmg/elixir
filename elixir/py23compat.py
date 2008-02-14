# Some helper functions to get by without Python 2.4

# set
try:
    set = set
except NameError:
    from sets import Set as set

# sorted
try:
    sorted = sorted
except NameError:
    # global name 'sorted' doesn't exist in Python2.3
    # this provides a poor-man's emulation of the sorted built-in method
    def sorted(l, kwargs):
        if 'key' not in kwargs:
            raise Exception('Our python 2.3 version of sorted needs a key kwarg argument')
        key_func = kwargs['key']
        sorted_list = list(l)
        sorted_list.sort(lambda self, other: cmp(key_func(self),
                                                 key_func(other)))
        return sorted_list

# rsplit
try:
    ''.rsplit
    def rsplit(s, delim, maxsplit):
        return s.rsplit(delim, maxsplit)

except AttributeError:
    def rsplit(s, delim, maxsplit):
        """Return a list of the words of the string s, scanning s
        from the end. To all intents and purposes, the resulting
        list of words is the same as returned by split(), except
        when the optional third argument maxsplit is explicitly
        specified and nonzero. When maxsplit is nonzero, at most
        maxsplit number of splits - the rightmost ones - occur,
        and the remainder of the string is returned as the first
        element of the list (thus, the list will have at most
        maxsplit+1 elements). New in version 2.4.
        >>> rsplit('foo.bar.baz', '.', 0)
        ['foo.bar.baz']
        >>> rsplit('foo.bar.baz', '.', 1)
        ['foo.bar', 'baz']
        >>> rsplit('foo.bar.baz', '.', 2)
        ['foo', 'bar', 'baz']
        >>> rsplit('foo.bar.baz', '.', 99)
        ['foo', 'bar', 'baz']
        """
        assert maxsplit >= 0
        
        if maxsplit == 0: return [s]
        
        # the following lines perform the function, but inefficiently.
        #  This may be adequate for compatibility purposes
        items = s.split(delim)
        if maxsplit < len(items):
            items[:-maxsplit] = [delim.join(items[:-maxsplit])]
        return items
