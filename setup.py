#!/usr/bin/env python3
from setuptools import setup
from phuey.phuey import __version__


setup(name='phuey',
      version=__version__,
      author='Adam Garcia',
      author_email='garciadam@gmail.com',
      url='https://github.com/pancho-villa/Phuey',
      license='MIT',
      description='A python library to control Philips™ Hue Devices',
      packages=['phuey'],
      classifiers=['Development Status :: 5 - Production/Stable',
                   'Intended Audience :: Developers',
                   'Topic :: Software Development :: Home Automation',
                   'License :: OSI Approved :: MIT License',
                   'Programming Language :: Python :: 2.7',
                   'Programming Language :: Python :: 3',
                   'Programming Language :: Python :: 3.2',
                   'Programming Language :: Python :: 3.3',
                   'Programming Language :: Python :: 3.4',
                   'Programming Language :: Python :: 3.5',
                   ],
      keywords = 'development, automation',
      )
