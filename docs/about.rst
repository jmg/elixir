=====
About
=====

-------
History
-------

In 2006, `Jonathan LaCour <http://cleverdevil.org>`_ discovered the fantastic
`SQLAlchemy <http://sqlalchemy.org>`_ project, and really liked its power and
flexibility, but found that in many simple cases he would prefer a simpler and
more attractive way to declare his model objects.  As a result, Jonathan spent
a few hours on a weekend to create the `ActiveMapper
<http://cleverdevil.org/computing/35/>`_ SQLAlchemy extension. For a weekend's
worth of work, it wasn't half bad, and gained a little bit of traction in the
wild.  But, over time, it became clear that ActiveMapper needed a lot of work
to stabilize and become more useful.

Later that year, `Daniel Haus <http://www.ematia.de>`_ released his own layer
on top of SQLAlchemy, called `TurboEntity <http://turboentity.ematia.de>`_. 
TurboEntity solved some of the problems of ActiveMapper, and took a slightly
different approach to the problem.  TurboEntity also began to gain some ground
and it became clear to both Daniel and Jonathan that they needed to work
together.

Around the same time, Gaëtan de Menten contacted both Jonathan and Daniel to
reveal that he had been working on his own layer as well.  A few weeks later,
all three agreed to work together to create a replacement for TurboEntity and
ActiveMapper using their collective experience and knowledge.


--------
The Name
--------

The Oxford English Dictionary defines Elixir as: "a magical or medicinal potion,
a preparation that was supposedly able to change metals into gold, sought by 
alchemists."


----------
The Future
----------

The eventual goal of the Elixir project is to become an official SQLAlchemy
extension.  But, before we submit elixir for inclusion within SQLAlchemy, we
want the opportunity to solicit feedback and contributions from users to make
sure that we have ironed out any bugs, missing features, syntax changes, or
documentation deficiencies.

The primary things we would like to resolve before we make our first stable
and official release are:

- TODO