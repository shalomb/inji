# Copyright (C) 2020 Shalom Bhooshi
"""Utility for rendering Jinja2 templates."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("inji")
except PackageNotFoundError:
    __version__ = "unknown"
