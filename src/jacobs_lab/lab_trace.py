"""Compatibility alias: lab_trace -> jacobs_lab.trace.lab_trace."""

from .trace import lab_trace as _impl  # noqa: F401
import sys as _sys

_sys.modules[__name__] = _impl
