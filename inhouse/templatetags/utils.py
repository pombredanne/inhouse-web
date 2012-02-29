# -*- coding: utf-8 -*-

"""Common utilities."""

from django import template
from django.utils.translation import ugettext as _


register = template.Library()


@register.filter
def format_minutes_to_time(val):
    """Formates minutes as decimal to a hour string.

    :param val:
    :returns: String formatted time in MM:HH
    """
    if not val:
        return ''
    h = int(val / 60)
    m = int(val % 60)
    return u'%02i:%02i' % (h, m)
