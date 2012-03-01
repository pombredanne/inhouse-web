# -*- coding: utf-8 -*-


"""Main fabric file

Notes:
 * To use the less compiler, install the 'NodeJS package manager' and run 'npm install --global less'
"""

from cStringIO import StringIO
import os
import shutil
import sys
sys.path.insert(0, os.getcwd())
import urllib2
import zipfile

from fabric import colors
from fabric.api import *
from fabric.contrib import django
from fabric.contrib.console import confirm


CMD_PYTHON = 'python'
CMD_PYLINT = 'pylint'
CMD_LESSC = 'lessc'

PYLINT_MODULES = ['inhouse']

INITIAL_FIXTURES = ['auth', 'countries']

BOOTSTRAP_PATH = os.path.abspath(os.path.join('assets', 'less', 'bootstrap'))
BOOTSTRAP_URL = 'https://github.com/twitter/bootstrap/zipball/v2.0.1'

django.settings_module('settings')
from django.conf import settings as dj_settings


def download_bootstrap():
    """Retrieves the boostrap less files."""
    if (os.path.isdir(BOOTSTRAP_PATH)
        and os.path.isfile(os.path.join(BOOTSTRAP_PATH, 'bootstrap.less'))):
        return
    print 'Fetching %s' % BOOTSTRAP_URL
    response = urllib2.urlopen(BOOTSTRAP_URL)
    zfile = zipfile.ZipFile(StringIO(response.read()))
    dest = os.path.abspath(os.path.join('assets', 'less'))
    print 'Extracting to %s' % dest
    topdir = zfile.namelist()[0]
    lessdir = os.path.join(topdir, 'less')
    zfile.extractall(dest,)
    shutil.move(os.path.join(dest, lessdir), BOOTSTRAP_PATH)
    shutil.rmtree(os.path.abspath(os.path.join('assets', 'less', topdir)))


@task
def compile_less():
    """Compiles less scripts and outputs the css files."""
    lessc_args = ''
    download_bootstrap()
    lessfile = os.path.abspath(os.path.join('assets', 'less', 'inhouse.less'))
    cssfile = os.path.abspath(os.path.join('inhouse', 'static', 'css',
                                           'style.css'))
    print 'Compiling less files'
    lessc_args += '--compress'
    local(' '.join([CMD_LESSC, lessc_args, lessfile, cssfile]))


@task
def clean():
    """Cleans all temporary files."""
    for root, dirs, files in os.walk('.'):
        for name in files:
            if name.endswith('.pyc') or name.endswith('~'):
                os.remove(os.path.join(root, name))


@task
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
    load_dev_data()


@task
def devserver(host='localhost', port=8000):
    """Runs the application in development mode."""
    #local('python manage.py runserver %s:%s' % (host, port))
    local('export DJANGO_SETTINGS_MODULE=settings.development')
    local('python manage.py runserver %s:%s --settings=settings_debug' % (host, port))


@task
def disable_initial_data():
    django.settings_module('settings_debug')
    os.remove('inhouse/fixtures/initial_data.json')


@task
def enable_initial_data():
    django.settings_module('settings_debug')
    shutil.copy('inhouse/fixtures/_initial_data.json',
                'inhouse/fixtures/initial_data.json')


@task
def errlint(pylint=CMD_PYLINT):
    """Run pylint to find only errors."""
    lint(pylint, pylint_args='-f colorized -d W,C,R,I -r n')


@task
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


@task
def load_dev_data():
    django.settings_module('settings_debug')
    local('python manage.py loaddata dev_users')
    local('python manage.py loaddata test_data')


@task
def load_initial_data():
    django.settings_module('settings_debug')
    enable_initial_data()
    local('python manage.py syncdb --noinput')
    disable_initial_data()


@task
def mo():
    """Compiles all language files."""
    local('python manage.py compilemessages')


@task
def po():
    """Extracts all gettext strings."""
    local('python manage.py makemessages -a -i "env*"')
    local('python manage.py makemessages -d djangojs -a -i "env*"')


@task
def quicklint(pylint=CMD_PYLINT, pylint_args=''):
    """Run pylint with colorized output."""
    lint(pylint, pylint_args='-f colorized -r n ' + pylint_args)


@task
def recreate_initial_data():
    django.settings_module('settings_debug')
    if os.path.isfile('inhouse/fixtures/_initial_data.json'):
        local('mv inhouse/fixtures/_initial_data.json inhouse/fixtures/_initial_data.json.old')
        local('rm -f dev.db')
    local('python manage.py syncdb --noinput')
    local('python manage.py loaddata %s' % ' '.join(INITIAL_FIXTURES))
    local('python manage.py dumpdata -a -e inhouse.AuthUserGroup -e contenttypes.ContentType --indent=2> inhouse/fixtures/_initial_data.json')


@task
def todos(pylint=CMD_PYLINT):
    """Run pylint and only show todos."""
    lint(pylint, pylint_args='-f colorized -d W,C,R,I,E -e W0511 -r n')
