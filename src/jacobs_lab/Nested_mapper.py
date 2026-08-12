"""Compatibility alias: Nested_mapper -> jacobs_lab.core.nested_mapper."""

from .core import nested_mapper as _impl  # noqa: F401
import sys as _sys

_sys.modules[__name__] = _impl
