"""Compatibility alias: lab_adapters_extended -> jacobs_lab.trace.lab_adapters_extended."""

from .testing.trace import lab_adapters_extended as _impl  # noqa: F401
import sys as _sys

_sys.modules[__name__] = _impl
