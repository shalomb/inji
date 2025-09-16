#!/usr/bin/env python3

# -*- coding: utf-8 -*-

import distutils.cmd
import re
import subprocess
import sys
import setuptools

# Suppress setup.py's stdout logging for our commands that output data
if any( x in ['requirements', 'version'] for x in sys.argv ):
    sys.argv.insert(1, '-q')

#!/usr/bin/env python3

# -*- coding: utf-8 -*-

# Minimal setup.py for legacy compatibility
# All configuration is now in pyproject.toml

import setuptools

setuptools.setup()
