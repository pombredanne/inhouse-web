# -*- coding: utf-8 -*-

"""Utility and helper functions for views."""

from django.shortcuts import render_to_response
from django.template import RequestContext


def render(request, template_name, data=None):
    """Helper that renders and returns a response.

    :param request: The request object.
    :param template_name: A template name.
    :param data: Dictonary with data to be rendered (optional).

    :returns: Response object.
    """
    return render_to_response(template_name,
                              context_instance=RequestContext(request, data))


def store_dict_in_session(request, storagename, dct, exclude=None):
    """Stores a dictionary or QueryDict in a request session under a given name.

    :param request: Request with required session
    :param storagename: Name of the dict for later retrieval
    :param dct: Data dictionary to store
    :param exclude: List of keys to exclude from storage
    """
    if exclude is None:
        exclude = []
    to_store = dct.copy()
    for key in set(to_store):
        if key in exclude:
            del to_store[key]
    request.session[storagename] = to_store


def get_dict_from_session(request, storagename, default=None):
    """Retrieves a stored dict from a session.

    :param request: Request with required session
    :param storagename: Name of stored dict
    :returns: stored or empty dictionary
    """
    return request.session.get(storagename, {}) or default or {}


def response_json(request, obj, redirect=None):
    """Return a JSON response with obj as payload.

    If redirect is not ``None`` the response contains a Location
    header with the value of redirect. The JavaScript is then able to
    perform a page refresh on its own.

    If the request contains a 'X-PU-Managed' header the returned
    object is wrapped in a dictionary with the following keys and
    values:
      - payload: the original object
      - messages: list of messages (2-tuples of message type, message)
    """
    # Unfortunately the XHR standard states that 302 FOUND
    # must be handled transparently. So the frontend code
    # doesn't even see the redirect. Therefore we're sending a
    # 200 with an additional Location header.
    # http://www.w3.org/TR/XMLHttpRequest/#infrastructure-for-the
    # send-method
    if 'HTTP_X_PU_MANAGED' in request.META:
        obj = {'payload': obj,
               'messages': []}
        if redirect is None:  # flush messages
            obj['messages'] = [(msg.tags, unicode(msg.message))
                               for msg in messages.get_messages(request)]
    response = HttpResponse(json.dumps(obj), content_type='application/json')
    if redirect is not None:
        response['Location'] = redirect
    return response


def get_ttlist(query, func=unicode):
    """Returns a list with two-tuples from a query

    :param query: Query to convert
    :param func: Callable that accepts object as parameter
    """
    return [(el.id, func(el)) for el in query.all()]
