#!/usr/bin/env python3

# -*- coding: utf-8 -*-

# NAME
# inji/__init__.py

# Copyright (C) 2020 Shalom Bhooshi
# Author: Shalom Bhooshi

""" Utility for rendering jinja2 templates """

from . import cli

__version__  = cli._version()
# cli_location was removed in v0.6.0 (modernized to use [project.scripts] in pyproject.toml)
# The 'inji' command is now declared via pyproject.toml and installed via uv tool/pip
