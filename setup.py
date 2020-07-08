#!/usr/bin/env python3

# -*- coding: utf-8 -*-

import os
import re
import sys
from setuptools import setup

with open('version') as f:
    __version__ = f.read().strip()
    __version__ = re.sub('^[vV]', '', __version__)

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

with open('README.md', 'r') as fh:
    long_description = fh.read()

setup(  name             = 'inji',
        version          = __version__,
        description      = 'Render parameterized Jinja2 template files',
        url              = 'https://github.com/shalomb/inji',
        author           = 'Shalom Bhooshi',
        author_email     = 's.bhooshi@gmail.com',
        license          = 'Apache License 2.0',
        packages         = ['inji'],
        zip_safe         = False,
        scripts          = ['inji/inji'],
        install_requires = requirements,
        python_requires  = '>=3.5',
        long_description = long_description,
        long_description_content_type = 'text/markdown',
        classifiers=[
            'Programming Language :: Python :: 3',
            'Operating System :: OS Independent',
            'Environment :: Console',
            'Intended Audience :: System Administrators',
            'License :: OSI Approved :: Apache Software License',
            'Topic :: System :: Systems Administration'
        ]
    )
