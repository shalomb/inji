#!/usr/bin/env python3

# -*- coding: utf-8 -*-

import os
import re
import sys
import setuptools
import distutils.cmd

# Suppress setup.py's stdout logging for our commands that output data
if any( x in ['requirements', 'version'] for x in sys.argv ):
    sys.argv.insert(1, '-q')

requirements_dev = '''
jinja2==2.11.*
pyyaml==5.3.*
setproctitle
'''.strip().split('\n')

requirements_test = '''
ansible>=2.8
cffi==1.14.2
coverage==5.2.1
pytest-tap==3.1
pytest-cov==2.10.1
pytest==6.0.1
'''.strip().split('\n')

# https://jichu4n.com/posts/how-to-add-custom-build-steps-and-commands-to-setuppy/
class RequirementsCommand(distutils.cmd.Command):
    """ Emit requirements """
    description = 'emit requirements'
    user_options = [
        ('dev',  None, 'emit dev requirements'),
        ('test', None, 'emit test requirements')
    ]

    def initialize_options(self):
        self.dev  = None
        self.test = None

    def finalize_options(self): pass

    def run(self):
        if self.test:
           requirements = requirements_test
        else:
           requirements = requirements_dev
        print('\n'.join(requirements))
        return requirements

with open('version') as f:
    __version__ = f.read().strip()
    __version__ = re.sub('^[vV]|\-\w{8}$', '', __version__)

class VersionCommand(distutils.cmd.Command):
    """ Emit version """
    description = 'Emit version'
    user_options = [
        ('version', None, 'version')
    ]
    def initialize_options(self): pass
    def finalize_options(self): pass
    def run(self):
            print(__version__)
            return(__version__)

with open('README.md', 'r') as fh:
    long_description = fh.read()

setuptools.setup(
        name             = 'inji',
        version          = __version__,
        description      = 'Render parametrized Jinja2 templates at the CLI',
        url              = 'https://github.com/shalomb/inji',
        author           = 'Shalom Bhooshi',
        author_email     = 's.bhooshi@gmail.com',
        license          = 'Apache License 2.0',
        packages         = setuptools.find_packages(),
        scripts          = [ 'bin/inji' ],
        install_requires = requirements_dev,
        include_package_data = True,
        zip_safe         = False,
        python_requires  = '>=3.5',
        long_description_content_type = 'text/markdown',
        long_description = long_description,
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
        ],
        cmdclass = {
            'requirements': RequirementsCommand,
            'version': VersionCommand,
        }
    )
