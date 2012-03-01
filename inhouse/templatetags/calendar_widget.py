# -*- coding: utf-8 -*-

"""Tags to create a calendar widget."""

from calendar import HTMLCalendar, month_name
# see: http://journal.uggedal.com/creating-a-flexible-monthly-calendar-in-django/
import calendar
import datetime
import re

from django import template
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _


register = template.Library()

P_DAY_URL = re.compile(r"""^time/(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d+)/$""")


@register.tag(name='get_calendar')
def do_calendar(parser, token):
    syntax_help = 'syntax should be \'get_calendar for <month> <year> as <var_name>\''
    try:
        tag_name, arg = token.contents.split(None, 1)
    except ValueError:
        raise template.TemplateSyntaxError, '%r tag requires arguments, %s' \
              % (token.contents.split()[0], syntax_help)
    m = re.search(r'as (\w+)', arg)
    if not m:
        raise template.TemplateSyntaxError, '%r tag had invalid arguments, %s' \
              % (tag_name, syntax_help)
    return CalendarNode(*m.groups())


class Calendar(HTMLCalendar):
    """A HTML calendar with small adjustments."""

    def formatday(self, day, weekday):
        """Return a day as a table cell."""
        if day != 0:
            cssclass = self.cssclasses[weekday]
            if datetime.date.today() == datetime.date(self.year, self.month, day):
                cssclass += ' today'
            #if day == 0:
            #    return '<td class="noday">&nbsp;</td>' # day outside month
            #else:
            return '<td class="%s">%d</td>' % (cssclass, day)
        else:
            return '<td class="noday">&nbsp;</td>' # day outside month

    def formatmonthname(self, theyear, themonth, withyear=True):
        v = []
        """Return a month name as a table row."""
        if withyear:
            s = '%s %s' % (month_name[themonth], theyear)
        else:
            s = '%s' % month_name[themonth]
        v.append('<tr><th colspan="7" class="month">%s' % s)
        v.append('<div class="btn-group" style="float:right;">')
        v.append('<a class="btn btn-mini" title="" href="#"><i class="icon-arrow-left"></i></a>')
        v.append('<a class="btn btn-mini" title="" href="#"><i class="icon-arrow-right"></i></a>')
        v.append('</div>')
        v.append('</th>')
        v.append('</tr>')
        return ''.join(v)

    def formatmonth(self, year, month):
        self.year, self.month = year, month
        return super(Calendar, self).formatmonth(year, month)


class CalendarNode(template.Node):
    """The node, that creates the calendar widget."""

    def __init__(self, var_name):
        self.var_name = var_name

    def render(self, context):
        today = datetime.date.today()
        request = template.Variable('request').resolve(context)
        month = int(request.session['calendar_month'])
        year = int(request.session['calendar_year'])
        #context['selected_month'] = datetime.date(year, month, 1)
        cal = Calendar()
        return mark_safe(cal.formatmonth(year, month))
