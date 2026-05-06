#!/usr/bin/env python3

# -*- coding: utf-8 -*-

import argparse
import fnmatch
import json
import os
import subprocess
import sys
from os.path import (  # noqa: F401 — re-exported as utils.basename etc.
    abspath,
    basename,
    dirname,
    exists,
    expandvars,
    isdir,
    isfile,
    join,
)

import requests
import yaml


def json_parse(string):
    """Parse a JSON string into a dictionary"""
    try:
        return json.loads(string)
    except Exception as e:
        msg = f"Error parsing JSON config: {str(e)}"
        print(msg, file=sys.stderr)
        raise TypeError(msg)


def kv_parse(string):
    """Parse a string of the form foo=bar into a dictionary"""
    try:
        key, val = string.split("=", 1)
        if key is None or key == "":
            raise TypeError("Empty key")
    except Exception as e:
        err = f"Invalid key found parsing KV string '{string}': {str(e)}"
        print(err, file=sys.stderr)
        raise
    return {key: val}


def read_context(yaml_file):
    yaml_file = yaml_file.__str__()
    with open(yaml_file) as f:
        try:
            in_vars = yaml.load(f, Loader=yaml.SafeLoader)
            if in_vars is None:
                raise TypeError(f"'{yaml_file}' contains no data")
        except TypeError as exc:
            raise exc
    return in_vars


def recursive_iglob(rootdir=".", pattern="*"):
    for root, dirnames, filenames in os.walk(rootdir):
        for filename in fnmatch.filter(filenames, pattern):
            yield os.path.join(root, filename)


def path(fspath, type="file"):
    """
    Checks if a filesystem path exists with the correct type
    """

    fspath = abspath(expandvars(str(fspath)))
    msg = None
    prefix = f"path '{fspath}'"

    if not exists(fspath):
        msg = f"{prefix} does not exist"

    if type == "file" and isdir(fspath):
        msg = f"{prefix} is not a file"

    if msg is not None:
        print(msg, file=sys.stderr)
        raise argparse.ArgumentTypeError(msg)

    return fspath


def file_or_stdin(file):
    # /dev/stdin is a special case allowing bash (and other shells?) to name stdin
    # as a file. While python should have no problem reading from it, we actually
    # read template relative to the template's basedir and /dev has no templates.
    if file == "-" or file == "/dev/stdin":
        return "-"
    return path(file)


def cmd(args):
    return subprocess.check_output(args.split(" ")).decode("utf-8").strip()


def load_file(file):
    return open(file, encoding="utf-8").read().strip()


def get(url):
    response = requests.get(url)
    if (
        "Content-Type" in response.headers
        and response.headers["Content-Type"] == "application/json"
    ):
        ret = response.json()
    else:
        ret = response.content.decode("utf8")
    return ret


def ip_api(key):
    return json.loads(get("http://ip-api.com/json"))[key]


def whatismyip():
    return get("http://checkip.amazonaws.com/").strip()
