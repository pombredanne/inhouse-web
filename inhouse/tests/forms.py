# -*- coding: utf-8 -*-

"""Testcases for the forms."""

from django.core.exceptions import ValidationError
from django.test import TestCase

from inhouse.forms import IssueNumber


class TestIssueNumber(TestCase):

    def test_to_python(self):
        v = IssueNumber()
        self.assertEqual(v.to_python('#1234'), 1234)
        self.assertEqual(v.to_python(1234), 1234)
        self.assertEqual(v.to_python(' #1234 '), 1234)
        self.assertEqual(v.to_python('xxx'), 0)

    def test_validate(self):
        v = IssueNumber()
        self.assertRaises(ValidationError, v.validate, 'foo')
