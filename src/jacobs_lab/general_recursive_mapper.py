"""Compatibility alias: general_recursive_mapper -> jacobs_lab.core.general_recursive_mapper."""

from .core import general_recursive_mapper as _impl  # noqa: F401
import sys as _sys

_sys.modules[__name__] = _impl
