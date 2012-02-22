# -*- coding: utf-8 -*-

import logging
import traceback

from django.conf import settings
from django.db.models import loading
from django.db.models.signals import pre_save
from django.http import HttpResponse, Http404

from inhouse import models

log = logging.getLogger('django')


class AjaxDebugMiddleware(object):

    def process_exception(self, request, exception):
        if (settings.DEBUG and request.is_ajax()
            and not isinstance(exception, Http404)):
            log.exception('Exception during AJAX request:')
            return HttpResponse(traceback.format_exc(exception),
                                mimetype='text/plain', status=500)


class AutoCurrentUserMiddleware(object):
    """Updates created_by, modified_by attributes.

    The attributes created_by and modified_by are only updated for
    models in dlgicert application.

    This middleware class must come after AuthenticationMiddleware.
    """

    def __init__(self):
        # cache relevant models
        self._app_models = loading.get_models(models)
        super(AutoCurrentUserMiddleware, self).__init__()

    def process_request(self, request):
        """Attaches a local callback function listening to pre_save signal."""
        # we intentionally set protected members, pylint:disable=W0212
        if request.user.is_authenticated():
            user_id = request.user.id
        else:
            user_id = None

        def pre_save_cb(*args, **kwds):
            sender = kwds['sender']
            instance = kwds['instance']
            if sender in self._app_models:
                if hasattr(instance, 'created_by') and not instance.created_by:
                    instance.created_by = user_id
                if hasattr(instance, 'modified_by'):
                    instance.modified_by = user_id
        # store dispatch_uid as request attribute
        request._auto_current_user_uid = id(pre_save_cb)
        # connect callback to pre_save signal
        pre_save.connect(pre_save_cb, weak=False,
                         dispatch_uid=request._auto_current_user_uid)

    def _disconnect_callback(self, request):
        """Actually removes callback attached in process_request."""
        dispatch_uid = getattr(request, '_auto_current_user_uid', None)
        if dispatch_uid is not None:
            pre_save.disconnect(dispatch_uid=dispatch_uid)

    def process_response(self, request, response):
        """Removes callback attached in process_request."""
        self._disconnect_callback(request)
        return response

    def process_exception(self, request, exception):
        """Removes callback attached in process_request."""
        # exception unused, pylint: disable=W0613
        self._disconnect_callback(request)



class UserLanguageMiddleware(object):
    """Loads the profile for a logged in user and sets preferred language.

    This middleware class must come after AuthenticationMiddleware and
    before LocaleMiddleware.
    """

    def process_request(self, request):
        """Load user profile and activate settings."""
        if not request.user.is_authenticated():
            return
        try:
            user_profile = request.user.get_profile()
        except models.UserProfile.DoesNotExist:
            return
        lkey = 'django_language'
        if user_profile.language in [x[0] for x in settings.LANGUAGES]:
            request.session[lkey] = str(user_profile.language)
        else:
            try:
                del request.session[lkey] # let Django do the rest
            except KeyError:
                pass
