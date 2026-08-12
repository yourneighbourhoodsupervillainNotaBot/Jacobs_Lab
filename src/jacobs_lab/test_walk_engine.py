"""Compatibility alias: test_walk_engine -> jacobs_lab.testing.test_walk_engine."""

from .testing import test_walk_engine as _impl  # noqa: F401
import sys as _sys

_sys.modules[__name__] = _impl
