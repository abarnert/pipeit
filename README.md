# pipeit
Pipe the iterable (or other key argument) to a function

# Use

Don't. At least at present--but most likely forever--this library is just here
for me to play with different ways of implementing pipe syntax, not to
actually use in real-life code.

There are a bunch of similar libraries on PyPI, one of which probably does
what you want, and is actually tested and maintained. I don't know any of
them all that well, but here are some I've heard mentioned:

 * pipe
 * pipe-tool
 * pipetools
 * pipeop
 * pipey
 * grapevine

Also, if you're using Pandas:

 * dfply
 * pandas-ply
 * sspipe

# Experiment

`pipeit` provides three wrappers to allow piping in the last argument
(`pipe`), the first argument (`pipe0`), or all arguments (`pipestar`). The
first one is useful the most often:

    >>> @pipe
    ... def add_if_less(n, xs):
    ...     return sum(x for x in xs if x<n)
    >>> range(10) | add_if_less(6)
    15

So, why is this better than the usual Python way, like this:

    >>> def add_if_less(n, xs);
    ...     return sum(x for x in xs if x<n)
    >>> add_if_less(6, range(10))
    15

Well, in this case, it isn't. But the advantage comes when you chain
together a bunch of pipes into a pipeline.

Many things you're likely to want to pipe are already builtin, or in
itertools, or third-party libraries like more-itertools, so you'll probably
use the wrapper as a wrapper more often than as a decorator. Except
that the module already has wrappers for most of the useful stuff that
comes with Python, so you may not even do that.

Typically, any function that takes an iterable as its last argument and
returns an iterable is a good candidate for being in the middle of a
pipeline (and any function that takes an iterable as its last argument
but doesn't return one is still a good candidate for being the tail end of
a pipeline).

For example, you could rewrite the above as:

    >>> range(10) | pfilter(lambda x: x<6) | sum()
    15

Notice that when there are no extra arguments, you still need to call the
pipe function to get a pipeable thing. I'm not yet sure whether this is
annoying or nice. (Consider the fact that Python requires parens for normal
function calls, which at first seems annoying compared to, say, Ruby, but
turns out to have a lot of advantages.)

Here's another example:

    >>> ('abc def bab qqq'.split()
    ...      | preversed()
    ...      | pfilter(re.compile('a').search)
    ...      | pprint(sep='-'))
    bab-abc

... which is equivalent to:

    >>> print(*filter(re.compile('a').search,
    ...               reversed('abc def bab qqq'.split())),
    ...       sep='-')
    
(Notice that `pprint` is one of the few useful cases for `pipestar` rather
than `pipe`.)

Or, if you want to return the joined-up string rather than print it:

    >>> ('abc def bab qqq'.split()
    ...      | preversed()
    ...      | pfilter(re.compile('a').search)
    ...      | pjoin('-'))
    bab-abc

... as opposed to:

    >>> '-'.join(filter(re.compile('a').search,
    ...                 reversed('abc def bab qqq'.split())))

The pipe version makes it clear what order things are happening in.
We're talking an iterable and passing it through one pipe after another.

But of course you can write the same thing in proper order today:

    >>> words = 'abc def bab qqq'.split()
    >>> revwords = reversed(words)
    >>> awords = filter(re.compile('a'), revwords)
    >>> result = '-'.join(awords)

This has the advantage and the disadvantage that each step is a statement.
That means you get the nice Python statement layout rather than relying on
ad-hoc indenting of a complex expression, you can stick in a debugger
breakpoint (or `tuple` and `print` or `log` or whatever) to see what's
happening at any point, etc. But it also means it's more verbose, and you
have to name each step (nothing's stopping you from calling them all `xs`
or whatever, but it does smell weird if you do).

The performance is fine either way. The only overhead is the tiny constant
cost at setup time. Is the extra operator call cheaper or more expensive
than the extra local variable loads and stores? Probably cheaper, but I
can't imagne a case where you'd care enough to test.

The traditional way also lets you use functions without having to wrap them
up. As you can see from the source, wrapping up and re-exporting everything
relevant from `itertools` isn't exactly difficult, so if you wanted to do the
same for, say, `more-itertools`, you could. In fact, you could do it totally
dynamically and just wrap everything in the module (and the ones that don't
make sense, as long as you don't call them, that's fine).

This also means you can use generator expressions. In many cases, they're
a lot more readable than `map` and `filter` calls. Not so much in this
case, because we can filter on a bound method:

    >>> awords = (re.match('a', word) for word in words)
    >>> awords = filter(re.compile('a').match, words)

... but when you can't do that it's much nicer:

    >>> odds = (x for x in xs if x%2)
    >>> odds = filter(lambda x: x%2, xs)

# Implementation and Extensions

The quick&dirty idea is that you want an object that's just like a
function but calls its call operator `__ror__` instead of `__call__`.
However, to be useful in most cases, this has to be put together with
something like `partial`.

Why? If you want to think of it in Haskell terms, notice that a Python
`Iterable` is already a Haskell `Producer` (it's a thing that `for` wants,
and you can write it with a function that `yield`s...), and things like 
`sum` are `Consumer`s. The only reason piping isn't as trivial in Python
as in Haskell is that `map f xs` is curried, so `map f` is a `Pipe`, 
usable as-is, while `map(f, xs)` is not curried, so `map(f)` is just a
`TypeError`. Writing `partial(map, f)` is a pain, so you either need a 
currying library like the one that comes with `toolz`, or you need to 
write a wrapper that explicitly does the partialing while wrapping.
Which is pretty simple, and that's what I did.

And that's all the tricks there are: There wrapper is a `class` that 
stashes its arguments at call (construction) time like `partial`, but
it has an `__ror__` method instead of a `__call__` method.

Well, there is one other minor trick buried in the pre-wrapped
functions: an unbound method like `str.join` that takes `self` and an
iterable is a perfectly good wrappable function, where you bind in the
`self` at construction time and then pipe in the iterable.

It might be worth adding more tricks for, e.g., making pipes that can be 
constructed with no args, or that can be called as well as piped (like a 
`partial`), or that can bind args in at the `pipe` call instead of in a 
separate call. I'm not sure if any of those are good things to have or not.

You could also implement `__or__` to allow throwing regular functions into
the pipeline, as long as there's at least one wrapped function to get in
the way. Except that only works if the unwrapped functions don't take any
additional arguments. (PyMacro could help here, but if you're using that,
you don't need runtime tricks; just use all regular functions and macro
up the pipes into calls.) So I'm not sure if it's worth it. Maybe `print`
is a special enough case to be special?
