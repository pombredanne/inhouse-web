# -*- coding: utf-8 -*-

"""Testcases for template tags."""

import decimal

from django.test import TestCase

from inhouse.templatetags.utils import format_minutes_to_time


class TestFormatMinutesToTime(TestCase):

    def test_return_value(self):
        self.assertEqual(format_minutes_to_time(1), u'00:01')
        self.assertEqual(format_minutes_to_time(15), u'00:15')
        self.assertEqual(format_minutes_to_time(60), u'01:00')
        self.assertEqual(format_minutes_to_time(61), u'01:01')
        self.assertEqual(format_minutes_to_time(600), u'10:00')
        self.assertEqual(format_minutes_to_time(601), u'10:01')
        self.assertEqual(format_minutes_to_time(611), u'10:11')
        self.assertEqual(format_minutes_to_time(671), u'11:11')

    def test_should_accept_integer(self):
        value = 120
        ret = format_minutes_to_time(value)
        self.assertEqual(ret, u'02:00')

    def test_should_accept_decimal(self):
        value = decimal.Decimal(120)
        ret = format_minutes_to_time(value)
        self.assertEqual(ret, u'02:00')

    def test_should_handle_empty_values(self):
        self.assertEqual(format_minutes_to_time(None), u'')
        self.assertEqual(format_minutes_to_time(False), u'')
