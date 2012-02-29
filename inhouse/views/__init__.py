# -*- coding: utf-8 -*-

"""View functions."""

import time

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import login as django_login
from django.utils.translation import ugettext_lazy as _

from inhouse import forms, models
from inhouse.exceptions import InhouseModelError
from inhouse.views.utils import render


@login_required
def index(request):
    """The user's dashboard."""
    return render(request, 'inhouse/dashboard.html')


def login(request, *args, **kwargs):
    attempts_key = 'login_attempts'
    attempts = request.session.get(attempts_key, (0, None))
    if request.method == 'POST':
        attempts = (attempts[0]+1, time.time())
        request.session[attempts_key] = attempts
    kwargs['authentication_form'] = forms.LoginForm
    response = django_login(request, *args, **kwargs)
    if response.status_code == 302:
        try:
            del request.session[attempts_key]
        except KeyError:
            pass
    return response

@login_required
def profile_details(request):
    messages.success(request, _(u'This is a success'))
    messages.warning(request, _(u'This is a warning'))
    messages.error(request, _(u'This is an error'))
    try:
        profile = models.UserProfile.new(user=request.user)
    except InhouseModelError:
        profile = request.user.get_profile()
    address = profile.address
    commdata = profile.communication
    address_form = forms.UserProfileAddressForm(instance=address)
    commdata_form = forms.Communication(instance=commdata)
    user_form = forms.UserProfileForm(instance=profile)
    return render(request, 'inhouse/profile.html', {
        'profile_form_address': address_form,
        'profile_form_commdata': commdata_form,
        'profile_form_user': user_form,
    })
