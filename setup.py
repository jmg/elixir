from setuptools import setup, find_packages

setup(name="Elixir",
      version="0.2.0",
      description="Declarative Mapper for SQLAlchemy",
      long_description="""
Elixir
======

A declarative layer on top of SQLAlchemy. It is a fairly thin wrapper, which 
provides the ability to define model objects following the Active Record 
design pattern, and using a DSL syntax similar to that of the Ruby on Rails 
ActiveRecord system.

Elixir does not intend to replace SQLAlchemy's core features, but instead 
focuses on providing a simpler syntax for defining model objects when you do
not need the full expressiveness of SQLAlchemy's manual mapper definitions.

Elixir is intended to replace the ActiveMapper SQLAlchemy extension, and the 
TurboEntity project.  
""",
      author="Gaetan de Menten, Daniel Haus and Jonathan LaCour",
      author_email="sqlelixir@googlegroups.com",
      url="http://elixir.ematia.de",
      license = "MIT License",
      install_requires = [
          "SQLAlchemy >= 0.3.0"
      ],
      packages=['elixir'],
      classifiers=[
          "Development Status :: 4 - Beta",
          "Intended Audience :: Developers",
          "License :: OSI Approved :: MIT License",
          "Operating System :: OS Independent",
          "Programming Language :: Python",
          "Topic :: Database :: Front-Ends",
          "Topic :: Software Development :: Libraries :: Python Modules"
      ],
      extras_require = {
        'pudge': ["docutils>=0.4", "elementtree>=1.2.6", "kid>=0.9", 
                  "Pygments==dev,>=0.7dev-r2661", "pudge==dev,>=0.1.3dev-r134", 
                  "buildutils==dev,>=0.1.2dev-r109",],
      },
      test_suite = 'nose.collector')
