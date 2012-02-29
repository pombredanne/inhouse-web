# -*- coding: utf-8 -*-

"""Admin models."""

# ignore missing constructors in this module, pylint: disable=W0232
# ignore too few public methods, pylint: disable=R0903
# ignore too many public methods, pylint: disable=R0904

from django import forms
from django.db.models import Q
from django.contrib import admin
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _

from reversion.admin import VersionAdmin

from inhouse.templatetags.utils import format_minutes_to_time
from inhouse import models


# Custom actions

def edit_bookings(modeladmin, request, queryset):
    ids = [booking.id for booking in queryset]
    #url = HttpResponseRedirect(reverse('inhouse.admin_views.edit_bookings'))
    url = "%s?id=" % reverse('inhouse.admin_views.edit_bookings')
    url += "&id=".join(str(x) for x in ids)
    return HttpResponseRedirect(url)
edit_bookings.short_description = _(u'Edit selected bookings')


class ModelAdmin(admin.ModelAdmin):

    def save_model(self, request, obj, form, change):
        obj.save()
        #super(ModelAdmin, self).save_model(request, obj, form, change)


class AddressAdmin(ModelAdmin):

    fieldsets = (
        (None, {
            'fields': ('name1',
                       'name2',
                       'name3',
                       'name4',
                       'street',
                       'zip_code',
                       'city',
                       'country',
                       'group',
                       )}),
        (_(u'Box office'), {
            'fields': ('post_office_box',
                       'box_zip_code',
                       )}),
        (_(u'Timestamp'), {
            'classes': ('collapse',),
            'fields': ('created',
                       'created_by',
                       'modified',
                       'modified_by'
                       )}),
    )
    list_display = ('id', 'name1', 'name2', 'name3', 'name4', 'street',
                    'zip_code', 'city', 'country', 'group', 'created',
                    'modified')
    list_display_links = ('id', 'name1', 'name2', 'name3', 'name4')
    list_filter = ['group']
    ordering = ['id']
    readonly_fields = ('created', 'created_by', 'modified', 'modified_by')


class AddressGroupAdmin(ModelAdmin):

    list_display = ('id', 'name', 'description')
    list_display_links = ('id', 'name')
    ordering = ['id']


class BillingTypeAdmin(ModelAdmin):

    list_display = ('id', 'name', 'description')
    list_display_links = ('id', 'name')


class BookingAdmin(VersionAdmin):

    actions = [edit_bookings]
    date_hierarchy = 'created'
    fieldsets = (
        (None, {
            'fields': ('title',
                       'description',
                       'location',
                       )}),
        (_(u'Ticket information'), {
            'fields': ('issue',
            )}),
        (_(u'Details'), {
            'fields': ('day',
                       'project',
                       'step',
            )}),
        (_(u'Time information'), {
            'fields': ('from_time',
                       'to_time',
                       'duration',
            )}),
        (_(u'Billing information'), {
            'classes': ('collapse',),
            'fields': ('invoice',
                       'coefficient',
                       'external_coefficient',
            )}),
        (_(u'Timestamp'), {
            'classes': ('collapse',),
            'fields': ('created',
                       'created_by',
                       'modified',
                       'modified_by'
                       )}),
    )
    list_display = ('id', 'project', 'step', 'get_date', 'get_user',
                    'get_duration', 'get_tracker', 'get_title')
    list_display_links = ('id', 'get_title')
    list_filter = ['project', 'day__user', 'issue__tracker', 'invoice']
    ordering = ['id']
    raw_id_fields = ['issue', 'step', 'day', 'invoice']
    readonly_fields = ('created', 'created_by', 'modified', 'modified_by')
    search_fields = ['title', 'description', 'issue__title',
                     'issue__description', 'issue__no', 'issue__master']

    def get_date(self, booking): # pylint: disable=R0201
        return booking.day.date
    get_date.short_description = _(u'Date')
    get_date.admin_order_field = 'day__date'

    def get_duration(self, booking): # pylint: disable=R0201
        return format_minutes_to_time(booking.duration)
    get_duration.admin_order_field = 'duration'
    get_duration.short_description = _(u'Duration')

    def get_title(self, booking): # pylint: disable=R0201
        return booking.get_title()
    get_title.short_description = _(u'Activity')

    def get_tracker(self, booking): # pylint: disable=R0201
        if booking.issue:
            return booking.issue.tracker.name
        else:
            return ''
    get_tracker.short_description = _(u'Tracker')
    get_tracker.admin_order_field = 'issue__tracker__name'

    def get_user(self, booking): # pylint: disable=R0201
        return booking.day.user
    get_user.short_description = _(u'User')
    get_user.admin_order_field = 'day__user'

    def save_model(self, request, obj, form, change):
        position = request.POST.get('position')
        if not position:
            obj.next_position()
            obj.save()


class CommissionStatusAdmin(ModelAdmin):

    list_display = ('id', 'name', 'description')
    list_display_links = ('id', 'name')
    ordering = ['id']


class CompanyAdmin(ModelAdmin):
    """Admin class for model :class:`Company`"""

    fieldsets = (
        (None, {
            'fields': ('name',
                       'description',
                       )}),
        (_(u'Contact information'), {
            'fields': ('address',
                       'communication',
                       )}),
        (_(u'Bank account'), {
            'fields': ('account_no',
                       'bank_code',
                       'bank',
                       )}),
        (_(u'Timestamp'), {
            'classes': ('collapse',),
            'fields': ('created',
                       'created_by',
                       'modified',
                       'modified_by'
                       )}),
    )
    list_display = ('id', 'name', 'created', 'modified')
    list_display_links = ('id', 'name')
    readonly_fields = ('created', 'created_by', 'modified', 'modified_by')
    raw_id_fields = ['address', 'communication']


class CommunicationAdmin(ModelAdmin):
    """Admin class for model :class:`Communication`"""

    fieldsets = (
        (None, {
            'fields': ('email',
                       'phone_landline',
                       'phone_mobile',
                       'fax',
                       'url'
                       )}),
        (_(u'Timestamp'), {
            'classes': ('collapse',),
            'fields': ('created',
                       'created_by',
                       'modified',
                       'modified_by'
                       )}),
    )
    list_display = ('id', 'email', 'phone_landline', 'phone_mobile', 'fax',
                    'url')
    list_display_links = ('id', 'email')
    readonly_fields = ('created', 'created_by', 'modified', 'modified_by')


class ContactAdmin(ModelAdmin):
    """Admin class for model :class:`Contact`"""

    fieldsets = (
        (None, {
            'fields': ('salutation',
                       'title',
                       'first_name',
                       'last_name',
                       'description'
                       )}),
        (_(u'Contact information'), {
            'fields': ('address',
                       'communication',
                       'birthday',
                       )}),
        (_(u'Company information'), {
            'fields': ('customer',
                       'position',
                       'department',
                       )}),
        (_(u'Timestamp'), {
            'classes': ('collapse',),
            'fields': ('created',
                       'created_by',
                       'modified',
                       'modified_by'
                       )}),
    )
    list_display = ('id', 'salutation', 'title', 'first_name', 'last_name',
                    'customer')
    list_display_links = ('id',)
    raw_id_fields = ['address', 'communication']
    readonly_fields = ('created', 'created_by', 'modified', 'modified_by')


class CountryAdmin(ModelAdmin):

    list_display = ('id', 'name', 'printable_name', 'num_code', 'iso2', 'iso3',
                    'dial_code')
    list_display_links = ('id', 'name' ,'printable_name')


class CustomerAdmin(ModelAdmin):
    """Admin class for model :class:`Customer`"""

    # No deletion allowed.
    actions = None
    fieldsets = (
        (None, {
            'fields': ('name1',
                       'name2',
                       'name3',
                       )}),
        (_(u'Contact information'), {
            'fields': ('salutation',
                       'address',
                       'communication',
                       )}),
        (_(u'Billing'), {
            'fields': ('day_rate',
                       )}),
        (_(u'Timestamp'), {
            'classes': ('collapse',),
            'fields': ('created',
                       'created_by',
                       'modified',
                       'modified_by'
                       )}),
    )
    list_display = ('id', 'name1', 'name2', 'name3', 'created', 'modified')
    list_display_links = ('id', 'name1', 'name2', 'name3')
    #list_filter = []
    ordering = ['id']
    raw_id_fields = ['address', 'communication']
    readonly_fields = ('created', 'created_by', 'modified', 'modified_by')


class DayBookinsInline(admin.TabularInline):

    can_delete = False
    extra = 0
    model = models.Booking
    fields = ('project', 'step', 'duration', 'issue')
    readonly_fields = ('project', 'step', 'duration', 'issue')
    template = 'admin/inhouse/booking/day_tabular_inline.html'


class DayAdmin(ModelAdmin):

    date_hierarchy = 'date'
    fieldsets = (
        (None, {
            'fields': ('user',
                       'date',
                       'locked'
                       )}),
        (_(u'Timestamp'), {
            'classes': ('collapse',),
            'fields': ('created',
                       'created_by',
                       'modified',
                       'modified_by'
                       )}),
    )
    #inlines = [DayBookinsInline]
    list_display = ('id', 'user', 'date', 'locked', 'get_booking_sum',
                    'created', 'modified')
    list_filter = ('user', 'locked')
    readonly_fields = ('created', 'created_by', 'modified', 'modified_by')

    def get_booking_sum(self, day): # pylint: disable=R0201
        """Display the booking time per day.

        The normal frontend validation will not allow more than 24 hours,
        but the backend should display a limit of 24 hours e.g. because of
        backend jobs that created more than 24 hours per day.
        """
        duration = day.get_booking_sum()
        # TODO: Use constant variable
        if duration > 1440:
            color = 'red'
        else:
            color = 'black'
        value = format_minutes_to_time(duration)
        return '<span style="color: %s;">%s</span>' % (color, value)
    get_booking_sum.short_description = _(u'Duration')
    get_booking_sum.allow_tags = True


class DepartmentUserInline(admin.TabularInline):

    model = models.DepartmentUser


class DepartmentAdmin(ModelAdmin):

    fieldsets = (
        (None, {
            'fields': ('name',
                       )}),
        (_(u'Timestamp'), {
            'classes': ('collapse',),
            'fields': ('created',
                       'created_by',
                       'modified',
                       'modified_by'
                       )}),
    )
    #inlines = [DepartmentUserInline]
    list_display = ('id', 'name', 'created', 'modified')
    list_display_links = ('id', 'name')
    ordering = ['name']
    readonly_fields = ('created', 'created_by', 'modified', 'modified_by')


class DepartmentUserForm(forms.ModelForm):
    """Form validation for :class:`DepartmentUserAdmin`"""

    class Meta:
        model = models.DepartmentUser

    def clean(self, *args, **kwds):
        data = self.cleaned_data
        query = models.DepartmentUser.objects.filter(
            user=data['user'], department=data['department'])
        if query.count() == 1 and self.instance.pk is None:
            raise forms.ValidationError(
                'The user "%s" is already a member in the department "%s".'
                % (data['user'], data['department']))
        return data


class DepartmentUserAdmin(ModelAdmin):

    fieldsets = (
        (None, {
            'fields': ('department',
                       'user',
                       )}),
        (_(u'Timestamp'), {
            'classes': ('collapse',),
            'fields': ('created',
                       'created_by',
                       'modified',
                       'modified_by'
                       )}),
    )
    form = DepartmentUserForm
    list_filter = ['department', 'user']
    list_display = ('id', 'department', 'user')
    list_display_links = ('id',)
    readonly_fields = ('created', 'created_by', 'modified', 'modified_by')


class InvoiceAdmin(ModelAdmin):

    fieldsets = (
        (None, {
            'fields': ('project',
                       'internal_no',
                       'valid_from',
                       'valid_to',
                       )}),
        (_(u'Timestamp'), {
            'classes': ('collapse',),
            'fields': ('created',
                       'created_by',
                       'modified',
                       'modified_by'
                       )}),
    )
    list_display = ('id', 'project', 'internal_no', 'valid_from', 'valid_to',
                    'created', 'modified')
    list_display_links = ('id',)
    list_filter = ('project',)
    readonly_fields = ('created', 'created_by', 'modified', 'modified_by')


class NewsGroupAdmin(ModelAdmin):

    fieldsets = (
        (None, {
            'fields': ('news',
                       'group',
                       'priority',
                       )}),
        (_(u'Timestamp'), {
            'classes': ('collapse',),
            'fields': ('created',
                       'created_by',
                       'modified',
                       'modified_by'
                       )}),
    )
    list_display = ('id', 'news', 'group', 'priority')
    list_display_links = ('id',)
    readonly_fields = ('created', 'created_by', 'modified', 'modified_by')


class NewsGroupInline(admin.TabularInline):

    model = models.NewsGroup
    fields = ['group', 'priority']


class NewsAdmin(ModelAdmin):

    fieldsets = (
        (None, {
            'fields': ('title',
                       'message',
                       'valid_from',
                       'valid_to',
                       )}),
        (_(u'Timestamp'), {
            'classes': ('collapse',),
            'fields': ('created',
                       'created_by',
                       'modified',
                       'modified_by'
                       )}),
    )
    inlines = [NewsGroupInline]
    list_display = ('id', 'title', 'valid_from', 'valid_to', 'created',
                    'modified')
    list_display_links = ('id', 'title')
    readonly_fields = ('created', 'created_by', 'modified', 'modified_by')


class ProjectForm(forms.ModelForm):

    class Meta:
        model = models.Project

    def clean(self):
        pass


class ProjectAdmin(ModelAdmin):

    # No deletion allowed. Projects can only be set inactive.
    actions = None
    date_hierarchy = 'created'
    fieldsets = (
        (None, {
            'fields': ('name',
                       'key',
                       'image',
                       'description',
                       'type',
                       'status',
                       'master',
                       'department',
                       'manager',
                       )}),
        (_(u'Customer'), {
            'fields': ('customer',
                       'contact',
                       )}),
        (_(u'Billing'), {
            'classes': ('collapse',),
            'fields': ('billing_type',
                       'commission_status',
                       'coefficient_saturday',
                       'coefficient_sunday'
                       )}),
        (_(u'Timestamp'), {
            'classes': ('collapse',),
            'fields': ('created',
                       'created_by',
                       'modified',
                       'modified_by'
                       )}),
    )
    #form = ProjectForm
    list_display = ('id', 'name', 'key', 'customer', 'type', 'colored_status',
                    'manager', 'created', 'modified')
    list_display_links = ('id', 'name')
    # TODO: Department filter is not working properly
    list_filter = ['status', 'type', 'customer']
    #list_filter = ['status', 'type', 'customer', 'department']
    list_select_related = True
    ordering = ['name']
    raw_id_fields = ['customer', 'contact']
    readonly_fields = ('created', 'created_by', 'modified', 'modified_by')
    search_fields = ['name', 'description']

    def colored_status(self, project): # pylint: disable=R0201
        if project.status in models.PROJECT_INACTIVE_STATUS:
            color = 'red'
        elif project.status in models.PROJECT_ACTIVE_STATUS:
            color = 'green'
        else:
            return project.status
        return '<span style="color: %s;">%s</span>' % (color, project.status)
    colored_status.allow_tags = True
    colored_status.admin_order_field = 'status'
    colored_status.short_description = _(u'Status')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not request.user.is_superuser:
            if db_field.name == 'department':
                query = models.Department.objects.filter(
                    departmentuser=request.user)
                #query = query.values_list('id')
                #kwargs['queryset'] = query
                #kwargs['to_field_name'] = 'name'
                return forms.ModelChoiceField(
                    queryset=query, required=not db_field.blank,
                    initial=db_field.primary_key)
                #return db_field.formfield(**kwargs)
            elif db_field.name == 'master':
                query = models.Project.objects.filter(
                    department__departmentuser=request.user)
                #query = query.values_list('id')
                #kwargs['queryset'] = query
                #kwargs['to_field_name'] = 'name'
                #kwargs['initial'] = db_field.primary_key
                #kwargs['empty_label'] = db_field.blank and _('None') or None
                return forms.ModelChoiceField(
                    queryset=query, required=not db_field.blank,
                    initial=db_field.primary_key)
                #return db_field.formfield(**kwargs)
        return super(ProjectAdmin, self).formfield_for_foreignkey(
            db_field, request, **kwargs)

    def queryset(self, request):
        query = super(ProjectAdmin, self).queryset(request)
        if request.user.is_superuser:
            return query
        # If the user is not an administrator, filter the project list
        # by his department assignments and projects without department
        # assignment.
        query = models.Project.objects.filter(
            Q(department__departmentuser=request.user) |
            Q(department=None))
        return query

    def save_model(self, request, obj, form, change):
        self_referenced = False
        master = request.POST.get('master')
        project_manager = request.POST.get('project_manager')
        if not master:
            # Create a self reference if no master is given
            self_referenced = True
        if not change and not project_manager:
            obj.manager = request.user
        obj.save()
        if self_referenced:
            obj.master = obj
            obj.save()


class ProjectRateForm(forms.ModelForm):
    """Validation form for :class:`ProjectRate`."""

    class Meta:
        model = models.ProjectRate

    def clean(self, *args, **kwds):
        data = self.cleaned_data
        project = data['project']
        valid_from = data['valid_from']
        valid_to = data['valid_to']
        print valid_from, valid_to
        if valid_from > valid_to:
            raise forms.ValidationError(_(u'"Valid from" must be smaller than'
                                          u' "valid to".'))
        return data


class ProjectRateAdmin(ModelAdmin):

    fieldsets = (
        (None, {
            'fields': ('project',
                       'valid_from',
                       'valid_to',
                       'hour_rate',
                       )}),
        (_(u'Timestamp'), {
            'classes': ('collapse',),
            'fields': ('created',
                       'created_by',
                       'modified',
                       'modified_by'
                       )}),
    )
    form = ProjectRateForm
    list_display = ('id', 'project', 'valid_from', 'valid_to', 'hour_rate',
                    'created', 'modified')
    list_display_links = ('id',)
    list_filter = ('project',)
    ordering = ('project', '-valid_from')
    readonly_fields = ('created', 'created_by', 'modified', 'modified_by')


class ProjectStepAdmin(ModelAdmin):

    fieldsets = (
        (None, {
            'fields': ('name',
                       'description',
                       'project',
                       'status',
                       )}),
        (_(u'Billing information'), {
            'classes': ('collapse',),
            'fields': ('coefficient',
                       'duration',
                       'flat_rate',
                       'day_rate',
                       )}),
        (_(u'Timestamp'), {
            'classes': ('collapse',),
            'fields': ('created',
                       'created_by',
                       'modified',
                       'modified_by'
                       )}),
    )
    list_display = ('id', 'project', 'name', 'position', 'status', 'created',
                    'modified')
    list_display_links = ('id', 'name')
    list_filter = ['project', 'status',]
    ordering = ('project', 'position')
    readonly_fields = ('created', 'created_by', 'modified', 'modified_by')

    def save_model(self, request, obj, form, change):
        # TODO: Only set if not given!
        if not change:
            # Determine the step`s next position
            obj.next_position()
        obj.save()


class ProjectStepTemplateAdmin(ModelAdmin):

    fieldsets = (
        (None, {
            'fields': ('name',
                       'description',
                       )}),
        (_(u'Timestamp'), {
            'classes': ('collapse',),
            'fields': ('created',
                       'created_by',
                       'modified',
                       'modified_by'
                       )}),
    )
    list_display = ('id', 'name', 'created', 'modified')
    list_display_links = ('id', 'name')
    ordering = ('name',)
    readonly_fields = ('created', 'created_by', 'modified', 'modified_by')


class ProjectTrackerForm(forms.ModelForm):
    """Form validation for :class:`ProjectTracker`"""

    class Meta:
        model = models.ProjectTracker

    def clean(self, *args, **kwds):
        data = self.cleaned_data
        # Validates, that project/tracker is unique
        query = models.ProjectTracker.objects.filter(
            project=data['project'],
            tracker=data['tracker'])
        if query.count() == 1 and self.instance.pk is None:
            # Raise only if it's a new data set
            raise forms.ValidationError(
                'The project "%s" is already assigned to the issue tracker "%s"'
                % (data['project'], data['tracker']))
        return data


class ProjectTrackerAdmin(ModelAdmin):

    fieldsets = (
        (None, {
            'fields': ('project',
                       'tracker',
                       )}),
        (_(u'Timestamp'), {
            'classes': ('collapse',),
            'fields': ('created',
                       'created_by',
                       'modified',
                       'modified_by'
                       )}),
    )
    form = ProjectTrackerForm
    list_display = ('id', 'project', 'tracker', 'created', 'modified')
    list_display_links = ('id',)
    readonly_fields = ('created', 'created_by', 'modified', 'modified_by')


class ProjectTypeAdmin(ModelAdmin):

    list_display = ('id', 'name', 'description')
    list_display_links = ('id', 'name')
    ordering = ['id']


class ProjectUserForm(forms.ModelForm):
    """Form validation for :class:`ProjectUserAdmin`"""

    class Meta:
        model = models.ProjectUser

    def clean(self, *args, **kwds):
        data = self.cleaned_data
        chosen_project = data['project']
        if not chosen_project:
            return data
        # Validates, that user/project is unique
        query = models.ProjectUser.objects.filter(
            project=chosen_project,
            user=data['user'])
        if query.count() == 1 and self.instance.pk is None:
            # Raise only if it's a new data set
            raise forms.ValidationError(
                _(u'The user "%(user)s" is already a member of the project'
                  u' "%(project)s".')
                % {'user': data['user'], 'project': chosen_project})
        chosen_step = data['default_step']
        if chosen_step and chosen_step.id:
            if chosen_step.project != chosen_project:
                raise forms.ValidationError(
                    _(u'The chosen step "%(step)s" does not belong to the'
                      u' project "%(project)s".')
                    % {'step': chosen_step, 'project': chosen_project})
        return data


class ProjectUserAdmin(ModelAdmin):

    fieldsets = (
        (None, {
            'fields': ('project',
                       'user',
                       'default_step',
                       )}),
        (_(u'Timestamp'), {
            'classes': ('collapse',),
            'fields': ('created',
                       'created_by',
                       'modified',
                       'modified_by'
                       )}),
    )
    form = ProjectUserForm
    list_display = ('id', 'project', 'user', 'default_step', 'created',
                    'modified')
    list_display_links = ('id',)
    list_filter = ['project', 'user']
    raw_id_fields = ['default_step']
    readonly_fields = ('created', 'created_by', 'modified', 'modified_by')


class TimerAdmin(ModelAdmin):

    fieldsets = (
        (None, {
            'fields': ('start_time',
                       'active',
                       'title',
                       'duration'
                       )}),
        (_(u'Timestamp'), {
            'classes': ('collapse',),
            'fields': ('created',
                       'created_by',
                       'modified',
                       'modified_by'
                       )}),
    )
    list_display = ('id', 'start_time', 'active', 'title', 'duration',
                    'created', 'modified')
    list_display_links = ('id',)
    readonly_fields = ('created', 'created_by', 'modified', 'modified_by')


class UserProfileAdmin(ModelAdmin):

    fieldsets = (
        (None, {
            'fields': ('user',
                       'birthday'
                       )}),
        (_(u'Conact information'), {
            'fields': ('salutation',
                       'address',
                       'communication',
                       )}),
        (_(u'Company information'), {
            'fields': ('company',
                       'personnel_no',
                       'job',
                       'day_rate',
                       'hours_per_week'
                       )}),
        (_(u'Timestamp'), {
            'classes': ('collapse',),
            'fields': ('created',
                       'created_by',
                       'modified',
                       'modified_by'
                       )}),
    )
    list_display = ('id', 'personnel_no', 'user', 'birthday',
                    'address', 'company', 'job', 'day_rate', 'created',
                    'modified')
    list_display_links = ('id', 'user')
    list_filter = ('company',)
    raw_id_fields = ['address', 'communication', 'company']
    readonly_fields = ('created', 'created_by', 'modified', 'modified_by')


admin.site.register(models.Address, AddressAdmin)
admin.site.register(models.AddressGroup, AddressGroupAdmin)
admin.site.register(models.BillingType, BillingTypeAdmin)
admin.site.register(models.Booking, BookingAdmin)
admin.site.register(models.Communication, CommunicationAdmin)
admin.site.register(models.CommissionStatus, CommissionStatusAdmin)
admin.site.register(models.Company, CompanyAdmin)
admin.site.register(models.Contact, ContactAdmin)
admin.site.register(models.Country, CountryAdmin)
admin.site.register(models.Customer, CustomerAdmin)
admin.site.register(models.Day, DayAdmin)
# DefaultProject
admin.site.register(models.Department, DepartmentAdmin)
admin.site.register(models.DepartmentUser, DepartmentUserAdmin)
admin.site.register(models.Invoice, InvoiceAdmin)
admin.site.register(models.News, NewsAdmin)
admin.site.register(models.NewsGroup, NewsGroupAdmin)
admin.site.register(models.Project, ProjectAdmin)
admin.site.register(models.ProjectRate, ProjectRateAdmin)
admin.site.register(models.ProjectStep, ProjectStepAdmin)
admin.site.register(models.ProjectStepTemplate, ProjectStepTemplateAdmin)
admin.site.register(models.ProjectTracker, ProjectTrackerAdmin)
admin.site.register(models.ProjectType, ProjectTypeAdmin)
admin.site.register(models.ProjectUser, ProjectUserAdmin)
# ProjectUserRate
# Salutation
admin.site.register(models.Timer, TimerAdmin)
admin.site.register(models.UserProfile, UserProfileAdmin)
