#!/usr/bin/env python3

# -*- coding: utf-8 -*-

import os
import sys
from setuptools import setup

with open('version') as f:
    __version__ = f.read().strip()

if sys.argv[1] == 'version':
    print(__version__)
    sys.exit(0)

requirements = '''
jinja2==2.11.*
pyyaml==5.3.*
'''.strip().split('\n')

if sys.argv[1] == 'requirements':
    print('\n'.join(requirements))
    sys.exit(0)

setup(  name             = 'inji',
        version          = '0.1',
        description      = "Render Jinja2 templates",
        url              = 'https://github.com/shalomb/inji',
        author           = 'Shalom Bhooshi',
        author_email     = 's.bhooshi@gmail.com',
        license          = 'Apache License 2.0',
        packages         = ['inji'],
        zip_safe         = False,
        scripts          = ['inji/inji'],
        install_requires = requirements
    )
