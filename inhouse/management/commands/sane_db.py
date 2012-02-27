# -*- coding: utf-8 -*-

"""Command to check the database sanity."""

from optparse import make_option
import time

from django.core.management.base import BaseCommand
from django.utils.translation import ugettext_lazy as _


class Command(BaseCommand):

    help = _(u'Verify the database sanity')

    def handle(self, *args, **options):
        start_time = time.time()
        end_time = time.time()

    def _get_tests(self):
        pass

    def sane_xxx(self):
        pass
