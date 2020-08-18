#!/usr/bin/env python3

# -*- coding: utf-8 -*-

import os
import re
import sys
from setuptools import find_packages, setup

with open('version') as f:
    __version__ = f.read().strip()
    __version__ = re.sub('^[vV]|\-\w{8}$', '', __version__)

if sys.argv[1] == 'version':
    print(__version__)
    sys.exit(0)

requirements = '''
jinja2==2.11.*
pyyaml==5.3.*
setproctitle
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
        packages         = find_packages(),
        scripts          = [ 'bin/inji' ],
        install_requires = requirements,
        include_package_data = True,
        zip_safe         = False,
        python_requires  = '>=3.5',
        long_description = long_description,
        long_description_content_type = 'text/markdown',
        keywords         = [ 'jinja', 'jinja2', 'templating' ],
        classifiers=[
            'Development Status :: 4 - Beta',
            'Environment :: Console',
            'Intended Audience :: Developers',
            'Intended Audience :: System Administrators',
            'License :: OSI Approved :: Apache Software License',
            'Operating System :: OS Independent',
            'Programming Language :: Python :: 3',
            'Topic :: Software Development',
            'Topic :: System :: Systems Administration'
        ]
    )
