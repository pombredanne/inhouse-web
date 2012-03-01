# -*- coding: utf-8 -*-

"""Testcases for the models."""

import datetime
import time

from django.test import TestCase
from django.test.client import Client

from inhouse import models


class TestAddress(TestCase):

    def test_get_addressstring(self):
        c = models.Country()
        c.id = 1
        c.name = u'Germany'
        adr = models.Address()
        adr.name1 = u'foo'
        adr.name2 = u'bar'
        adr.country = c
        ret = adr.get_addressstring()
        self.assertEqual(ret, u'foo<br />bar<br />')
        adr.street = u'foostreet'
        ret = adr.get_addressstring()
        self.assertEqual(ret, u'foo<br />bar<br />foostreet<br />')

    def test_get_addresstuple(self):
        c = models.Country()
        c.id = 1
        c.name = u'Germany'
        adr = models.Address()
        adr.name1 = u'Max'
        ret = adr.get_addresstuple(names_only=True)
        self.assert_(isinstance(ret, tuple))
        self.assertEqual(len(ret), 1)
        adr.name2 = u'Mustermann'
        ret = adr.get_addresstuple(names_only=True)
        self.assertEqual(len(ret), 2)
        adr.name3 = u'foo'
        ret = adr.get_addresstuple(names_only=True)
        self.assertEqual(len(ret), 3)
        adr.name4 = u'bar'
        adr.street = u'Musterstrasse'
        adr.city = u'Musterstadt'
        adr.zip_code = '12345'
        adr.country = c
        ret = adr.get_addresstuple(names_only=True)
        self.assertEqual(len(ret), 4)
        ret = adr.get_addresstuple(names_only=False)
        self.assertEqual(len(ret), 7)

    def test_get_join_name(self):
        c = models.Country()
        c.id = 1
        c.name = u'Germany'
        adr = models.Address()
        adr.name1 = u'foo1'
        adr.name2 = u'foo2'
        adr.name3 = u'foo3'
        adr.name4 = u'foo4'
        adr.country = c
        ret = adr.get_join_name()
        self.assertEqual(ret, 'foo1foo2foo3foo4')
        ret = adr.get_join_name(' ')
        self.assertEqual(ret, 'foo1 foo2 foo3 foo4')

    def test_get_join_name_html(self):
        c = models.Country()
        c.id = 1
        c.name = u'Germany'
        adr = models.Address()
        adr.name1 = u'foo1'
        adr.name2 = u'foo2'
        adr.name3 = u'foo3'
        adr.name4 = u'foo4'
        ret = adr.get_join_name_html()
        self.assertEqual(ret, 'foo1<br />foo2<br />foo3<br />foo4')


class TestDay(TestCase):

    def test_slugify(self):
        day = models.Day()
        day.date = datetime.date(2010, 1, 12)
        self.assertEqual(day.slugify(), u'2010/01/12')
        day.date = datetime.date(2012, 7, 15)
        self.assertEqual(day.slugify(), u'2012/07/15')


class TestTimer(TestCase):

    def setUp(self):
        self.client = Client()

    def test_clear(self):
        timer = models.Timer()
        timer.clear()
        self.assertEqual(timer.active, False)
        self.assertEqual(timer.duration, 0)

    def test_get_time_tuple(self):
        timer = models.Timer()
        timer.duration = 4380
        hours, minutes = timer.get_time_tuple()
        self.assertEqual(hours, 1)
        self.assertEqual(minutes, 15)
        timer.duration = 540
        hours, minutes = timer.get_time_tuple()
        self.assertEqual(hours, 0)
        self.assertEqual(minutes, 15)

    def test_start(self):
        timer = models.Timer()
        timer.start()
        self.assertEqual(timer.active, True)

    def test_stop(self):
        timer = models.Timer()
        timer.stop()
        self.assertEqual(timer.active, False)
        self.assertEqual(timer.duration, 0)
        timer = models.Timer()
        timer.start()
        time.sleep(1)
        timer.stop()
        self.assertEqual(timer.active, False)
        self.assertEqual(timer.duration, 1)
