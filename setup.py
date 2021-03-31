#!/usr/bin/env python3

# -*- coding: utf-8 -*-

import distutils.cmd
import os
import re
import setuptools
import subprocess
import sys

# Suppress setup.py's stdout logging for our commands that output data
if any( x in ['requirements', 'version'] for x in sys.argv ):
    sys.argv.insert(1, '-q')

requirements_dev = '''
jinja2==2.11.*
pyyaml==5.4.*
markdown==3.2.*
requests>=2.24
python-tr
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

def version():
    args = 'git describe --tags --always'.split(' ')
    version = subprocess.check_output(args).decode().strip()
    version = re.sub('^[vV]|\-\w{8}$', '', version)
    version = re.sub('-', '.post', version)
    return version

class VersionCommand(distutils.cmd.Command):
    """ Emit version numbers """
    description = 'Emit version numbers'
    user_options = [
        ('version', None, 'current version number'),
        ('next', None, 'next version number'),
    ]
    def initialize_options(self): pass
    def finalize_options(self): pass
    def run(self):
        print(version())
        return(version())

with open('README.md', 'r') as fh:
    long_description = fh.read()

setuptools.setup(
    name             = 'inji',
    version          = version(),
    description      = 'Render parametrized Jinja2 templates at the CLI',
    author           = 'Shalom Bhooshi',
    author_email     = 's.bhooshi@gmail.com',
    license          = 'Apache License 2.0',
    url              = 'https://github.com/shalomb/inji',
    download_url     = 'https://github.com/shalomb/inji/tarball/{}'.format(version()),
    packages         = setuptools.find_packages(),
    scripts          = [ 'bin/inji' ],
    install_requires = requirements_dev,
    include_package_data = True,
    zip_safe         = False,
    python_requires  = '>=3.5',
    long_description_content_type = 'text/markdown',
    long_description = long_description,
    keywords         = [ 'jinja', 'jinja2', 'templating' ],
    classifiers      = [
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
    cmdclass         = {
        'requirements': RequirementsCommand,
        'version':      VersionCommand,
    }
)
