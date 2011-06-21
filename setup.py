#!/usr/bin/env python

#from distutils.core import setup
from setuptools import setup

setup(name='gepdb',
      version='0.1rc1',
      description='Graphical user interface for epdb',
      author='Patrick Sabin',
      package_data = {
          'gepdb': ['bug.png', 'breakpoint.png']},
      author_email='patricksabin@gmx.at',
      url='http://code.google.com/p/epdb/',
      packages=['gepdb'],
      scripts = ['bin/gepdb'],
     )

