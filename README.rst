===========
Inhouse-Web
===========

Inhouse-Web is web-based time recording and tracking software built for
companies, that want to track their projects worktime to get an accurate time
billing for their customers. In contrast to other time trackers, Inhouse-Web
will not offer an own task system. It directly synchronizes with other issue
tracking systems like Trac so that each employee can connect their worktime with
already existing tickets for their projects. But, This application is quite more
than a simple time tracking system. You can also manage you companies stock of
soft- and hardware, books and other material used in an IT service company.

The application is written entirely in Python and uses the Django webframework.
It is licensed under the `GNU General Public License v3`__.

Installation
============

Via setup tools
---------------

You can get the latest release via pip oder easy_install::

 $ pip install inhouse-web
 $ easy_install inhouse-web

From source
-----------

Or you can checkout the latest sources from the repository::

 $ git clone git://github.com/hkage/inhouse-web.git

If you checked out the latest sources, you should install the requirements
manually::

 $ pip install -r requirements/stable-req.txt

The tools needed for development can be installed by::

 $ pip install -r requirements/dev-req.txt

Settings
========

Inhouse-Web uses a handful of settings, that are used within the booking and
especially the invoice workflow. The following settings are used:

 * `DEFAULT_COEFFICIENT_SATURDAY`: (default 1.25) The multiplier used for bookings
   created on saturday. E.g. 5 bookable hours created on a saturday will be
   calculated as 6.25 hours.
 * `DEFAULT_COEFFICIENT_SUNDAY`: (default 1.5) The multiplier for bookings created
   on sundays.
 * `DEFAULT_COEFFICIENT_PROJECT_STEP`:

Running
===========

To run the application in development mode, simply type::

 $ fab devserver


__ http://www.gnu.org/licenses/gpl.html
