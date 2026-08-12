"""Compatibility alias: test_tree_preview -> jacobs_lab.viz.test_tree_preview."""

from .viz import test_tree_preview as _impl  # noqa: F401
import sys as _sys

_sys.modules[__name__] = _impl
