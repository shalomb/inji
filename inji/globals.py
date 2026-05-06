# hold global variables and functions for direct use in templates
# https://jinja.palletsprojects.com/en/2.11.x/api/#the-global-namespace
# https://jinja.palletsprojects.com/en/2.11.x/templates/#list-of-global-functions

import builtins
import inspect
import platform as _platform
import re
import socket
import sys
from datetime import datetime

import markdown as _markdown

from . import utils

# Default extensions and config for the markdown global — extracted so ruff
# can format the lambda without exceeding the 100-char line limit.
_MD_EXTENSIONS = [
    "admonition",
    "extra",
    "meta",
    "sane_lists",
    "smarty",
    "toc",
    "wikilinks",
]
_MD_EXTENSION_CONFIGS = {
    "codehilite": {
        "linenums": True,
        "guess_lang": False,
    }
}


def _os_release(k=None):
    ret = {}
    for line in open("/etc/os-release").read().strip().split("\n"):
        k, v = line.split("=", 1)
        ret[k] = v.strip('"')
    return ret


def _render_markdown(
    f,
    output_format="html5",
    extensions=None,
    extension_configs=None,
):
    """Load a markdown file and convert it to HTML."""
    return _markdown.markdown(
        utils.load_file(f),
        extensions=extensions or _MD_EXTENSIONS,
        output_format=output_format,
    )


"""
_globals contains the dictionary of functions (implemented as lambda functions)
or variables (regular values) that are accessible inside template expressions.
"""
_globals = dict(
    bacon_ipsum=(
        """ Return N paragraphs of bacon-ipsum """,
        lambda n=3: utils.get(
            f"https://baconipsum.com/api/?type=all-meat&paras={n}&start-with-lorem=1&format=html"
        ),
    ),
    cat=(""" Read a file in """, lambda *n: [utils.load_file(x) for x in n]),
    date=(
        """ Return the timestamp for datetime.now() """,
        datetime.now(),  # variable
    ),
    git_branch=(
        """ Return the current git branch of HEAD """,
        lambda: utils.cmd("git rev-parse --abbrev-ref HEAD"),
    ),
    GET=(
        """ Issue a HTTP GET request against URL returning body content or an object if JSON """,
        lambda url="http://httpbin.org/anything": utils.get(url),
    ),
    git_commit_id=(
        """ Return the git commit ID of HEAD """,
        lambda fmt="%h": utils.cmd(f"git log --pretty=format:{fmt} -n 1 HEAD"),
    ),
    git_remote_url=(
        """ Return the URL of the named origin """,
        lambda origin="origin": utils.cmd(f"git remote get-url {origin}"),
    ),
    git_remote_url_http=(
        """ Return the HTTP URL of the named origin """,
        lambda origin="origin": re.sub(
            "git@(.*):", "https://\\1/", utils.cmd(f"git remote get-url {origin}")
        ),
    ),
    git_tag=(
        """ Return the value of git describe --tag --always """,
        lambda fmt="current": (
            utils.cmd("git describe --tag --always")
            if fmt == "current"
            else re.sub(r"-[A-Fa-fg0-9\-]+$", "", utils.cmd("git describe --tag --always"))
        ),
    ),
    host_id=(""" Return the host's ID """, lambda: utils.cmd("hostid")),
    int=(""" Cast value as an int """, lambda v: builtins.int(v)),
    fqdn=(""" Return the current host's fqdn """, lambda: socket.getfqdn()),
    hostname=(""" Return the current host's name """, lambda: socket.gethostname()),
    machine_id=(
        """ Return the machine's ID """,
        lambda: utils.load_file("/var/lib/dbus/machine-id") or utils.load_file("/etc/machine-id"),
    ),
    markdown=(
        """ Load content from a markdown file and convert it to html """,
        _render_markdown,
    ),
    now=(""" Return the timestamp for datetime.now() """, lambda: datetime.now()),
    os=(""" Dictionary holding the contents of /etc/os-release """, _os_release()),
    os_release=(
        """ Lookup key in /etc/os-release and return its value """,
        lambda k: _os_release()[k],
    ),
    platform=(
        """ Access functions in the platform module """,
        dict(set(inspect.getmembers(_platform, inspect.isfunction))),
    ),
    run=(
        """
    Run a command and return its STDOUT
    e.g. hello {{ run('id -un') }}
    """,
        lambda v: utils.cmd(v),
    ),
    ip_api=(
        """
    Return an attribute from the http://ip-api.com/json response object
    (e.g. status, country, countryCode, region, city, zip, lat, lon,
    timezone, isp, org, as, query)
    """,
        lambda key="country": utils.ip_api(key),
    ),
    whatismyip=(""" Return the host's public (IPv4) address """, lambda: utils.whatismyip()),
)


for k, v in _globals.items():
    setattr(sys.modules[__name__], k, v[1])
