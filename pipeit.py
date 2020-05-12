import builtins
import functools
import itertools

from functools import wraps

# NOTE: This will be added to below.
__all__ = ['pipe', 'pipe0', 'pipestar']

# Is a single-arg version (which you'd compose with partial) useful?
# The nice thing is, calling and piping would be the same operation.
# And together with a full suite of Haskell-y helpers (compose, but also
# flip, roll, etc.), you could write all of the examples below as
# single-arg-pipeable. But it would be inefficient and a lot less
# Pythonic-looking. So probably you don't want that.
# def pipe1(func):
#     @wraps(func, updated=())
#     class Wrapper:
#         def __call__(self, *args, **kwargs):
#             return func(*args, **kwargs)
#         def __ror__(self, arg):
#             return func(arg)
#     return Wrapper()

# TODO: For single-arg functions, having to do xs | preversed() instead
#       of xs | preversed is annoying. We could, instead of returning an
#       class that you then call to get an instance that takes __ror__,
#       return an instance of a class that you can either directly __ror__
#       or __call__ to partial in arguments. Is that worth it?
def pipe(func):
    """xs | pipe(func)(a, b, c=d) = func(a, b, xs, c=d)
    
    Typically used as a decorator, and typically both xs and the return
    value are iterables, but this isn't required.
    
    >>> @pipe
    ... def add_if_less(n, xs):
    ...     return sum(x for x in xs if x<n)
    >>> range(10) | add_if_less(6)
    15
    
    This can also be used to wrap existing functions like map, filter,
    and most of itertools and more-itertools:
    
    >>> pfilter, pmap, plist = pipe(filter), pipe(map), pipe(list)
    >>> range(10) | pfilter(lambda x: x%2) | pmap(lambda x: x+1) | plist()
    [2, 4, 6, 8, 10]

    A few functions take their iterable or other usefully-pipeable argument
    first rather than last. For these, use pipe0.
    """
    # TODO: wrap Wrapper?
    class Wrapper:
        __slots__ = ('args', 'kwargs')
        def __new__(cls, args, kwargs):
            self = super(Wrapper, cls).__new__(cls)
            self.args = args
            self.kwargs = kwargs
            return self
        def __ror__(self, arg):
            return func(*self.args, arg, **self.kwargs)
    @wraps(func)
    def wrapper(*args, **kwargs):
        return Wrapper(args, kwargs)
    return wrapper

def pipe0(func):
    """xs | pipe0(func)(a, b, c=d) = func(xs, a, b, c=d)
    
    Typically used as a decorator, and typically both xs and the return
    value are iterables, but this isn't required. Most functions take
    their iterable or other usefully-pipeable argument last rather than
    first; for these, use pipe rather than pipe0.
    
    >>> @pipe0
    ... def add_if_less(xs, n):
    ...     return sum(x for x in xs if x<n)
    >>> range(10) | add_if_less(6)
    15
    """
    # TODO: wrap Wrapper?
    class Wrapper:
        __slots__ = ('args', 'kwargs')
        def __new__(cls, args, kwargs):
            self = super(Wrapper, cls).__new__(cls)
            self.args = args
            self.kwargs = kwargs
            return self
        def __ror__(self, arg):
            return func(*self.args, arg, **self.kwargs)
    @wraps(func)
    def wrapper(*args, **kwargs):
        return Wrapper(args, kwargs)
    return wrapper

def pipestar(func):
    """xs | pipestar(func)(a, b, c=d) = func(a, b, *xs, c=d)
    
    Typically used as a decorator. xs must be an iterable. In most
    cases you want to pass the iterable as an argument rather than
    unpacking it; use pipe for that. But this does have occasional
    uses.
    """
    # TODO: wrap Wrapper?
    class Wrapper:
        __slots__ = ('args', 'kwargs')
        def __new__(cls, args, kwargs):
            self = super(Wrapper, cls).__new__(cls)
            self.args = args
            self.kwargs = kwargs
            return self
        def __ror__(self, arg):
            return func(*self.args, *arg, **self.kwargs)
    @wraps(func)
    def wrapper(*args, **kwargs):
        return Wrapper(args, kwargs)
    return wrapper

_g = globals()
for name in ('all any dict enumerate filter len list min map max '
             'reversed set sum tuple zip').split():
    _g[name] = _g['p'+name] = pipe(getattr(builtins, name))
    __all__.append('p'+name)
for name in 'print'.split():
    _g[name] = _g['p'+name] = pipestar(getattr(builtins, name))
    __all__.append('p'+name)
_g['join'] = _g['pjoin'] = pipe(str.join)
__all__.append('pjoin')
for name in ('accumulate chain compress cycle dropwhile filterfalse groupby '
             'product repeat starmap takewhile tee zip_longest').split():
    _g[name] = _g['p'+name] = pipe(getattr(itertools, name))
    __all__.append('p'+name)
# NOTE: reduce takes its iterable in the middle. If you want to use it
#       with an initial value, you have to pass it as a keyword argument.
for name in 'reduce'.split():
    _g[name] = _g['p'+name] = pipe(getattr(functools, name))
    __all__.append('p'+name)

del _g
    
def test():
    from builtins import print
    print(pfilter(lambda x: x%2))
    print(range(10) | pfilter(lambda x: x%2))
    print(range(10) | pfilter(lambda x: x%2) | pmap(lambda x: x*2) | plist())

    import re
    ('abc def bab qqq'.split()
         | preversed()
         | pfilter(re.compile('a').search)
         | pprint())

if __name__ == '__main__':
    test()
