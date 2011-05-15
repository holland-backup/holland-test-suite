Intro
=====

This package intends to provide integration tests for holland.  The basic
approach here is to do the following:

* Provide a set of MySQL binary distribution tarballs for each MySQL version to
  test 
* Setup a sandbox directory under ${sandbox_root}
* Run holland commands against this MySQL version by setting MYSQL_HOME to point
  to the correct MySQL installation and holland's [mysql:client] will pick that
  up via defaults-extra-files = .my.cnf

Configuration
=============
Tests are parameterized via nose-testconfig.  

Running
=======

To run the tests you should first run scripts/mkvirtualenv.py in the main holland repo

Install nose-testconfig

# pip install --upgrade nose-testconfig

Make sure you're using the current nosetests from the virtualenv:

# set +h

(or # rehash in zsh)

Run the test suite:

# nosetests --tc-file=config.ini

This will unpack the mysql versions specified in the config.ini and run the tests
in test.py

Each test in test.py just run holland backup (with or without --dry-run) against a 
config in holland.conf.d/

