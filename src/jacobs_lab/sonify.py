"""Compatibility alias: sonify -> jacobs_lab.audio.sonify."""

from .audio import sonify as _impl  # noqa: F401
import sys as _sys

_sys.modules[__name__] = _impl
