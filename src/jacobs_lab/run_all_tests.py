"""Compatibility alias: run_all_tests -> jacobs_lab.testing.run_all_tests."""

from .testing import run_all_tests as _impl  # noqa: F401
import sys as _sys

_sys.modules[__name__] = _impl
