"""Compatibility alias: test_sonify -> jacobs_lab.audio.test_sonify."""

from .audio import test_sonify as _impl  # noqa: F401
import sys as _sys

_sys.modules[__name__] = _impl
