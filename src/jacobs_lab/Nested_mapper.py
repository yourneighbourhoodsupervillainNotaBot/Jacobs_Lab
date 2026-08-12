"""Compatibility alias: Nested_mapper -> jacobs_lab.core.Nested_mapper."""

from .core import Nested_mapper as _impl  # noqa: F401
import sys as _sys

_sys.modules[__name__] = _impl
