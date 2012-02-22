# -*- coding: utf-8 -*-

from django import forms
from django.contrib.auth.forms import AuthenticationForm as BaseAuthenticationForm
from django.forms import widgets
from django.forms.forms import BoundField as BaseBoundField
from django.forms.util import flatatt
from django.utils.encoding import force_unicode
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from inhouse import models


class BoundField(BaseBoundField):
    """Inhouse specific bound field."""

    def as_widget(self, widget=None, attrs=None, only_initial=False):
        """Renders a field and adds dlgi styles if appropriate."""
        if not widget:
            widget = self.field.widget
        if isinstance(widget, widgets.Input):
            if not attrs:
                # Maintain existing style classes:
                class_attrs = set((
                    self.field.widget.attrs.get('class') or '').split(' '))
                # anf add those for general layout:
                class_attrs.add('input-text')
                attrs = {'class': ' '.join(class_attrs)}
        return BaseBoundField.as_widget(self, widget=widget, attrs=attrs,
                                    only_initial=only_initial)


class InhouseMixin(object):
    """Implements custom form rendering."""

    def __unicode__(self):
        """Renders a Form."""
        output = []
        for name, field in self.fields.items():
            bfield = BoundField(self, field, name)
            if self.check_hide(bfield):
                output.append(unicode(bfield))
            else:
                label = conditional_escape(force_unicode(bfield.label))
                help_text = conditional_escape(force_unicode(bfield.help_text))
                # Only add the suffix if the label does not end in
                # punctuation.
                if self.label_suffix:
                    if label[-1] not in ':?.!':
                        label += self.label_suffix
                req_mark = u''
                if field.required:
                    req_mark = u'*'
                labelcls = 'control-label'
                divcls = 'control-group'
                if bfield.errors:
                    labelcls = labelcls + ' error'
                    label = '! %s' % label
                    divcls = 'control-group error'
                label = bfield.label_tag(u'%s %s' % (label, req_mark),
                                     {'class': labelcls}) or ''
                output.append('<div class="%s">' % divcls)
                output.append(force_unicode(label))
                output.append('<div class="controls">')
                if bfield.errors:
                    bfield.field.widget.attrs['class'] = 'error'
                output.append(unicode(bfield))
                if help_text:
                    output.append('<p class="help-block">%s</p>' % help_text)
                output.append('</div>')
                output.append('</div>')
        return mark_safe(u'\n'.join(output))

    def has_required_fields(self):
        """Checks, if form contains required fields."""
        return any(field.required for field in self.fields.itervalues())

    def set_choices(self, fieldname, choices, default=None, empty_value=None):
        """Sets choices of a field after initialisation."""
        if empty_value:
            choices = [empty_value] + list(choices)
        bound_field = self[fieldname]
        bound_field.field.choices = choices
        if default is not None:
            self.initial[fieldname] = default

    def check_hide(self, bfield):  # pylint: disable=R0201
        """Checks, whether this field should be hidden."""
        if bfield.is_hidden:
            return True
        if (getattr(bfield.field.widget, 'hide_if_one_option', False)
            and len(bfield.field.widget.choices) == 1):
            return True
        return False

    def set_queryset(self, fieldname, queryset):
        """Sets queryset of a field after initialisation."""
        bound_field = self[fieldname]
        bound_field.field.queryset = queryset

    def _clean_fields(self):
        """Like base function, but exclude readonly fields w/o hidden data."""
        super(InhouseMixin, self)._clean_fields()
        for name in self.fields:
            if name not in self.cleaned_data:
                continue
            field = self.fields[name]
            if not getattr(field, '_show_hidden', True):
                del self.cleaned_data[name]

    @property
    def errors_with_prefix(self):
        """Returns dict with errors.

        If the form has a prefix defined, this is added to the keys
        to ensure correct display via javascript.
        """
        if self.prefix is not None:
            dct = {}
            for key, err in self.errors.items():
                if key != '__all__':
                    dct[self.add_prefix(key)] = err
                else:
                    dct[key] = err
            return dct
        else:
            return self.errors


class Form(InhouseMixin, forms.Form):
    """Inhouse specific form."""


class ModelForm(InhouseMixin, forms.ModelForm):
    """Inhouse specific model form."""


class StrippedCharField(forms.CharField):
    """A character field that strips its value."""

    def to_python(self, value):
        value = super(StrippedCharField, self).to_python(value)
        return value.strip() or None


class DatePickerField(forms.DateField):
    """DatePickerField with a Closure DatePicker."""

    def __init__(self, *args, **kwargs):
        if 'widget' not in kwargs:
            kwargs['widget'] = forms.widgets.DateInput(
                attrs={'class': 'datepicker input-date-picker'})
        kwargs['localize'] = kwargs.get('localize', True)
        super(DatePickerField, self).__init__(*args, **kwargs)


class ReadonlyWidget(forms.TextInput):
    """Widget for the representation of readonly content."""

    def __init__(self, *args, **kwargs):
        self._show_hidden = kwargs.pop('hidden_field', True)
        super(ReadonlyWidget, self).__init__(*args, **kwargs)

    def render(self, name, value, attrs=None):
        if value is None:
            value = ''
        final_attrs = self.build_attrs(attrs, type=self.input_type, name=name)
        if value != '':
            # Only add the 'value' attribute if a value is non-empty.
            final_attrs['value'] = force_unicode(self._format_value(value))
        final_attrs['type'] = 'hidden'
        #final_attrs['class'] = 'uneditable-input'
        if 'id' in final_attrs:
            parts = [u'<span id="%s-ro" class="uneditable-input">%s</span>'
                     % (final_attrs['id'], (self._format_value(value)))]
        else:
            parts = [u'<span class="uneditable-input">%s</span>' % self._format_value(value)]
        if self._show_hidden:
            parts.append(u'<input%s />' % flatatt(final_attrs))
        return mark_safe(u''.join(parts))


class ReadonlyDateTimeWidget(ReadonlyWidget):
    """Widget for the readonly rendering of a date time field."""
    format = '%Y-%m-%d %H:%M:%S'
    is_localized = True

    def __init__(self, attrs=None, format=None, **kw):  # pylint: disable=W0622
        # Once format builtin is needed here, the format kw has to be
        # renamed (and W0622 can be enabled again).
        super(ReadonlyDateTimeWidget, self).__init__(attrs, **kw)
        self.formatter = None
        if format is not None:
            self.format = format
            if re.match('^[A-Z][A-Z_]+[A-Z]$', format):
                self.formatter = date_format
            else:
                self.formatter = lambda v, f: v.strftime(f)
            self.manual_format = True
        else:
            self.format = formats.get_format('DATETIME_INPUT_FORMATS')[0]
            self.manual_format = False

    def _format_value(self, value):
        if self.is_localized and not self.manual_format:
            return formats.localize_input(value)
        elif self.formatter is not None:
            value = datetime_safe.new_datetime(value)
            return self.formatter(value, self.format)
        return value

    def _has_changed(self, initial, data):
        # If our field has show_hidden_initial=True, initial will be a string
        # formatted by HiddenInput using formats.localize_input, which is not
        # necessarily the format used for this widget. Attempt to convert it.
        try:
            input_format = formats.get_format('DATETIME_INPUT_FORMATS')[0]
            initial = datetime.datetime(
                *time.strptime(initial, input_format)[:6])
        except (TypeError, ValueError):
            pass
        return super(ReadonlyDateTimeWidget, self)._has_changed(
            self._format_value(initial), data)


class ReadonlySelectWidget(forms.Select):
    """Widget for the representation of readonly content for a select field."""

    def __init__(self, *args, **kwargs):
        self._show_hidden = kwargs.pop('hidden_field', True)
        super(ReadonlySelectWidget, self).__init__(*args, **kwargs)

    def render(self, name, value, attrs=None, choices=()):
        if value is None:
            value = ''
        final_attrs = self.build_attrs(attrs, name=name)
        for choice in self.choices:
            if str(choice[0]) == str(value):
                final_attrs['value'] = value
                value = choice[1]
        final_attrs['type'] = 'hidden'
        parts = [u'<span>%s</span>' % value]
        if self._show_hidden:
            parts.append(u'<input%s />' % flatatt(final_attrs))
        return mark_safe(u''.join(parts))

    # TODO(andi) Remove has_changed(), or document it
    # def has_changed(self):
    #     return False


class ReadonlyBooleanWidget(widgets.CheckboxInput):
    """Widget for the representation of readonly boolean field."""

    def render(self, name, value, attrs=None):
        result = self.check_test(value)
        output = u'<span>%s</span>' % _(u'No')
        if result:
            output = u'<span>%s</span>' % _(u'Yes')
        return mark_safe(output)


class ReadonlyField(forms.Field):
    """Displays a read-only field.

    The default widget is the ReadonlyWidget.

    :param hidden_field: If `True` (the default) a hidden field is
      rendered.
    """

    def __init__(self, *args, **kwargs):
        self._show_hidden = kwargs.pop('hidden_field', False)
        widget = kwargs.pop('widget', None)
        if widget is None:
            widget = ReadonlyWidget(hidden_field=self._show_hidden)
        if not self._show_hidden:
            kwargs['required'] = False
        kwargs['widget'] = widget
        super(ReadonlyField, self).__init__(*args, **kwargs)

    def clean(self, *args, **kwargs):
        """Ignores validation if no hidden field is available."""
        if not self._show_hidden:
            return
        return super(ReadonlyField, self).clean(*args, **kwargs)


class HideIfOneOptionWidget(forms.Select):
    """Widget, that renders itself invisible, if there is only one option."""
    hide_if_one_option = True

    def render(self, name, value, attrs=None, choices=()):
        if len(self.choices) == 1:
            for x in self.choices:
                value = x[0]
            final_attrs = self.build_attrs(
                attrs, type='hidden', name=name)
            if value != '':
                # Only add the 'value' attribute if a value is non-empty.
                final_attrs['value'] = value
            return mark_safe(u'<input%s />' % flatatt(final_attrs))
        else:
            return super(
                HideIfOneOptionWidget, self).render(name, value, attrs=attrs)


class CheckboxSelectMultipleWidget(forms.CheckboxSelectMultiple):
    """Derived class with custom rendering."""

    def render(self, name, value, attrs=None, choices=()):
        """Renders the widgets.

        :param name: Name of the element
        :param value: Value
        :param attrs: Optional attributes for the HTML element
        :param choices: The choice list to use
        """
        if value is None:
            value = []
        has_id = attrs and 'id' in attrs
        final_attrs = self.build_attrs(attrs, name=name)
        output = [u'<div>']
        # Normalize to strings
        str_values = set([force_unicode(v) for v in value])
        for i, (option_value, option_label) in enumerate(chain(
            self.choices, choices)):
            # If an ID attribute was given, add a numeric index as a suffix,
            # so that the checkboxes don't all have the same ID attribute.
            if has_id:
                final_attrs = dict(final_attrs, id='%s_%s' % (attrs['id'],
                                                              option_value))
                label_for = u' for="%s"' % final_attrs['id']
            else:
                label_for = ''
            cbox = forms.CheckboxInput(final_attrs, check_test=lambda value:
                                       value in str_values)
            option_value = force_unicode(option_value)
            option_label = conditional_escape(force_unicode(option_label))
            output.append(u'<div>%s<label%s> %s</label></div>' % (
                cbox.render(name, option_value), label_for, option_label))
        output.append(u'</div>')
        return mark_safe(u'\n'.join(output))






class Address(ModelForm):
    """Address form."""

    name1 = StrippedCharField(max_length=200, required=True, label=_(u'Name'))
    name2 = StrippedCharField(max_length=200, required=False, label=_(u'Name'))
    name3 = StrippedCharField(max_length=200, required=False, label=_(u'Name'))
    name4 = StrippedCharField(max_length=200, required=False, label=_(u'Name'))
    street = StrippedCharField(max_length=100, required=False,
                               label=_(u'Street'))
    zip_code = StrippedCharField(max_length=30, required=False,
                                 help_text=_(u'e.g. 12345'),
                                 widget=forms.TextInput({'class': 'span1'}),
                                 label=_(u'ZIP code'))
    city = StrippedCharField(max_length=50, required=False, label=_(u'City'))
    country = forms.ModelChoiceField(
        queryset=models.Country.objects.all().order_by('name'),
        required=False, label=_(u'Country'))
    post_office_box = StrippedCharField(max_length=100, required=False,
                                        label=_(u'Post office box'))


    class Meta:
        model = models.Address


class Communication(ModelForm):

    class Meta:
        model = models.Communication


class LoginForm(InhouseMixin, BaseAuthenticationForm):
    """Form used to login a user."""


class UserProfileAddressForm(Address):
    """Minimal address form used in the user profile."""

    class Meta:
        exclude = ('group', 'post_office_box', 'box_zip_code')
        model = models.Address


class UserProfileForm(ModelForm):

    #username = forms.CharField(label=_(u'Username'),
    #                           widget=ReadonlyWidget(),
    #                           required=False)
    first_name = StrippedCharField(label=_(u'First name'), max_length=30)
    last_name = StrippedCharField(label=_(u'Last name'), max_length=30)
    email = forms.EmailField(label=_(u'Email address'))
    birthday = DatePickerField(required=False, label=_(u'Birthday'))
    #status = forms.BooleanField(label=_(u'Active'), required=False)
    language = forms.ChoiceField(choices=models.LANGUAGE_CHOICES,
                                     label=_(u'Language'))

    class Meta:
        model = models.UserProfile
        fields = ('first_name', 'last_name', 'email', 'birthday', 'language',)

    @classmethod
    def get_initial_data(cls, user):
        """Returns initial data for this form."""
        return {'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'status': user.is_active,
                'email': user.email}
