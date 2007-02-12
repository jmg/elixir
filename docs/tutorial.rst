========
Tutorial
========

.. CHECKME: this is not rendered?

---------
Diving in
---------

1. Installation
---------------
        
In this tutorial, we will show you how to create a small and simple model. 
Before we start please make sure that you already have the Elixir package 
installed. If not, do so by typing [#]_:
 
 ::
 
     easy_install Elixir
 
 .. [#] If you don't even have "``easy_install``" yet, please visit the
        `EasyInstall website
        <http://peak.telecommunity.com/DevCenter/EasyInstall>`_ first and find
        out how to use it (it's pretty easy, like the name promises).

2. A very simple model
----------------------

Now fire up your favorite text editor and create a file "``model.py``"
containing the following lines:

::

    from elixir import *

    metadata.connect("sqlite:///movies.sqlite")

    class Movie(Entity):
        with_fields(
            title = Field(Unicode(30)),
            year = Field(Integer),
            description = Field(Unicode)
        )
        
        def __repr__(self):
            return '<Movie "%s" (%d)>' % (self.title, self.year)


What does this snippet do? First of all it connects to an SQLite-database
[#]_. Then it declares a ``Movie``-entity (ie. a class, that inherits Elixir's
``Entity``-baseclass). This entity will hold three fields:

- ``title``: holds up to 30 unicode chars, which represent the movie's title
- ``year``:  an integer containing the year the movie was released
- ``description``: this could be a plot summary, a review, or any long string
  of text that you like.

The ``__repr__()``-method below is totally unrelated to Elixir, it just tells
the python interpreter to print objects in a human-readable way. It's nice to
have, but fully optional.  We have put this into our model so that we can 
easily trace what is happening in an interactive python interpreter.

Also, please note that elixir currently provide two different ways to declare
the fields on your entities. We have not decided yet on which one we like best,
or if we will always keep both. The other way to declare your fields is using
the ``has_field`` statement, rather than the ``with_fields`` statement.  The
``Movie`` example above can be declared using the ``has_field`` statement like
so:

::

    from elixir import *

    metadata.connect("sqlite:///movies.sqlite")

    class Movie(Entity):
        has_field('title', Unicode(30))
        has_field('year', Integer)
        has_field('description', Unicode)
        
        def __repr__(self):
            return '<Movie "%s" (%d)>' % (self.title, self.year)


If you have a strong preference for one syntax over the other, please let us
know so that we can make a good decision before our final stable release!


.. [#] This assumes you have `pysqlite <http://pysqlite.org/>`_
       installed. You may use any other database instead, as long as it's
       `supported by SQLAlchemy <http://www.sqlalchemy.org/features.myt>`_.


3. Action!
----------

What time is it? It's database-table-creation-time! Fire up your python
interpreter of choice (preferably `IPython <http://ipython.scipy.org/>`_) and
hack in the lines below [#]_ (only lines starting with "``>>>``", of course):

::

    >>> from model import *
    >>> create_all()
    >>> Movie(title="Blade Runner", year=1982)
    <Movie "Blade Runner" (1982)>
    
You've created all necessary tables by executing ``create_all()`` and then
instantiated a first movie-object. You could add more movies here, but so far
"Blade Runner" does the job.

Because SQLAlchemy tries to do as many operations as possible in one single
operation (a so called `Unit of Work`), which is very efficient, the data has
not been written to the database table yet. You can tell SQLAlchemy to do so
by typing:

::

    >>> objectstore.flush()

This will tell SQLAlchemy to generate all of the SQL to insert the Movie into
the database, and then execute that SQL. Now, to see a list of all the movies 
in our database, simply type:

::

    >>> Movie.select()
    [<Movie "Blade Runner" (1982)>]

Not many, but exactly what we expected. Close the interpreter now and delete
[#]_ the database file (``movies.sqlite``), we will recreate and populate it
in the next step.
    
.. [#] Make sure, you're running your interpreter from the directory where you
       saved the ``model.py`` file.
.. [#] If you're using any other DBMS than SQLite, just drop the created table
       (most probably something like ``DROP TABLE model_movie;``).

4. Relationships
----------------

So far you've seen how to declare simple entities, create objects, store them
to the database and retrieve them again. Not too much magic, but a lot more 
pleasant to the eye compared to calling lowlevel SQL-statements.

Now we will do something more advanced. Movies need genres, so we'll add a new
entity "``Genre``" to our ``model.py``:

::

    class Genre(Entity):
        with_fields(
            name = Field(Unicode(15), unique=True)
        )
        
        def __repr__(self):
            return '<Genre "%s">' % self.name

The ``__repr__()``-method is totally optional, again. We're limiting the
length of our genres to 15 characters and demand that those names are
unique. There's no use in having two genres with the same name, right?

We could start the interpreter again and instantiate some genres, but before
we do that, we want to tell Elixir how to relate movies and genres to add more
excitement. Add two lines to your ``model.py``, so it reads:

::

    class Movie(Entity):
        with_fields(
            title = Field(Unicode(30)),
            year = Field(Integer),
            description = Field(Unicode)
        )
        
        belongs_to('genre', of_kind='Genre')                # add this line
    
        def __repr__(self):
            return '<Movie "%s" (%d)>' % (self.title, self.year)
    
    
    class Genre(Entity):
        with_fields(
            name = Field(Unicode(15))
        )
        
        has_many('movies', of_kind='Movie')                 # and this one
        
        def __repr__(self):
            return '<Genre "%s">' % self.name

A movie belongs to a genre and a genre may have many movies, that's what it
says. We could let movies have multiple genres by changing the ``belongs_to``-
and ``has_many``-statements in both lines to ``has_and_belongs_to_many``, but
one genre per movie is enough for our example.

Again, start your python interpreter, ensure that the old database table has
been deleted, and then create your new model's tables:

::
    
    >>> from model import *
    >>> create_all()

Create a genre and a couple of titles:

::

    >>> scifi = Genre(name="Science-Fiction")
    >>> alien = Movie(title="Alien", year=1979)
    >>> starwars = Movie(title="Star Wars", year=1977)
    >>> brunner = Movie(title="Blade Runner", year=1982)

Now add the movies to the genre (just like you'd do if it was a plain old
python list), and flush the objectstore:

::

    >>> scifi.movies.append(alien)
    >>> scifi.movies.append(starwars)
    >>> scifi.movies.append(brunner)
    >>> objectstore.flush()

Let's demonstrate some magic now, enter these two lines:

::

    >>> m = Movie.get_by(title="Alien")
    >>> m.title, m.genre
    ('Alien', <Genre "Science-Fiction">)
    
As you can see, all the dirty work has been done for you - automatically and
out of your way. Primary [#]_ and foreign keys have been generated
automatically, and if you'd used ``has_and_belongs_to_many``, even the
necessary secondary tables.

.. [#] If you don't specify any primary keys by passing ``primary_key=True``
       as a keyword-argument to the ``Field()``-construct, Elixir will
       automatically create one for you, which will then be accessible under
       the name ``id``.


5. Where to go from here?
-------------------------

You have created a simple model with some entities and set up some
relationships between them. Now that you've seen how it basically works, take
a closer look at Elixir's `API-docs <module-index.html>`_, `examples
<examples.html>`_ and `testcases
<http://elixir.ematia.de/svn/elixir/trunk/tests/>`_, which come with the
source distribution, and see how to create other types of relationships and
fine tweak Elixir's options to your liking.

To learn more about the available datatypes, how to retrieve and modify data
and about lower level features please consult `SQLAlchemy's detailed
documentation <http://www.sqlalchemy.org/docs/>`_.

Enjoy database development the easy way and let us know when you created
something cool!



