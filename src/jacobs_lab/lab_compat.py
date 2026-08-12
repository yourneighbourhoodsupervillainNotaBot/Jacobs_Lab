from __future__ import annotations

import importlib


def import_folding():
    """Import the folding VM module from the installed package."""
    try:
        return importlib.import_module("jacobs_lab.folding_computation")
    except ModuleNotFoundError:
        return importlib.import_module("jacobs_lab.folding_computations")


def apply_pyglet_label_guard():
    """
    Guard against the pyglet destructor bug:

        AttributeError: 'Label' object has no attribute '_boxes'

    This can happen when Labels are destroyed repeatedly in an inspector UI.
    """
    try:
        from pyglet.text import DocumentLabel

        if getattr(DocumentLabel, "_lab_del_guarded", False):
            return

        original_del = DocumentLabel.__del__

        def _safe_document_label_del(self):
            try:
                if hasattr(self, "_boxes"):
                    original_del(self)
            except Exception:
                pass

        DocumentLabel.__del__ = _safe_document_label_del
        DocumentLabel._lab_del_guarded = True

    except Exception:
        pass
