#!/bin/bash

PS1="# "

VIRTUALENV_NAME='holland_test'

virtualenv --no-site-packages ${VIRTUALENV_NAME}

. ./${VIRTUALENV_NAME}/bin/activate

pip install nose nose-testconfig

$SHELL
