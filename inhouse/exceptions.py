# -*- coding: utf-8 -*-

"""Inhouse exception classes."""


class InhouseError(StandardError):
    """Base error class."""
    pass


class InhouseModelError(InhouseError):
    """Class for model errors."""
    pass
