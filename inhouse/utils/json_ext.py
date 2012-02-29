# -*- coding: utf-8 -*-

"""Custom JSON api.

The purpose of this module is to expose the API of the json module
with application specific defaults. That's mainly providing a custom
encoder.
"""

# silency pylint, this is a wrapper module...
# function intentionally redefined, pylint: disable=E0102
# wildcard import is intentional too, pylint: disable=W0401,W0614
# hidden names are ok, pylint: disable=C0103
from json import *

from django.core.serializers.json import DjangoJSONEncoder

_real_dumps = dumps


def dumps(*args, **kwargs):
    """Calls json.dumps but optionally sets DjangoJSONEncode."""
    if not 'cls' in kwargs:
        kwargs['cls'] = DjangoJSONEncoder
    return _real_dumps(*args, **kwargs)
