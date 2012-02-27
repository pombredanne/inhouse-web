# -*- coding: utf-8 -*-

"""Testcases for the models."""

import time

from django.test import TestCase
from django.test.client import Client

from inhouse import models


class TimerTest(TestCase):

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
