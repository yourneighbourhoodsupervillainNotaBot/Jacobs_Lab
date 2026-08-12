"""Compatibility alias: lab_sonify_trace -> jacobs_lab.audio.lab_sonify_trace."""

from .audio import lab_sonify_trace as _impl  # noqa: F401
import sys as _sys

_sys.modules[__name__] = _impl
