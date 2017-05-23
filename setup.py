#! /usr/bin/env python

from setuptools import setup, find_packages

# Extracts the __version__
VERSION = [
    l for l in open('rbh_quota/__init__.py').readlines()
    if l.startswith('__version__ = ')
][0].split("'")[1]

setup(
    name='rbh-quota',
    version=VERSION,
    packages=find_packages(),
    description='rbh plugin to add QUOTA table in MySQL database',
    keywords='rbh robinhood quota database',
    author='Sami BOUCENNA',
    author_email='liquid.same@gmail.fr',
    entry_points={'console_scripts': ['rbh-quota = rbh_quota.rbhQuota:insert']},
    install_requires=['MySQL-python'],
)
