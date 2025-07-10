# -*- coding: utf-8 -*-
"""Shim module to maintain backward-compatibility for modules that do
``import utils`` from the project root.  It simply re-exports everything
from ``app.utils`` so that call-sites outside the *app* package continue to
work even after we turned *app* into a proper Python package with relative
imports.

This file should come **before** any other code attempts to import the
``utils`` package to avoid ``ModuleNotFoundError``.
"""

from importlib import import_module as _imp

_app_utils = _imp("app.utils")

# Re-export public names
__all__ = getattr(_app_utils, "__all__", dir(_app_utils))

for _name in __all__:
    globals()[_name] = getattr(_app_utils, _name)

# Clean-up namespace
del _imp, _app_utils, _name
