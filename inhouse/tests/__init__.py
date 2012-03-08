"""Unittests for the application."""

import os
import re
import types
import unittest


# TestCase discovery is derived from
# http://code.google.com/p/google-app-engine-django/source/browse/trunk/appengine_django/tests/__init__.py

TEST_RE = r'^.*tests.py$'
TEST_NAME_REGEX = os.environ.get('TEST_NAME_REGEX', None)


def _name_excluded_by_pattern(name):
    if not TEST_NAME_REGEX:
        return False
    regex = []
    for part in TEST_NAME_REGEX.split('+'):
        part = part.strip()
        if re.escape(part) == part:  # it's literal string
            regex.append('.*%s.*' % part)
        else:  # it's an regex already
            regex.append(part)
    if not regex:
        return False
    elif len(regex) == 1:
        regex = regex[0]
    else:
        regex = '(%s)' % '|'.join(regex)
    return re.search(regex, name, re.IGNORECASE) is None


# Search through every file inside this package.
test_names = []
test_dir = os.path.dirname(__file__)
for filename in os.listdir(test_dir):
    if not re.match(TEST_RE, filename):
        continue
    # Import the test file and find all TestClass clases inside it.
    test_module = __import__('inhouse.tests.%s' %
                             filename[:-3], {}, {},
                             filename[:-3])
    for name in dir(test_module):
        item = getattr(test_module, name)
        if not (isinstance(item, (type, types.ClassType)) and
                issubclass(item, unittest.TestCase)):
            continue
        if _name_excluded_by_pattern(name):
            print 'Ignoring %s by user request.' % name
            continue
        # Found a test, bring into the module namespace.
        exec '%s = item' % name
        test_names.append(name)

# Hide everything other than the test cases from other modules.
__all__ = test_names
