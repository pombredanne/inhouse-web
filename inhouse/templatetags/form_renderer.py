# -*- coding: utf-8 -*-

"""Form renderer filter."""

from django import template
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from inhouse.forms import BoundField

register = template.Library()  # pylint: disable=C0103


class RequiredFieldsNode(template.Node):
    """Node that actually renders a required fields text."""

    def __init__(self, forms):
        super(RequiredFieldsNode, self).__init__()
        self.forms = forms

    def render(self, context):
        for forms in self.forms:
            formsobj = forms.resolve(context, True)
            if not isinstance(formsobj, (list, tuple)):
                formsobj = [formsobj]
            for form in formsobj:
                if form.has_required_fields():
                    return unicode(_(u'* Required fields'))
        return u''


@register.tag(name='reqfields')
def render_form_required(parser, token):  # pylint: disable=W0613
    """Renders a given list."""
    contents = token.split_contents()
    forms = []
    for expr in contents[1:]:
        forms.append(parser.compile_filter(expr))
    return RequiredFieldsNode(forms)


class FormErrorsNode(template.Node):
    """Node that renders errors to one ore more forms."""

    def __init__(self, forms):
        super(FormErrorsNode, self).__init__()
        self.forms = forms

    def render(self, context):
        errors = []
        general_errors = []
        for forms in self.forms:
            formsobj = forms.resolve(context, True)
            if not isinstance(formsobj, (list, tuple)):
                formsobj = [formsobj]
            for form in formsobj:
                if form.errors:
                    for key, error in form.errors.items():
                        if key in form.fields.keys():
                            field = form.fields.get(key)
                            bf = BoundField(form, field, key)
                            label = bf.label or None
                            errors.append((_(label), ', '.join(error)))
                        else:
                            general_errors.append(', '.join(error))
        return render_to_string('inhouse/snippets/form_errors.html',
                                {'errors': errors,
                                 'general_errors': general_errors})


@register.tag(name='form_errors')
def render_form_errors(parser, token):  # pylint: disable=W0613
    """Renders errors to one or more forms."""
    contents = token.split_contents()
    forms = []
    for expr in contents[1:]:
        forms.append(parser.compile_filter(expr))
    return FormErrorsNode(forms)
