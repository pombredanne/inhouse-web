# -*- coding: utf-8 -*-

"""Model definitions."""

import calendar
import cgi
import datetime

from django.conf import settings
from django.contrib.auth.models import Group, User
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import ugettext_lazy as _

from issues.models import Issue, Tracker
from inhouse.exceptions import InhouseModelError

# Languages
LANGUAGE_CHOICES = [(x[0], _(x[1])) for x in settings.LANGUAGES]

# Project status
PROJECT_STATUS_OPEN = 1
PROJECT_STATUS_DELETED = 2
PROJECT_STATUS_IDLE = 3
PROJECT_STATUS_CLOSED = 4

PROJECT_STATUS_CHOICES = (
    (PROJECT_STATUS_OPEN, _(u'Open')),
    (PROJECT_STATUS_DELETED, _(u'Deleted')),
    (PROJECT_STATUS_IDLE, _(u'Idle')),
    (PROJECT_STATUS_CLOSED, _(u'Closed'))
)

PROJECT_ACTIVE_STATUS = (
    PROJECT_STATUS_OPEN,
)

PROJECT_INACTIVE_STATUS = (
    PROJECT_STATUS_DELETED,
    PROJECT_STATUS_IDLE,
    PROJECT_STATUS_CLOSED,
)

# Step status
STEP_STATUS_OPEN = 1
STEP_STATUS_CLOSED = 2

STEP_STATUS_CHOICES = (
    (STEP_STATUS_OPEN, _(u'Open')),
    (STEP_STATUS_CLOSED, _(u'Closed')),
)

# Priorities
PRIORITY_CHOICES = (
    (1, _(u'Low')),
    (2, _(u'Normal')),
    (3, _(u'High'))
)

# Monkey-patch DEFAULT_NAMES for Meta options. Otherwise
# db_column_prefix would raise an error.
from django.db.models import options
options.DEFAULT_NAMES += ('db_column_prefix',)


def _create_column_prefix_mc(base_cls, inject=False):
    """Creates and returns a meta class for models.

    The purpose of this function is to take the base_cls argument to
    avoid hierarchy problems with different meta classes.
    """

    class ColumnPrefixModelMeta(base_cls):
        """Metaclass that provides an easy way to set column prefixes.

        With this metaclass it's possible to use Meta.db_column_prefix to
        define a prefix that should be used for all column names in this
        model.

        If db_column is not set it is generated from the attribute
        name. Then the metaclass checks wether db_column starts with the
        given prefix.

        Note: To make this work you'll need to monkey-patch the available
        Meta options like this:

            from django.db.models import options
            options.DEFAULT_NAMES += ('db_column_prefix',)
        """

        def __new__(cls, name, bases, attrs):  # pylint: disable=C0203,E1002
            # accessing restricted _meta is intended: pylint:disable=W0212
            if inject:
                for attr_name, field in (
                    ('created_by', models.IntegerField(
                        blank=True, null=True, editable=False,
                        db_column='cruid')),
                    ('modified_by', models.IntegerField(
                        blank=True, null=True, editable=False,
                        db_column='upduid')),
                    ('created', models.DateTimeField(
                        auto_now_add=True, db_column='crdate')),
                    ('modified', models.DateTimeField(
                        auto_now=True, db_column='upddate'))):
                    attrs[attr_name] = field
            new_cls = super(ColumnPrefixModelMeta, cls).__new__(
                cls, name, bases, attrs)
            prefix = getattr(new_cls._meta, 'db_column_prefix', None)
            # db_column_prefix on abstract base classes will be ignored.
            if not new_cls._meta.abstract and prefix is not None:
                # Shamelessly stolen from ModelBase.__new__:
                new_fields = new_cls._meta.local_fields + \
                             new_cls._meta.local_many_to_many + \
                             new_cls._meta.virtual_fields
                for field in new_fields:
                    if isinstance(field, generic.GenericForeignKey):
                        continue
                    if field.db_column is None:
                        field.db_column = field.get_attname()
                    if not field.db_column.startswith(prefix):
                        field.db_column = '%s%s' % (prefix, field.db_column)
                    # This sets field.column which is needed for build SQL
                    # statements
                    field.set_attributes_from_name(field.name)
            return new_cls
    return ColumnPrefixModelMeta


class DefaultInfo(models.Model):
    """Base class for all models in this module.

    This base class provides default fields that should be used by all
    models in this module.
    """

    __metaclass__ = _create_column_prefix_mc(models.base.ModelBase)

    created_by = models.IntegerField(
        blank=True, null=True, editable=False,
        db_column='cruid')  # references User
    modified_by = models.IntegerField(
        blank=True, null=True, editable=False,
        db_column='upduid')  # references User
    created = models.DateTimeField(auto_now_add=True, db_column='crdate')
    modified = models.DateTimeField(auto_now=True, db_column='upddate')

    class Meta:
        abstract = True

    @classmethod
    def new(cls, **kwds):
        """Initializes and returns a new instance.

        The new instance is already saved to the database.

        This method can be overridden by subclasses to create related
        objects.
        """
        obj = cls(**kwds)
        obj.save()
        return obj

    def save(self, *args, **kwargs):
        self.full_clean()
        super(DefaultInfo, self).save(*args, **kwargs)


class StarredItemMixin(object):
    """Mixin class for starrable items."""

    @classmethod
    def get_starred(cls, user):
        """Returns all objects from this class, that are starred by the user.

        :param user: A :class:`User` instance
        :returns: Query of :class:`StarredItem`
        """
        ct = ContentType.objects.get_for_model(cls)
        #return ct.starreditem_set.filter(user=user)
        ids = ct.starreditem_set.filter(user=user).values_list('object_id')
        return cls.objects.filter(id__in=ids)

    def is_starred(self, user):
        """Checks, wheter the object is starred by the user.

        :returns: ``True`` or ``False``
        """
        ct = ContentType.objects.get_for_model(self)
        query = StarredItem.objects.filter(content_type__pk=ct.id,
            object_id=self.id, user=user)
        return query.count() == 1

    def add_star(self, user):
        """Add an :class:`StarredItem` for an object.

        :param user: A :class:`User` instance
        """
        if self.is_starred(user):
            # Prevent multiple entries
            return
        star = StarredItem(content_object=self)
        star.user = user
        star.save()

    def remove_star(self, user):
        """Delete the StarredItem for an object.

        :params user: A :class:`User` instance
        """
        ct = ContentType.objects.get_for_model(self)
        query = StarredItem.objects.filter(content_type__pk=ct.id,
            object_id=self.id, user=user)
        if query.count() == 1:
            query.delete()


class Address(DefaultInfo):
    group = models.ForeignKey('AddressGroup', db_column='adgid',
                              blank=True, null=True,
                              verbose_name=_(u'Address group'))
    name1 = models.CharField(max_length=200, db_column='name1',
                             verbose_name=_(u'Name'))
    name2 = models.CharField(max_length=200, db_column='name2',
                             blank=True, null=True,
                             verbose_name=_(u'Name'))
    name3 = models.CharField(max_length=200, db_column='name3',
                             blank=True, null=True,
                             verbose_name=_(u'Name'))
    name4 = models.CharField(max_length=200, db_column='name4',
                             blank=True, null=True,
                             verbose_name=_(u'Name'))
    street = models.CharField(db_column='strasse', max_length=100,
                              blank=True, null=True,
                              verbose_name=_(u'Street'))
    zip_code = models.CharField(db_column='plz', max_length=30,
                                blank=True, null=True,
                                verbose_name=_(u'ZIP code'))
    city = models.CharField(db_column='ort', max_length=50,
                            blank=True, null=True,
                            verbose_name=_(u'City'))
    country = models.ForeignKey('Country', db_column='laid',
                                blank=True, null=True,
                                verbose_name=_(u'Country'))
    post_office_box = models.CharField(db_column='pf', max_length=100,
                                       blank=True, null=True,
                                       verbose_name=_(u'Post office box'))
    box_zip_code = models.IntegerField(db_column='pfplz',
                                       blank=True, null=True,
                                       verbose_name=_(u'Box office code'))

    class Meta:
        db_table = u'adresse'
        db_column_prefix = u'adr_'
        verbose_name = _(u'Address')
        verbose_name_plural = _(u'Addresses')

    def __unicode__(self):
        return self.name1

    def get_addressstring(self, sep='<br />', *args, **kwds):
        """Returns an address as one single string.

        :param sep: Seperator string after earch address element.
        :returns: String with address information.
        """
        data = self.get_addresstuple(*args, **kwds)
        if '<' in sep:  # Separator is HTML/XML
            frmt = cgi.escape
        else:
            frmt = lambda x: x
        return sep.join(frmt(part) for part in data if part is not None)

    def get_addresstuple(self, names_only=False):
        """Return an address as a tuple.

        :param names_only: Return only the name part of the address

        :returns: Tuple with address elements
        """
        t = []
        if self.name1:
            t.append(self.name1)
        if self.name2:
            t.append(self.name2)
        if self.name3:
            t.append(self.name3)
        if self.name4:
            t.append(self.name4)
        if not names_only:
            if self.street:
                t.append(self.street)
            if self.city and not self.zip_code:
                t.append(self.city)
            elif self.city and self.zip_code:
                t.append('%s %s' % (self.zip_code, self.city))
            if self.country:
                t.append(str(self.country))
        return tuple(t)

    def get_join_name(self, join_char=''):
        """Return only the name fields joined together.

        :param join_char: The character used to join the name fields.
        :returns: String with address name fields.
        """
        parts = [self.name1, self.name2,
                 self.name3, self.name4]
        return join_char.join(cgi.escape(part) for part in parts
                              if part is not None)

    get_join_name_html = lambda me: me.get_join_name('<br />')


class AddressGroup(models.Model):
    name = models.CharField(db_column='kbez', max_length=100,
                            unique=True, verbose_name=_(u'Name'))
    description = models.CharField(max_length=255, db_column='bez',
                                   blank=True, null=True,
                                   verbose_name=_(u'Description'))

    class Meta:
        db_table = u'k_adgrp'
        db_column_prefix = u'adg_'
        ordering = ('name',)
        verbose_name = _(u'Address group')
        verbose_name_plural = _(u'Address groups')

    def __unicode__(self):
        return self.name


class AuthUserGroup(models.Model):
    """Unmanaged model for Django's group/user relation.

    Just to get the ID's.
    """

    user = models.ForeignKey(User, verbose_name=_(u'User'))
    group = models.ForeignKey(Group, verbose_name=_(u'Group'))

    class Meta:
        db_table = 'auth_user_groups'
        managed = False


class BillingType(models.Model):
    name = models.CharField(db_column='kbez', max_length=100,
                            unique=True, verbose_name=_(u'Name'))
    description = models.CharField(max_length=255, db_column='bez',
                                   blank=True, null=True,
                                   verbose_name=_(u'Description'))

    class Meta:
        db_table = u'k_abrechnungsart'
        db_column_prefix = u'aba_'
        ordering = ('name',)
        verbose_name = _(u'Billing type')
        verbose_name_plural = _(u'Billing types')

    def __unicode__(self):
        return self.name


class Booking(DefaultInfo):
    title = models.CharField(db_column='titel', max_length=255,
                             verbose_name=_(u'Title'))
    description = models.TextField(db_column='bem',
                                   verbose_name=_(u'Description'))
    day = models.ForeignKey('Day', db_column='taid',
                            verbose_name=_(u'Day'))
    position = models.IntegerField(db_column='pos',
                                   verbose_name=_(u'Position'))
    project = models.ForeignKey('Project', db_column='prid',
                                verbose_name=_(u'Project'))
    # TODO: Disallow step deletion?
    step = models.ForeignKey('ProjectStep', db_column='psid',
                             blank=True, null=True, on_delete=models.SET_NULL,
                             verbose_name=_(u'Project step'))
    issue = models.ForeignKey(Issue, db_column='tiid', blank=True,
                              null=True, verbose_name=_(u'Issue'))
    from_time = models.TimeField(db_column='von',
                                 blank=True, null=True,
                                 verbose_name=_(u'Start'))
    to_time = models.TimeField(db_column='bis',
                               blank=True, null=True,
                               verbose_name=_(u'End'))
    #from_time = models.DecimalField(db_column='st_von',
                                    #max_digits=5, decimal_places=3,
                                    #blank=True, null=True,
                                    #verbose_name=_(u'From'))
    #to_time = models.DecimalField(db_column='st_bis',
                                  #max_digits=5, decimal_places=3,
                                  #blank=True, null=True,
                                  #verbose_name=_(u'To'))
    duration = models.DecimalField(db_column='std', max_digits=7,
                                   decimal_places=3,
                                   verbose_name=_(u'Duration'))
    location = models.CharField(db_column='ort', max_length=250,
                                blank=True, null=True,)
    #invoice_no = models.IntegerField(db_column='st_rnr',
    #                                 blank=True, null=True,
    #                                 verbose_name=_(u'Invoice no.'))
    invoice = models.ForeignKey('Invoice', db_column='abrid', blank=True,
                                null=True, on_delete=models.SET_NULL,
                                verbose_name=_(u'Invoice'))
    coefficient = models.DecimalField(db_column='faktor', max_digits=4,
                                      decimal_places=2, blank=True, null=True,
                                      verbose_name=_(u'External coefficient'))
    external_coefficient = models.DecimalField(db_column='pfaktor',
                                               max_digits=4, decimal_places=2,
                                               blank=True, null=True,
                                               verbose_name=_(u'Coefficient'))


    #status = models.ForeignKey('BookingStatus', db_column='st_sts')

    class Meta:
        db_table = u'stunde'
        db_column_prefix = u'st_'
        verbose_name = _(u'Booking')
        verbose_name_plural = _(u'Bookings')

    #def __unicode__(self):
        #return self.get_title()

    #@models.permalink
    #def get_absolute_url(self):
        #return '/time/edit/%d' % self.id
        #return reverse('inhouse.views.edit_booking', self.id, [])
        #return ('inhouse.views.edit_booking', [str(self.id)])

    @property
    def is_open(self):
        """Is the booking editable?

        :returns: ``True`` or ``False``
        """
        if (self.project.is_closed or self.day.locked
            or self.step.is_closed or self.invoice):
            return False
        return True

    def get_closing_reason_tuple(self):
        """Return one ore more reasons, why the booking is closed.

        :returns: Tuple with strings
        """
        reasons = []
        if self.is_open:
            return reasons
        if self.day.locked:
            reasons.append(_(u'The day is locked.'))
        if not self.project.is_open:
            reasons.append(_(u'The project is closed or inactive.'))
        if not self.step.is_open:
            reasons.append(_(u'The projectstep is closed.'))
        if self.invoice:
            reasons.append(_(u'The booking has been settled.'))
        return tuple(reasons)

    def get_closing_reason_string(self, sep='<br />'):
        """Return the closing reason(s) as one single string.

        :param sep: Seperator for the elements
        :returns: String
        """
        data = self.get_closing_reason_tuple()
        if '<' in sep:
            frmt = cgi.escape
        else:
            frmt = lambda x: x
        return sep.join(frmt(part) for part in data if part is not None)

    def next_position(self):
        """Set the next available position, depending on the day."""
        bookings = Booking.objects.filter(day=self.day)
        self.position = (bookings.aggregate(models.Max('position'))[
            'position__max'] or 0) + 1


class CommissionStatus(models.Model):
    name = models.CharField(db_column='kbez', max_length=100, unique=True,
                            verbose_name=_(u'Name'))
    description = models.CharField(max_length=255, db_column='bez',
                                   blank=True, null=True,
                                   verbose_name=_(u'Description'))

    class Meta:
        db_table = u'k_beauftragungsstatus'
        db_column_prefix = u'bs_'
        ordering = ('name',)
        verbose_name = _(u'Commission status')
        verbose_name_plural = _(u'Commission status')

    def __unicode__(self):
        return self.name


class Communication(DefaultInfo):
    email = models.EmailField(db_column='email', verbose_name=_(u'E-mail'))
    phone_landline = models.CharField(db_column='tel1', max_length=40,
                                      blank=True, null=True,
                                      verbose_name=_(u'Phone no. (landline)'))
    phone_mobile = models.CharField(db_column='tel2', max_length=40,
                                    blank=True, null=True,
                                    verbose_name=_(u'Phone no. (mobile)'))
    fax = models.CharField(db_column='fax', max_length=40,
                           blank=True, null=True,
                           verbose_name=_(u'Fax no.'))
    url = models.URLField(db_column='url', max_length=200,
                          blank=True, null=True,
                          verbose_name=_(u'URL'))

    class Meta:
        db_table = u'kommunikation'
        db_column_prefix = u'kom_'
        verbose_name = _(u'Communication data')
        verbose_name_plural = _(u'Communication data')

    def __unicode__(self):
        return self.get_as_string(', ')

    def get_as_string(self, sep='<br />'):
        """Return the communication data as one single string.

        :param sep: Separator to use.
        :returns: Single string with data.
        """
        data = self.get_tuple()
        if '<' in sep:
            frmt = cgi.escape
        else:
            frmt = lambda x: x
        return sep.join(frmt(part) for part in data if part is not None)

    def get_tuple(self):
        """Return the communication data as tuple elements.

        :returns: Tuple with data
        """
        t = []
        if self.email:
            t.append(self.email)
        if self.phone_landline:
            t.append(self.phone_landline)
        if self.phone_mobile:
            t.append(self.phone_mobile)
        if self.fax:
            t.append(self.fax)
        if self.url:
            t.append(self.url)
        return tuple(t)


class Company(DefaultInfo):
    name = models.CharField(max_length=400, db_column='fir_name', unique=True,
                            verbose_name=_(u'Name'))
    description = models.TextField(db_column='fir_bez',
                                   blank=True, null=True,
                                   verbose_name=_(u'Description'))
    address = models.ForeignKey('Address', db_column='fir_adrid',
                                verbose_name=_(u'Address'))
    communication = models.ForeignKey('Communication', db_column='fir_komid',
                                      verbose_name=_(u'Communication data'))
    bank = models.CharField(db_column='fir_bbez', max_length=100,
                            blank=True, null=True,
                            verbose_name=_(u'Bank'))
    bank_code = models.CharField(db_column='fir_blz', max_length=8,
                                 blank=True, null=True,
                                 verbose_name=_(u'Bank code no.'))
    account_no = models.CharField(db_column='fir_kto', max_length=10,
                                  blank=True, null=True,
                                  verbose_name=_(u'Account no.'))
    invoice_no = models.IntegerField(db_column='fir_renr',
                                     default=0,
                                     verbose_name=_(u'Invoice no.'))

    # bbez, mwa, mwb, aknr


    class Meta:
        db_table = u'firma'
        db_column_prefix = u'fir_'
        verbose_name = _(u'Company')
        verbose_name_plural = _(u'Companies')

    def __unicode__(self):
        return self.name


class Contact(DefaultInfo):
    salutation = models.ForeignKey('Salutation', blank=True, null=True,
                                   db_column='anid',
                                   verbose_name=_(u'Salutation'))
    title = models.CharField(db_column='titel', max_length=10,
                             blank=True, null=True,
                             verbose_name=_(u'Title'))
    first_name = models.CharField(db_column='vname', max_length=30,
                                  verbose_name=_(u'First name'))
    last_name = models.CharField(db_column='nname', max_length=30,
                                 verbose_name=_(u'Surname'))
    description = models.TextField(db_column='bez',
                                   blank=True, null=True,
                                   verbose_name=_(u'Description'))
    customer = models.ForeignKey('Customer', db_column='knid',
                                 verbose_name=_(u'Customer'))
    position = models.IntegerField(db_column='lfdnr',
                                   verbose_name=_(u'Position'))
    department = models.CharField(db_column='abteilung', max_length=30,
                                  blank=True, null=True,
                                  verbose_name=_(u'Department'))
    address = models.ForeignKey('Address', db_column='adrid',
                                blank=True, null=True,
                                verbose_name=_(u'Address'))
    communication = models.ForeignKey('Communication', db_column='komid',
                                      verbose_name=_(u'Communication data'))
    birthday = models.DateField(db_column='gebdat', blank=True, null=True,
                                verbose_name=_(u'Birthday'))

    class Meta:
        db_table = u'ansprech'
        db_column_prefix = u'as_'
        verbose_name = _(u'Contact')
        verbose_name_plural = _(u'Contacts')

    @property
    def name(self):
        return u' '.join([self.firstname or u'', self.lastname or u''])


class Country(models.Model):
    name = models.CharField(db_column='cid', max_length=100, unique=True,
                            verbose_name=_(u'Name'))
    printable_name = models.CharField(db_column='kbez', max_length=100,
                                      verbose_name=_(u'Printable name'))
    num_code = models.PositiveSmallIntegerField(db_column='nr',
                                                unique=True,
                                                verbose_name=_(u'Numeric code'))
    iso2 = models.CharField(db_column='iso2', max_length=2, unique=True,
                            verbose_name=_(u'CID'))
    iso3 = models.CharField(db_column='iso3', max_length=3, unique=True,
                            verbose_name=_(u'CID'))
    dial_code = models.CharField(db_column='vorwahl', max_length=10,
                                 null=True,
                                 verbose_name=_(u'Dial code'))

    class Meta:
        db_table = u'k_land'
        db_column_prefix = u'la_'
        verbose_name = _(u'Country')
        verbose_name_plural = _(u'Countries')

    def __unicode__(self):
        return self.printable_name


class Customer(DefaultInfo):
    name1 = models.CharField(max_length=400, db_column='name1',
                             verbose_name=_(u'Name'))
    name2 = models.CharField(max_length=200, db_column='name2',
                             blank=True, null=True,
                             verbose_name=_(u'Name'))
    name3 = models.CharField(max_length=200, db_column='name3',
                             blank=True, null=True,
                             verbose_name=_(u'Name'))
    salutation = models.ForeignKey('Salutation', blank=True, null=True,
                                   db_column='anid',
                                   verbose_name=_(u'Salutation'))
    address = models.ForeignKey('Address', db_column='adrid',
                                verbose_name=_(u'Address'))
    communication = models.ForeignKey('Communication', db_column='komid',
                                      blank=True, null=True,
                                      verbose_name=_(u'Communication data'))
    day_rate = models.DecimalField(db_column='tagessatz', max_digits=14,
                                   decimal_places=2, blank=True, null=True,
                                   verbose_name=_(u'Daily rate'))

    # zpoa, tlx, loe, fre1, fre2, fre3, debnr

    class Meta:
        db_table = u'kunde'
        db_column_prefix = u'kn_'
        unique_together = ('name1', 'name2', 'name3')
        verbose_name = _(u'Customer')
        verbose_name_plural = _(u'Customers')

    def __unicode__(self):
        return self.get_join_name(' ')

    def get_nametuple(self):
        """Return all parts of the name as a tuple.

        :returns: Tuple with name elements
        """
        t = []
        if self.name1:
            t.append(self.name1)
        if self.name2:
            t.append(self.name2)
        if self.name3:
            t.append(self.name3)
        return tuple(t)

    def get_join_name(self, join_char=''):
        """Return only the name fields joined together.

        :param join_char: The character used to join the name fields.
        :returns: String with address name fields.
        """
        parts = [self.name1, self.name2, self.name3]
        return join_char.join(cgi.escape(part) for part in parts
                              if part is not None)

    get_join_name_html = lambda me: me.get_join_name('<br />')


class Day(DefaultInfo):
    user = models.ForeignKey(User, verbose_name=_(u'User'))
    date = models.DateField(db_column='dat',
                            verbose_name=_(u'Date'),)
    locked = models.BooleanField(db_column='sperr', default=False,
                                 verbose_name=_(u'Locked?'),)

    class Meta:
        db_table = u'tag'
        db_column_prefix = u'ta_'
        unique_together = ('user', 'date')
        verbose_name = _(u'Day')
        verbose_name_plural = _(u'Days')

    def __unicode__(self):
        return self.slugify()

    def slugify(self):
        """Returns a slugified string of a day.

        :returns: String
        """
        return self.date.strftime('%Y/%m/%d')


class Department(DefaultInfo):
    name = models.CharField(max_length=100, db_column='kbez',
                            unique=True, verbose_name=_(u'Name'))

    class Meta:
        db_table = u'abteilung'
        db_column_prefix = u'abt_'
        verbose_name = _(u'Department')
        verbose_name_plural = _(u'Departments')

    def __unicode__(self):
        return self.name


class DepartmentUser(DefaultInfo):
    department = models.ForeignKey('Department', db_column='abtid')
    user = models.ForeignKey(User, db_column='userid')

    class Meta:
        db_table = u'abteilungnutzer'
        db_column_prefix = u'ppg_'
        unique_together = ('department', 'user')
        verbose_name = _(u'Department member')
        verbose_name_plural = _(u'Department members')

    def __unicode__(self):
        return u'%s:%s' % (self.department, self.user)


class Invoice(DefaultInfo):
    project = models.ForeignKey('Project', db_column='prid',
                                verbose_name=_(u'Project'))
    internal_no = models.IntegerField(db_column='rnr', blank=True,
                                      null=True,
                                      verbose_name=_(u'Internal no.'))
    valid_from = models.DateField(db_column='von',
                                  verbose_name=_(u'From'))
    valid_to = models.DateField(db_column='bis',
                                verbose_name=_(u'To'))

    class Meta:
        db_table = u'abrechnung'
        db_column_prefix = u'abr_'
        verbose_name = _(u'Invoice')
        verbose_name_plural = _(u'Invoices')

    def __unicode__(self):
        if self.project and self.project.key and self.internal_no:
            return '%s-%s' % (self.project.key, self.internal_no)
        else:
            return str(self)


class News(DefaultInfo):
    title = models.CharField(max_length=200, db_column='titel')
    message = models.TextField(db_column='text')
    valid_from = models.DateField(db_column='gueltig_ab', null=True)
    valid_to = models.DateField(db_column='gueltig_bis', null=True,
                                blank=True)

    class Meta:
        db_table = u'neuigkeit'
        db_column_prefix = u'neu_'
        verbose_name = _(u'News')
        verbose_name_plural = _(u'News')


class NewsGroup(DefaultInfo):
    news = models.ForeignKey('News', db_column='neuid',
                             verbose_name=_(u'News'))
    group = models.ForeignKey(Group, db_column='groupid',
                              verbose_name=_(u'Group'))
    priority = models.IntegerField(db_column='prio',
                                   choices=PRIORITY_CHOICES,
                                   default=1,
                                   verbose_name=_(u'Priority'))

    class Meta:
        db_table = u'neuigkeitgruppe'
        db_column_prefix = u'neg_'
        unique_together = ('news', 'group', 'priority')
        verbose_name = _(u'News group')
        verbose_name_plural = _(u'News groups')


class Project(DefaultInfo):
    name = models.CharField(db_column='name', max_length=80,
                            unique=True,
                            verbose_name=_(u'Name'))
    key = models.CharField(db_column='kurz', max_length=12,
                           unique=True, verbose_name=_(u'Key'))
    image = models.ImageField(db_column='bild', blank=True, null=True,
                              upload_to='projects',
                              verbose_name=_(u'Image'))
    description = models.TextField(db_column='bez',
                                   blank=True, null=True,
                                   verbose_name=_(u'Description'))
    customer = models.ForeignKey('Customer', db_column='knid',
                                 verbose_name=_(u'Customer'))
    company = models.ForeignKey('Company', db_column='firid',
                                blank=True, null=True,
                                verbose_name=_(u'Company'))
    contact = models.ForeignKey('Contact', db_column='asid',
                                blank=True, null=True,
                                verbose_name=_(u'Contact'))
    type = models.ForeignKey('ProjectType', db_column='prtid',
                             verbose_name=_(u'Type'))
    #status = models.ForeignKey('ProjectStatus', db_column='prsid',
    #                           verbose_name=_(u'Status'))
    status = models.IntegerField(db_column='srtid',
                                 choices=PROJECT_STATUS_CHOICES,
                                 verbose_name=_(u'Status'))
    master = models.ForeignKey('Project', db_column='erstprid',
                               blank=True, null=True,
                               verbose_name=_(u'Master project'))
    department = models.ForeignKey('Department', db_column='abtid',
                                   blank=True, null=True,
                                   verbose_name=_(u'Department'))
    manager = models.ForeignKey(User, db_column='leitung', blank=True,
                                null=True, verbose_name=_(u'Project Manager'))
    billing_type = models.ForeignKey('BillingType', db_column='abaid',
                                     blank=True, null=True,
                                     verbose_name=_(u'Billing type'))
    commission_status = models.ForeignKey('CommissionStatus',
                                          db_column='bsid',
                                          blank=True, null=True,
                                          verbose_name=_(u'Commission status'))
    coefficient_saturday = models.DecimalField(
        db_column='pr_faktorsamstag',
        verbose_name=_(u'Coefficient (saturday)'),
        max_digits=8, decimal_places=2, default=1)
    coefficient_sunday = models.DecimalField(
        db_column='pr_faktorsonntag',
        verbose_name=_(u'Coefficient (sunday)'),
        max_digits=8, decimal_places=2, default=1)

    # intnummer

    class Meta:
        db_table = u'projekt'
        db_column_prefix = u'pr_'
        ordering = ('id',)
        verbose_name = _(u'Project')
        verbose_name_plural = _(u'Projects')

    def __unicode__(self):
        return self.name

    @classmethod
    def copy(cls, other):
        """Creates a copy of an existing project instance.

        :returns: A new :class:`Project` instance
        """
        new = Project()
        new.name = u'%s \'%s\'' % (_(u'Copy of'), other.name)
        max_id = Project.objects.aggregate(models.Max('id'))['id__max'] or 0
        new.key = u'PR%d' % (max_id + 1)
        new.description = u''
        new.customer = other.customer
        new.company = other.company
        new.contact = other.contact
        new.type = other.type
        new.status = other.status
        new.department = other.department
        new.manager = other.manager
        new.billing_type = other.billing_type
        new.commission_status = other.commission_status
        new.coefficient_saturday = other.coefficient_saturday
        new.coefficient_sunday = other.coefficient_sunday
        return new

    #@models.permalink
    #def get_absolute_url(self):
        #return ('inhouse.views.show_project', [str(self.id)])

    @property
    def is_open(self):
        """Is the project currently active?

        :returns: ``True`` or ``False`
        """
        return self.status in PROJECT_ACTIVE_STATUS

    def get_coefficient(self, step=None, day=None):
        """Returns the billing coefficient for each booking.

        :param step:
        :param day:
        :returns: Coefficient as integer/float
        """
        co_x = 1
        co_y = 1
        if day:
            if day.date.weekday() == calendar.SATURDAY:
                if self.coefficient_saturday:
                    co_x = self.coefficient_saturday
                else:
                    co_x = settings.DEFAULT_COEFFICIENT_SATURDAY
            elif day.date.weekday() == calendar.SUNDAY:
                if self.coefficient_sunday:
                    co_x = self.coefficient_sunday
                else:
                    co_x = settings.DEFAULT_COEFFICIENT_SUNDAY
        if step and step.coefficient:
            co_y = step.coefficient
        return co_x * co_y


class ProjectRate(DefaultInfo):
    project = models.ForeignKey(Project, db_column='prid',
                                verbose_name=_(u'Project'))
    valid_from = models.DateField(db_column='von',
                                  verbose_name=_(u'Valid from'))
    valid_to = models.DateField(db_column='bis',
                                verbose_name=_(u'Valid to'),
                                default=datetime.date(4711, 12, 31))
    hour_rate = models.DecimalField(db_column='stdsatz', max_digits=14,
                                   decimal_places=2,
                                   verbose_name=_(u'Hourly rate'))

    class Meta:
        db_table = u'projektsatz'
        db_column_prefix = u'psa_'
        verbose_name = _(u'Projectrate')
        verbose_name_plural = _(u'Projectrates')


class ProjectStep(DefaultInfo):
    name = models.CharField(db_column='kbez', max_length=100,
                            verbose_name=_(u'Name'))
    description = models.CharField(max_length=255, db_column='bez',
                                   blank=True, null=True,
                                   verbose_name=_(u'Description'))
    project = models.ForeignKey('Project', db_column='prid',
                                verbose_name=_(u'Project'))
    position = models.IntegerField(db_column='pos',
                                   verbose_name=_(u'Position'))
    #status = models.ForeignKey('ProjectStepStatus', db_column='srtid',
    #                           verbose_name=_(u'Status'))
    status = models.IntegerField(db_column='srtid', choices=STEP_STATUS_CHOICES,
                                 verbose_name=_(u'Status'))
    coefficient = models.DecimalField(db_column='faktor', max_digits=5,
                                      decimal_places=4, blank=True, null=True,
                                      verbose_name=_(u'Coefficient'))
    duration = models.IntegerField(db_column='plandauer',
                                   blank=True, null=True,
                                   verbose_name=_(u'Duration'))
    flat_rate = models.DecimalField(db_column='pauschale', max_digits=14,
                                   decimal_places=2, blank=True, null=True,
                                   verbose_name=_(u'Flatrate'))
    day_rate = models.DecimalField(db_column='tagessatz', max_digits=14,
                                   decimal_places=2, blank=True, null=True,
                                   verbose_name=_(u'Daily rate'))

    # intnummer

    class Meta:
        db_table = u'projektschritt'
        db_column_prefix = u'ps_'
        unique_together = ('name', 'project')
        verbose_name = _(u'Project step')
        verbose_name_plural = _(u'Project steps')

    def __unicode__(self):
        return self.name

    @classmethod
    def copy(cls, other):
        """Creates a copy of a step."""
        new = ProjectStep()
        new.name = other.name
        new.description = other.description
        new.status = STEP_STATUS_OPEN
        return new

    @property
    def is_open(self):
        """Is the project step currently open?

        :returns: ``True`` or ``False`
        """
        return self.status == STEP_STATUS_OPEN

    def next_position(self):
        """Set the next free position for a project`s step."""
        steps = ProjectStep.objects.filter(project=self.project)
        # Automatically determine the fields new position
        max = steps.aggregate(models.Max('position'))['position__max'] or 0
        self.position = max + 1


class ProjectStepTemplate(DefaultInfo):
    """Defines a default step, that can be assigned with projects."""
    name = models.CharField(db_column='kbez', max_length=100,
                            verbose_name=_(u'Name'))
    description = models.CharField(max_length=255, db_column='bez',
                                   blank=True, null=True,
                                   verbose_name=_(u'Description'))

    class Meta:
        db_table = u'projektschritttemplate'
        db_column_prefix = u'pst_'
        verbose_name = _(u'Project step template')
        verbose_name_plural = _(u'Project step templates')


#class ProjectStepStatus(models.Model):
#    #id = models.AutoField(db_column='id', primary_key=True,
#    #                      verbose_name=_(u'Id'))
#    name = models.CharField(db_column='kbez', max_length=100,
#                            unique=True, verbose_name=_(u'Name'))
#    description = models.CharField(max_length=255, db_column='bez',
#                                   blank=True, null=True,
#                                   verbose_name=_(u'Description'))
#
#    class Meta:
#        db_table = u'k_schrittstatus'
#        db_column_prefix = u'srt_'
#        verbose_name = _(u'Project step status')
#        verbose_name_plural = _(u'Project step status')
#
#    def __unicode__(self):
#        return self.name


class ProjectTracker(DefaultInfo):
    """Relation for :class:`Project` and :class:`IssueTracker`"""
    tracker = models.ForeignKey(Tracker, db_column='tsyid',
                                verbose_name=_(u'Issue tracker'))
    project = models.ForeignKey('Project', db_column='prid',
                                verbose_name=_(u'Project'))

    class Meta:
        db_table = u'projektticketsystem'
        db_column_prefix = u'pts_'
        unique_together = ('tracker', 'project')
        verbose_name = _(u'Project issue tracker')
        verbose_name_plural = _(u'Project issue tracker')

    def __unicode__(self):
        return u'%s:%s' % (self.project, self.tracker)


class ProjectType(models.Model):
    name = models.CharField(db_column='kbez', max_length=100,
                            unique=True, verbose_name=_(u'Name'))
    description = models.CharField(max_length=255, db_column='bez',
                                   blank=True, null=True,
                                   verbose_name=_(u'Description'))

    class Meta:

        db_table = u'k_projekttyp'
        db_column_prefix = u'prt_'
        ordering = ('name',)
        verbose_name = _(u'Project type')
        verbose_name_plural = _(u'Project types')

    def __unicode__(self):
        return self.name


class ProjectUser(DefaultInfo):
    project = models.ForeignKey('Project', db_column='prid')
    user = models.ForeignKey(User, db_column='userid')
    default_step = models.ForeignKey('ProjectStep', db_column='psid',
                                     blank=True, null=True)

    class Meta:
        db_table = u'projektperson'
        db_column_prefix = u'prp_'
        unique_together = ('project', 'user')
        verbose_name = _(u'Project user')
        verbose_name_plural = _(u'Project users')

    def __unicode__(self):
        return u'%s:%s' % (self.project, self.user)


class ProjectUserRate(DefaultInfo):
    project_user = models.ForeignKey('ProjectUser', db_column='pps_prpid')
    purchase_rate = models.DecimalField(db_column='ek', max_digits=14,
                                   decimal_places=2, null=True,
                                   verbose_name=_(u'Purchase rate'))
    sale_rate = models.DecimalField(db_column='vk', max_digits=14,
                                   decimal_places=2, null=True,
                                   verbose_name=_(u'Sale rate'))
    hours = models.DecimalField(db_column='std', max_digits=7,
                                   decimal_places=3, default=0,
                                   verbose_name=_(u'Hours'))
    hour_rate = models.DecimalField(db_column='stdsatz', max_digits=14,
                                   decimal_places=2, null=True,
                                   verbose_name=_(u'Hourly rate'))
    valid_from = models.DateField(db_column='von',
                                  default=datetime.datetime(1970, 1, 1))
    valid_to = models.DateField(db_column='bis',
                                default=datetime.datetime(4711, 12, 31))

    class Meta:
        db_table = u'projektpersonsatz'
        db_column_prefix = u'pps_'
        verbose_name = _(u'Project user rate')
        verbose_name_plural = _(u'Project user rates')


class Salutation(models.Model):
    short_name = models.CharField(db_column='kurz', max_length=10,
                                  verbose_name=_(u'Short name'))
    name = models.CharField(db_column='kbez', max_length=100,
                            verbose_name=_(u'Name'))
    letter = models.CharField(db_column='brf', max_length=100,
                            verbose_name=_(u'Name'))

    class Meta:
        db_table = u'k_anrede'
        db_column_prefix = u'an_'
        verbose_name = _(u'Salutation')
        verbose_name_plural = _(u'Salutations')

    def __unicode__(self):
        return self.name


class StarredItem(models.Model):

    content_type = models.ForeignKey(ContentType, db_column='contenttype')
    object_id = models.PositiveIntegerField(db_column='objectid')
    content_object = generic.GenericForeignKey('content_type', 'object_id')
    user = models.ForeignKey(User, blank=True, null=True, editable=False,
                             db_column='userid',
                             related_name='%(class)s_creator',
                             verbose_name=_(u'User'))

    class Meta:
        db_table = u'lesezeichen'
        db_column_prefix = u'lez_'
        verbose_name = _(u'Starred item')
        verbose_name_plural = _(u'Starred items')


class Timer(DefaultInfo):
    start_time = models.DateTimeField(db_column='start',
                                      verbose_name=_(u'Start'))
    #end_time = models.DateTimeField(db_column='ende',
                                    #blank=True, null=True,
                                    #verbose_name=_(u'Stop'))
    duration = models.IntegerField(db_column='dauer',
                                   default=0,
                                   verbose_name=_(u'Duration'))
    title = models.CharField(db_column='titel', max_length=255,
                             verbose_name=_(u'Title'))
    # TODO: change to BooleanField and remove status values
    #status = models.IntegerField(db_column='status', choices=TIMER_CHOICES,
                                 #default=1, verbose_name=_(u'Status'))
    active = models.BooleanField(db_column='aktiv', default=False,
                                 verbose_name=_(u'Active'))

    class Meta:
        db_table = u'timer'
        db_column_prefix = u'tim_'
        verbose_name = _(u'Timer')
        verbose_name_plural = _(u'Timer')

    def clear(self):
        """Resets the timer."""
        self.active = False
        self.duration = 0

    def get_elapsed_time(self):
        """Returns the elapsed time.

        :returns: Elapsed time in seconds
        """
        if self.duration > 0:
            if self.active:
                return self.duration + (datetime.datetime.now() - self.start_time).seconds
            else:
                return self.duration
        else:
            if self.active:
                return (datetime.datetime.now() - self.start_time).seconds
            else:
                return 0

    def get_time_tuple(self):
        """Returns a split time information in hours and minutes.

        :return: Tuple with hours, minutes
        """
        minutes = self.duration / 60
        if minutes <= 15:
            # Less then 15 minutes count as 15 minutes
            return 0, 15
        h = minutes // 60
        minutes -= h * 60
        scrap = minutes % 15
        m = (minutes // 15) * 15
        if scrap >= 7.5:
            m += 15
        if m >= 60:
            h += m // 60
            m -= m % 60
        return h, m

    def start(self, title=None):
        """Start a timer.

        :param title: Title of the timer
        """
        if title:
            self.title = title
        self.start_time = datetime.datetime.now()
        self.active = True

    def stop(self):
        """Stop the timer."""
        end_time = datetime.datetime.now()
        self.active = False
        if not self.start_time:
            self.duration = 0
        else:
            self.duration += (end_time - self.start_time).seconds


class UserProfile(DefaultInfo):
    user = models.ForeignKey(User, unique=True,
                             db_column='userid')
    #short_name = models.CharField(db_column='kurz', max_length=8,
    #                              blank=True, null=True,
    #                              unique=True, verbose_name=_(u'Short name'))
    company = models.ForeignKey('Company', db_column='firid', blank=True,
                                null=True, verbose_name=_(u'Company'))
    salutation = models.ForeignKey('Salutation', blank=True, null=True,
                                   db_column='anid',
                                   verbose_name=_(u'Salutation'))
    address = models.ForeignKey('Address', db_column='adrid',
                                blank=True, null=True,
                                verbose_name=_(u'Address'))
    communication = models.ForeignKey('Communication', db_column='komid',
                                      verbose_name=_(u'Communication data'))
    birthday = models.DateField(db_column='gebdat', blank=True, null=True,
                                verbose_name=_(u'Birthday'))
    day_rate = models.DecimalField(db_column='tagkosten', max_digits=14,
                                   decimal_places=2, default=0,
                                   verbose_name=_(u'Daily rate'))
    job = models.CharField(db_column='job', max_length=80, blank=True,
                           null=True, verbose_name=_(u'Job'))
    personnel_no = models.CharField(db_column='personalnr', max_length=250,
                                    blank=True, null=True,
                                    verbose_name=_(u'Personell no.'))
    hours_per_week = models.DecimalField(db_column='stdwoche',
                                         max_digits=14, decimal_places=2,
                                         blank=True, null=True,
                                         verbose_name=_(u'Hours per week'))
    holidays_per_year = models.DecimalField(db_column='urlaub',
                                            max_digits=14, decimal_places=2,
                                            blank=True, null=True,
                                            verbose_name=_(u'Holidays per year'))
    language = models.CharField(db_column='sprache',
        max_length=10, choices=LANGUAGE_CHOICES, verbose_name=_(u'Language'))

    class Meta:
        db_table = u'person'
        db_column_prefix = u'pe_'
        verbose_name = _(u'User profile')
        verbose_name_plural = _(u'User profiles')

    @classmethod
    def new(cls, **kwds):
        try:
            user = kwds['user']
        except KeyError:
            raise InhouseModelError('Required keyword "user" missing')
        try:
            profile = user.get_profile()
            raise InhouseModelError(u'User profil already exists for user %s.'
            % user.username)
        except UserProfile.DoesNotExist:
            pass
        profile = cls(user=user)
        profile.address = Address.new(name1=user.first_name)
        profile.communication = Communication.new(email=user.email)
        if settings.LANGUAGES:
            profile.language = settings.LANGUAGES[0][0]
        else:
            profile.language = 'en'
        profile.save()
        return profile

    def get_news(self):
        pass
