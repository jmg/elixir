classifiers = """
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Topic :: Database :: Front-Ends",
    "Topic :: Software Development :: Libraries :: Python Modules"
"""

from setuptools import setup, find_packages

setup(name="Elixir",
      version="0.0.1",
      description="Declarative Mapper for SQLAlchemy",
      author="",
      author_email="",
      url="http://supermodel.ematia.de",
      install_requires = [
          "SQLAlchemy >= 0.3.0"
      ],
      packages=['elixir',
                'elixir.tests'],
      classifiers=classifiers,
      test_suite = 'nose.collector')
