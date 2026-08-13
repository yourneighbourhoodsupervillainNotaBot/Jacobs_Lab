"""Compatibility alias: lab_export -> jacobs_lab.trace.lab_export."""

from .testing.trace import lab_export as _impl  # noqa: F401
import sys as _sys

_sys.modules[__name__] = _impl
