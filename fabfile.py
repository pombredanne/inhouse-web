# -*- coding: utf-8 -*-

import os
import shutil
import sys
sys.path.insert(0, os.getcwd())

from fabric import colors
from fabric.api import *
from fabric.contrib import django
from fabric.contrib.console import confirm


CMD_PYTHON = 'python'
CMD_PYLINT = 'pylint'

PYLINT_MODULES = ['inhouse']

#INITIAL_FIXTURES = ['groups', 'permissions', 'dev_users']
INITIAL_FIXTURES = ['countries', 'groups', 'dev_users']

django.settings_module('settings')
from django.conf import settings as dj_settings


def clean():
    """Cleans all temporary files."""
    for root, dirs, files in os.walk('.'):
        for name in files:
            if name.endswith('.pyc') or name.endswith('~'):
                os.remove(os.path.join(root, name))


def dev_db(assume_yes=False):
    """Recreate development database."""
    django.settings_module('settings_debug')
    conf = dj_settings.DATABASES.get('default')
    if not conf:
        abort(colors.red('No default database configured.'))
    if conf.get('ENGINE', '').endswith('sqlite3'):
        path = conf.get('NAME')
        if os.path.isfile(path):
            if not assume_yes and not confirm('Delete existing database?'):
                abort('Aborting at user request.')
            os.remove(path)
    elif conf.get('ENGINE', '').endswith('psycopg2'):
        with settings(warn_only=True):
            local('dropdb -U %s %s' % (conf.get('USER'), conf.get('NAME')))
        local('createdb -U %s %s' % (conf.get('USER'), conf.get('NAME')))
    load_initial_data()


def devserver(host='localhost', port=8000):
    """Runs the application in development mode."""
    #local('python manage.py runserver %s:%s' % (host, port))
    local('export DJANGO_SETTINGS_MODULE=settings.development')
    local('python manage.py runserver %s:%s --settings=settings_debug' % (host, port))


def disable_initial_data():
    django.settings_module('settings_debug')
    os.remove('inhouse/fixtures/initial_data.json')


def enable_initial_data():
    django.settings_module('settings_debug')
    shutil.copy('inhouse/fixtures/_initial_data.json',
                'inhouse/fixtures/initial_data.json')


def errlint(pylint=CMD_PYLINT):
    """Run pylint to find only errors."""
    lint(pylint, pylint_args='-f colorized -d W,C,R,I -r n')


def lint(pylint=CMD_PYLINT, pylint_args=''):
    """Run pylint."""
    with settings(warn_only=True):  # catch pylint's exit status
        result = local(' '.join([CMD_PYLINT,
                                 '-d I --rcfile=tools/pylint.rc',
                                 pylint_args] + PYLINT_MODULES))
        # pylint's return code is: 0 = fine, 1 = fatal, 2 = error, 4 =
        # warning, 8 = refactor, 16 = convention, 32 = usage
        # error. 1-16 are bit-ORed.
        fatal = 1
        error = 2
        warning = 4
        usage = 32
        if result.return_code == usage:
            abort(colors.red('Pylint usage error.', bold=True))
        elif fatal & result.return_code or error & result.return_code:
            abort(colors.red('Pylint error.', bold=True))
        elif warning & result.return_code:
            print(colors.yellow('Pylint reported warnings.'))


def load_initial_data():
    django.settings_module('settings_debug')
    enable_initial_data()
    local('python manage.py syncdb --noinput')
    disable_initial_data()


def mo():
    """Compiles all language files."""
    local('python manage.py compilemessages')


def po():
    """Extracts all gettext strings."""
    local('python manage.py makemessages -a -i "env*"')
    local('python manage.py makemessages -d djangojs -a -i "env*"')


def quicklint(pylint=CMD_PYLINT, pylint_args=''):
    """Run pylint with colorized output."""
    lint(pylint, pylint_args='-f colorized -r n ' + pylint_args)


def recreate_initial_data():
    django.settings_module('settings_debug')
    if os.path.isfile('inhouse/fixtures/_initial_data.json'):
        local('mv inhouse/fixtures/_initial_data.json inhouse/fixtures/_initial_data.json.old')
        local('rm -f dev.db')
    local('python manage.py syncdb --noinput')
    local('python manage.py loaddata %s' % ' '.join(INITIAL_FIXTURES))
    local('python manage.py dumpdata -a -e inhouse.AuthUserGroup -e contenttypes.ContentType --indent=2> inhouse/fixtures/_initial_data.json')


def todos(pylint=CMD_PYLINT):
    """Run pylint and only show todos."""
    lint(pylint, pylint_args='-f colorized -d W,C,R,I,E -e W0511 -r n')
