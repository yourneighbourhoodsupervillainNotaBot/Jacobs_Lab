from __future__ import annotations

import pathlib
import re
import shutil

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
PKG = SRC / "jacobs_lab"

EXCLUDE_FILES = {
    "setup.py",
}

ALIASES = {
    "folding_computation": "folding_computations",
}


def known_modules():
    names = set()

    for p in ROOT.glob("*.py"):
        if p.name in EXCLUDE_FILES:
            continue

        if p.stem == "__init__":
            continue

        names.add(p.stem)

    for old, new in ALIASES.items():
        names.add(new)

    return sorted(names)


def rewrite_line(line: str, known) -> str:
    if line.lstrip().startswith(
        ("from .", "import .", "from jacobs_lab", "import jacobs_lab")
    ):
        return line

    indent = line[: len(line) - len(line.lstrip())]
    stripped = line.lstrip()

    for mod in known:
        target = ALIASES.get(mod, mod)

        # from module import ...
        m = re.match(rf"^from\s+{re.escape(mod)}\s+import\s+(.*)$", stripped)
        if m:
            return f"{indent}from .{target} import {m.group(1).strip()}\n"

        # import module as alias
        m = re.match(rf"^import\s+{re.escape(mod)}\s+as\s+(\w+)\s*$", stripped)
        if m:
            return f"{indent}from . import {target} as {m.group(1)}\n"

        # import module
        m = re.match(rf"^import\s+{re.escape(mod)}\s*$", stripped)
        if m:
            if target != mod:
                return f"{indent}from . import {target} as {mod}\n"
            return f"{indent}from . import {mod}\n"

    out = line

    # Rewrite string-based dynamic imports:
    #   importlib.import_module("module")
    # becomes:
    #   importlib.import_module("jacobs_lab.module")
    for mod in known:
        target = ALIASES.get(mod, mod)
        out = re.sub(
            rf"import_module\((['\"]){re.escape(mod)}\1\)",
            rf"import_module(\1jacobs_lab.{target}\1)",
            out,
        )

    return out


def rewrite_file(path: pathlib.Path, known):
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    new_lines = [rewrite_line(line, known) for line in lines]
    text = "".join(new_lines)

    # Variable-based dynamic imports used by test harness / runners.
    text = text.replace(
        "importlib.import_module(name)",
        'importlib.import_module(f"jacobs_lab.{name}")',
    )

    text = text.replace(
        'importlib.import_module("folding_computations")',
        'importlib.import_module("jacobs_lab.folding_computations")',
    )

    text = text.replace(
        'importlib.import_module("folding_computation")',
        'importlib.import_module("jacobs_lab.folding_computation")',
    )

    # Known small cleanups.
    if path.name == "natural_transformations.py":
        text = re.sub(r"\brun_self_tests\s*\(\)", "_run_self_tests()", text)

    if path.name == "sonify.py":
        text = text.replace(
            'write_wav("/home/claude/triangle_walk.wav", audio)',
            'write_wav("triangle_walk.wav", audio)',
        )

    path.write_text(text, encoding="utf-8")


def clean_package_dir():
    if PKG.exists():
        backup = ROOT / "backup_jacobs_lab"

        if backup.exists():
            shutil.rmtree(backup)

        shutil.move(str(PKG), str(backup))
        print(f"Backed up old package directory to: {backup}")


def copy_root_modules():
    PKG.mkdir(parents=True, exist_ok=True)

    for p in sorted(ROOT.glob("*.py")):
        if p.name in EXCLUDE_FILES:
            continue

        if p.stem == "__init__":
            continue

        shutil.copy2(p, PKG / p.name)


def canonicalize_folding():
    old = PKG / "folding_computation.py"
    new = PKG / "folding_computations.py"

    # If the local spelling is folding_computation.py, copy it to the
    # canonical folding_computations.py.
    if old.exists() and not new.exists():
        shutil.copy2(old, new)

    # If only the canonical file exists, create a small compatibility alias.
    if new.exists() and not old.exists():
        old.write_text(
            "from .folding_computations import *  # noqa: F401,F403\n",
            encoding="utf-8",
        )


INIT = '''"""Jacobs Lab package."""

__version__ = "0.2.0"
'''


MAIN = """import sys

from .lab_cli import main


def main_entry():
    return main()


if __name__ == "__main__":
    sys.exit(main_entry())
"""


LAB_COMPAT = '''from __future__ import annotations

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
'''


def write_package_core():
    (PKG / "__init__.py").write_text(INIT, encoding="utf-8")
    (PKG / "__main__.py").write_text(MAIN, encoding="utf-8")
    (PKG / "lab_compat.py").write_text(LAB_COMPAT, encoding="utf-8")


def main():
    known = known_modules()

    clean_package_dir()
    copy_root_modules()
    canonicalize_folding()

    for py in sorted(PKG.glob("*.py")):
        if py.name in ("__init__.py", "__main__.py", "lab_compat.py"):
            continue

        rewrite_file(py, known)

    write_package_core()

    print(f"Refined package written to: {PKG}")
    print()
    print("Next steps:")
    print("  python -m pip install -e .")
    print("  jacobs-lab test")
    print("  python -m jacobs_lab test")


if __name__ == "__main__":
    main()
