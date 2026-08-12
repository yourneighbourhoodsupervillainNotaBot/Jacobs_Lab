"""Compatibility alias: test_harness -> jacobs_lab.testing.test_harness."""

from .testing import test_harness as _impl  # noqa: F401
import sys as _sys

_sys.modules[__name__] = _impl
