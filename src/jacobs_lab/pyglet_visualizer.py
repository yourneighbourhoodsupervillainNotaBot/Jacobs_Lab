"""Compatibility alias: pyglet_visualizer -> jacobs_lab.viz.pyglet_visualizer."""

from .viz import pyglet_visualizer as _impl  # noqa: F401
import sys as _sys

_sys.modules[__name__] = _impl
