"""Deprecated alias: Nested_mapper -> nested_mapper."""

from . import nested_mapper as _impl  # noqa: F401
import sys as _sys

_sys.modules[__name__] = _impl
