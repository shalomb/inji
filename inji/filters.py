# https://jinja.palletsprojects.com/en/2.11.x/templates/#list-of-builtin-filters
# https://www.webforefront.com/django/usebuiltinjinjafilters.html

import ast
import builtins
import csv
import os
import sys
import time
from datetime import datetime

import more_itertools
import tr as _tr

from . import utils

# TODO
# Encapsulating filters in this way is great but it does little for their
# test coverage (nice trick to fool pycoverage eh!)
# Set these up for proper unit (not end-to-end) tests.

filters = dict(
    append=(""" Append values to the input list """, lambda v, *p: list(v) + list(p)),
    cat=(
        """ Concatenate "STDIN" (i.e. -) with contents of files named """,
        lambda v, *f: [
            (lambda item, default: default if item == "-" else utils.load_file(item))(
                item=x, default=v
            )
            for x in f
        ],
    ),
    count=(
        """ Return the count of the number of times x is in list """,
        lambda lst, *x: lst.count(*x),
    ),
    env_override=(
        """
    Allow for a value set in the environment to override a given value
    e.g. url | env_override("URL")
    """,
        lambda v, k: os.getenv(k, v),
    ),
    extend=(
        """ Append items to a list and return the list """,
        lambda *n: list(n[0]) + list(n[1:]),
    ),
    format_dict=(
        """
    Given a dict as value, return a formatted string as specified in format.
    e.g. url | urlsplit | format_dict("{scheme}://{hostname}:8080/{path}/")
    """,
        lambda v, f: f.format(**v),
    ),
    format_list=(
        """
    Given a list as value, return a formatted string as specified in format.
    e.g. url | urlsplit | format_list("{0}://{1}")
    """,
        lambda v, f: f.format(*v),
    ),
    from_csv=(
        """
    Split a string delimited by commas and return items in a list.
    e.g. (foo,) | from_csv  # note the (foo,) as csv.reader is expecting lines
    """,
        lambda v: list(csv.reader(v))[0],  # magic number is for single line of text
    ),
    from_literal=(""" Parse a string using ast.literal_eval() """, lambda v: ast.literal_eval(v)),
    grep=(
        """ Filter in those items matching text """,
        lambda v, *p: [x for m in p for x in v if x == m],
    ),
    index=(""" Return the index of item in list """, lambda lst, *x: lst.index(*x)),
    insert=(
        """ Insert values to the input list at specified index """,
        lambda lst, i=0, *v: [*lst[:i], *v, *lst[i:]],
    ),
    items=(
        """
    Select items specified by indexes from the list passed in
    e.g. range(1,10) | items(0,2,5,-3,-2)
    """,
        lambda *n: list(n[0][x] for x in n[1:]),
    ),
    keys=(
        """
    Return the keys of a dict passed in
    """,
        lambda d: d.keys(),
    ),
    pop=(
        """ Pop items at index 1 from an input list and return it """,
        lambda lst, i=-1: lst.pop(i),
    ),
    prepend=(""" Prepend values to the input list """, lambda lst, *v: [*v, *lst]),
    push=(""" Append items to a list and return the list """, lambda *n: list(n[0]) + list(n[1:])),
    remove=(
        """ Remove first item x from list """,
        lambda lst, *x: lst if lst.remove(*x) is None else lst,
    ),
    shift=(""" Pop item at index 0 from an input list and return it """, lambda lst: lst.pop(0)),
    strftime=(
        """ For a given date, return a date string in strftime(3) format """,
        lambda v, f="%F %T%z", tz="UTC": v.strftime(f),
    ),
    to_set=(""" Create a set from list """, lambda lst: builtins.set(lst)),
    to_date=(
        """ For a given string, try and parse the date """,
        # NOTE This isn't resilient against leapseconds
        # https://stackoverflow.com/questions/1697815/how-do-you-convert-a-time-struct-time-object-into-a-datetime-object#comment31967564_1697838
        lambda v, f="%Y-%m-%d %H:%M:%S.%f": datetime(*(time.strptime(v, f)[:6])),
    ),
    to_url=(
        """
    Take values from a dict passed in and
    return a string formatted in the form of a URL
    """,
        lambda v, f="https://{hostname}": f.format(**v),
    ),
    tr=(""" Emulate tr(1) """, lambda s, x, y, m="": _tr.tr(x, y, s, m)),
    uniq=(
        """ Remove duplicates items from set keeping order """,
        lambda lst: more_itertools.unique_everseen(lst),
    ),
    unshift=(
        """ Prepend items to a list and return the list """,
        lambda *n: list(n[1:]) + list(n[0]) if False else [*n[1:], *n[0]],
    ),
    values=(
        """
    Return the values of a dict passed in
    """,
        lambda d: d.values(),
    ),
    wrap=(
        """
    Wrap value with "parantheses" specified in format (default "()")
    """,
        lambda v, t="()": f"{t[0]}{v}{t[1]}",
    ),
)

filters.update(
    {
        # Seems del is specially treated inside dict()
        "del": (
            """ Remove item at index x from list """,
            lambda lst, x: [*lst[:x], *lst[(x + 1) :]],
        ),
    }
)

try:
    if __import__("importlib.util", fromlist=["find_spec"]).find_spec("ansible"):
        from .ansible import FilterModule

        filters.update(FilterModule().filters())
except Exception:
    pass

# Re-apply inji's own strftime after ansible (which overwrites it with an
# epoch-only variant). Inji's strftime accepts any datetime + strftime format.
_inji_strftime = (
    """ For a given date, return a date string in strftime(3) format """,
    lambda v, f="%F %T%z", tz="UTC": v.strftime(f),
)
filters["strftime"] = _inji_strftime

for k, v in filters.items():
    setattr(sys.modules[__name__], k, v[1])
