# -*- coding: utf-8 -*-

"""Template context processors."""

from django.conf import settings

import inhouse


def template_defaults(request):
    """Adds default variables to context."""
    # request unused, pylint:disable=W0613
    return {'DEV_VERSION': settings.DEV_VERSION,
            'VERSION': inhouse.__version__}
