#!/usr/bin/env python3

# -*- coding: utf-8 -*-

# NAME
# inji/__init__.py

# Copyright (C) 2020 Shalom Bhooshi
# Author: Shalom Bhooshi

""" Utility for rendering jinja2 templates """

from . import cli

__version__  = cli._version()
cli_location = cli.cli_location()
