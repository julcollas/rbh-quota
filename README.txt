I   - Introduction
II  - Compiling
III - Robinhood setup


I - Introduction
================

Using the robinhood MySQL database and a Lustre filesystem,
rbh-quota provides a new table 'QUOTA' to the database and stores
the quotas foreach users in it.
This table can be used to visualize the quotas through
robinhood's web interface from this fork : https://github.com/LiquidSame/robinhood

II - Compiling
==============

2.1 - From source tarball
-------------------------

It is advised to build rbh-quota on your target system,
to ensure the best compatibility with your Lustre and MySQL versions.

Build requirements: python, mysql-python, pip

Unzip and untar the source distribution:
> tar xzvf rbh-quota-0.x.x.tar.gz
> cd rbh-quota-0.x.x

Build:
> python setup.py sdist
> pip install dist/rbh-quota-0.x.x.tar.gz

Compiled package is generated in the 'dist/' directory.
rbh-quota is now an available command.

2.2 - From git repository
-------------------------

# Install git and autotools stuff:
> yum install git automake autoconf libtool

# Retrieve rbh-quota sources:
> git clone https://github.com/LiquidSame/rbh-quota.git
> cd rbh-quota
> git checkout master (or other branch)

Then refer to section 2.1 for next compilation steps.

III - Robinhood setup
====================

In order to use rbh-quota, your filesystem needs to run
Robinhood-3.x, an open-source software available here :
    https://github.com/cea-hpc/robinhood.git

It is best to use the changelog reader with robinhood.
# On your MDT
lfs changelog_register <device>

# Save the changelog reader id to your robinhood conf.file
# Make sure to have the '--readlog' option for your daemon

IV - First run
===============

Even if your filesystem is empty, you need to perform an initial scan
in order to initialize robinhood database.
This prevents from having entries in filesystem that it wouldn't know about.
robinhood --scan --once

# create a conf.file for rbh-quota (see 'V - Configuration file')
vim ~/.rbh-quota.ini
# or execute it with arguments (see 'rbh-quota --help')
rbh-quota -u robinhood -h localhost

A table 'QUOTA' will be created on the chosen database
or an error will be issued.

V - Configuration file
======================

template for '~/.rbh-quota.ini' :

[rbh-quota_api]
db_host = ...
db_user = robinhood
db_pwd = ...
db = robinhood_...
alerts = True/False
domain = ...
smtp_server = ...
sender = ...
webHost = ...
