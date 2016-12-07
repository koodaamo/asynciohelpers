from setuptools import setup, find_packages
import sys, os

version = '0.3rc0'

setup(name='asynciohelpers',
      version=version,
      description="Helpers for writing asyncio-based apps",
      long_description="",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='asyncio',
      author='Petri Savolainen',
      author_email='petri.savolainen@koodaamo.fi',
      url='',
      license='GPL',
      packages=find_packages(exclude=['ez_setup', 'tests']),
      include_package_data=True,
      zip_safe=False,
      setup_requires=['pytest-runner',],
      tests_require=['pytest', 'pytest-logging', 'pytest-asyncio'],
      install_requires=[
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
