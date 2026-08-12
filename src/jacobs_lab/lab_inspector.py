"""Compatibility alias: lab_inspector -> jacobs_lab.viz.lab_inspector."""

from .viz import lab_inspector as _impl  # noqa: F401
import sys as _sys

_sys.modules[__name__] = _impl
