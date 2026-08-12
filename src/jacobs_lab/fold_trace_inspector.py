"""Compatibility alias: fold_trace_inspector -> jacobs_lab.viz.fold_trace_inspector."""

from .viz import fold_trace_inspector as _impl  # noqa: F401
import sys as _sys

_sys.modules[__name__] = _impl
