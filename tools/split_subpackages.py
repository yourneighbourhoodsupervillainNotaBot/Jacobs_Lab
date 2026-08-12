from __future__ import annotations

import pathlib
import re
import shutil

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
PKG = SRC / "jacobs_lab"
BACKUP = ROOT / "backup_jacobs_lab_presplit"

PACKAGE_NAME = "jacobs_lab"

ALIASES = {
    "folding_computation": "folding_computations",
}

ROOT_KEEP = {
    "__init__",
    "__main__",
    "lab_compat",
}

SUBPACKAGE_MAP = {
    # core
    "general_recursive_mapper": "core",
    "named_aliases": "core",
    "recursive_lattice": "core",
    "Nested_mapper": "core",
    # structure
    "triangle_state_machine": "structure",
    "folding_graph": "structure",
    "flexagon": "structure",
    "Level_tree": "structure",
    # math lenses
    "galois_fields": "math_lenses",
    "set_theory": "math_lenses",
    "category_theory": "math_lenses",
    "natural_transformations": "math_lenses",
    "quintic_analysis": "math_lenses",
    # computation
    "folding_computation": "computation",
    "folding_computations": "computation",
    "turing_universality": "computation",
    "universality_probe": "computation",
    "complexity_lab": "computation",
    # instruments
    "fold_codec": "instruments",
    "fold_complexity": "instruments",
    "prime_machinery": "instruments",
    "pathfinding_lab": "instruments",
    "three_body_lab": "instruments",
    # audio
    "sonify": "audio",
    "test_sonify": "audio",
    "lab_sonify_trace": "audio",
    # viz
    "test_tree_preview": "viz",
    "pyglet_visualizer": "viz",
    "node_inspector": "viz",
    "fold_trace_inspector": "viz",
    "lab_inspector": "viz",
    # trace
    "lab_trace": "trace",
    "lab_adapters": "trace",
    "lab_adapters_extended": "trace",
    "lab_export": "trace",
    # testing
    "test_harness": "testing",
    "test_walk_engine": "testing",
    "run_all_tests": "testing",
    # cli
    "lab_cli": "cli",
    # root compatibility / cross-cutting
    "lab_compat": "",
}

EXPECTED_SUBPACKAGES = [
    "core",
    "structure",
    "math_lenses",
    "computation",
    "instruments",
    "audio",
    "viz",
    "trace",
    "testing",
    "cli",
    "misc",
]

KNOWN_MODULES = set(SUBPACKAGE_MAP.keys())
KNOWN_SORTED = []


def canonical(mod: str) -> str:
    return ALIASES.get(mod, mod)


def subpackage_for(mod: str) -> str | None:
    if mod in SUBPACKAGE_MAP:
        return SUBPACKAGE_MAP[mod]

    # Heuristics for modules not explicitly mapped.
    if mod.startswith("lab_adapters") or mod in {"lab_trace", "lab_export"}:
        return "trace"

    if mod.startswith("lab_sonify"):
        return "audio"

    if mod in {"sonify", "test_sonify"}:
        return "audio"

    if (
        mod.startswith("lab_inspector")
        or "visualizer" in mod
        or "preview" in mod
        or "inspector" in mod
    ):
        return "viz"

    if mod.startswith("test_") or mod == "run_all_tests":
        return "testing"

    if mod == "lab_cli":
        return "cli"

    if mod == "lab_compat":
        return ""

    # Default: keep unknown modules inside the package, but isolated.
    return "misc"


def target_path(mod: str):
    sub = subpackage_for(mod)

    if sub is None:
        return None, None

    canon = canonical(mod)

    if sub == "":
        return f"{PACKAGE_NAME}.{canon}", canon

    return f"{PACKAGE_NAME}.{sub}.{canon}", canon


def rewrite_line(line: str) -> str:
    if line.lstrip().startswith("#"):
        return line

    indent = line[: len(line) - len(line.lstrip())]
    stripped = line.lstrip()

    for mod in KNOWN_SORTED:
        tp, canon = target_path(mod)

        if not tp:
            continue

        parent = tp.rsplit(".", 1)[0]

        # Already rewritten to the new target.
        if tp in stripped:
            continue

        # from module import ...
        # from .module import ...
        # from jacobs_lab.module import ...
        m = re.match(
            rf"^from\s+(?:\.|{PACKAGE_NAME}\.)?{re.escape(mod)}\s+import\s+(.*)$",
            stripped,
        )
        if m:
            return f"{indent}from {tp} import {m.group(1).strip()}\n"

        # import module as alias
        m = re.match(
            rf"^import\s+(?:\.|{PACKAGE_NAME}\.)?{re.escape(mod)}\s+as\s+(\w+)\s*$",
            stripped,
        )
        if m:
            return f"{indent}from {parent} import {canon} as {m.group(1)}\n"

        # import module
        m = re.match(
            rf"^import\s+(?:\.|{PACKAGE_NAME}\.)?{re.escape(mod)}\s*$",
            stripped,
        )
        if m:
            if canon != mod:
                return f"{indent}from {parent} import {canon} as {mod}\n"
            return f"{indent}from {parent} import {canon}\n"

        # from . import module as alias
        m = re.match(
            rf"^from\s+(?:\.|{PACKAGE_NAME})\s+import\s+{re.escape(mod)}\s+as\s+(\w+)\s*$",
            stripped,
        )
        if m:
            return f"{indent}from {parent} import {canon} as {m.group(1)}\n"

        # from . import module
        m = re.match(
            rf"^from\s+(?:\.|{PACKAGE_NAME})\s+import\s+{re.escape(mod)}\s*$",
            stripped,
        )
        if m:
            if canon != mod:
                return f"{indent}from {parent} import {canon} as {mod}\n"
            return f"{indent}from {parent} import {canon}\n"

    out = line

    # Rewrite string-based dynamic imports.
    for mod in KNOWN_SORTED:
        tp, _ = target_path(mod)

        if not tp:
            continue

        out = re.sub(
            rf"import_module\((['\"]){re.escape(mod)}\1\)",
            rf"import_module(\1{tp}\1)",
            out,
        )

        out = re.sub(
            rf"import_module\((['\"]){PACKAGE_NAME}\.{re.escape(mod)}\1\)",
            rf"import_module(\1{tp}\1)",
            out,
        )

    # Common variable-based dynamic import pattern.
    out = out.replace(
        "importlib.import_module(name)",
        'importlib.import_module(f"jacobs_lab.{name}")',
    )

    return out


def rewrite_file(path: pathlib.Path):
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    new_lines = [rewrite_line(line) for line in lines]
    text = "".join(new_lines)

    # Known small cleanups.
    if path.name == "natural_transformations.py":
        text = re.sub(r"\brun_self_tests\s*\(\)", "_run_self_tests()", text)

    if path.name == "sonify.py":
        text = text.replace(
            'write_wav("/home/claude/triangle_walk.wav", audio)',
            'write_wav("triangle_walk.wav", audio)',
        )

    path.write_text(text, encoding="utf-8")


def check_package_exists():
    if not PKG.exists():
        raise SystemExit(
            f"Missing package directory: {PKG}\n" "Run tools/refine_package.py first."
        )


def check_not_already_split():
    for child in PKG.iterdir():
        if child.name == "__pycache__":
            continue

        if child.is_dir() and (child / "__init__.py").exists():
            raise SystemExit(
                f"{PKG} already appears to be split into subpackages.\n"
                "Restore from backup or remove the existing subpackage layout first."
            )


def backup_package():
    if BACKUP.exists():
        shutil.rmtree(BACKUP)

    shutil.copytree(PKG, BACKUP)
    print(f"Backed up existing package to: {BACKUP}")


def canonicalize_folding():
    old = PKG / "folding_computation.py"
    new = PKG / "folding_computations.py"

    if old.exists() and not new.exists():
        shutil.move(str(old), str(new))
        print("Renamed folding_computation.py -> folding_computations.py")

    elif old.exists() and new.exists():
        old.unlink()
        print("Removed duplicate folding_computation.py alias source file")


def collect_known_modules():
    global KNOWN_MODULES, KNOWN_SORTED

    for p in PKG.glob("*.py"):
        if p.stem in ("__init__", "__main__"):
            continue

        KNOWN_MODULES.add(p.stem)

    KNOWN_SORTED = sorted(KNOWN_MODULES, key=len, reverse=True)


def create_subpackage_dirs():
    for sub in EXPECTED_SUBPACKAGES:
        d = PKG / sub
        d.mkdir(parents=True, exist_ok=True)

        init = d / "__init__.py"
        if not init.exists():
            init.write_text(
                f'"""{PACKAGE_NAME}.{sub} subpackage."""\n',
                encoding="utf-8",
            )


def move_modules():
    moved = []

    for p in list(PKG.glob("*.py")):
        stem = p.stem

        if stem in ROOT_KEEP:
            continue

        sub = subpackage_for(stem)

        if sub is None or sub == "":
            continue

        dest_dir = PKG / sub
        dest_dir.mkdir(parents=True, exist_ok=True)

        dest = dest_dir / f"{canonical(stem)}.py"

        # If both folding spellings exist, keep only the canonical file.
        if (
            p.name == "folding_computation.py"
            and (PKG / "folding_computations.py").exists()
        ):
            p.unlink()
            continue

        shutil.move(str(p), str(dest))
        moved.append((stem, sub, canonical(stem)))

    return moved


def rewrite_all_files():
    for py in PKG.rglob("*.py"):
        if "__pycache__" in py.parts:
            continue

        rewrite_file(py)


def write_root_init():
    init = PKG / "__init__.py"
    init.write_text(
        '"""Jacobs Lab package (subpackage split refinement)."""\n\n'
        '__version__ = "0.3.0"\n',
        encoding="utf-8",
    )


def write_main():
    main = PKG / "__main__.py"
    main.write_text(
        """import sys

from .cli.lab_cli import main


def main_entry():
    return main()


if __name__ == "__main__":
    sys.exit(main_entry())
""",
        encoding="utf-8",
    )


def write_lab_compat():
    compat = PKG / "lab_compat.py"

    compat.write_text(
        '''from __future__ import annotations

import importlib


def import_folding():
    """Import the folding VM module from the split package."""
    try:
        return importlib.import_module("jacobs_lab.computation.folding_computation")
    except ModuleNotFoundError:
        return importlib.import_module("jacobs_lab.computation.folding_computations")


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
''',
        encoding="utf-8",
    )


def write_computation_folding_alias():
    comp = PKG / "computation"

    if not comp.exists():
        return

    alias = comp / "folding_computation.py"
    target = comp / "folding_computations.py"

    if target.exists() and not alias.exists():
        alias.write_text(
            '''"""Compatibility alias: folding_computation -> folding_computations."""

from . import folding_computations as _impl  # noqa: F401
import sys as _sys

_sys.modules[__name__] = _impl
''',
            encoding="utf-8",
        )


def write_root_aliases(moved):
    aliases_written = 0

    # Aliases for modules that were moved.
    for old, sub, canon in moved:
        if sub == "":
            continue

        alias_path = PKG / f"{old}.py"

        alias_path.write_text(
            f'''"""Compatibility alias: {old} -> {PACKAGE_NAME}.{sub}.{canon}."""

from .{sub} import {canon} as _impl  # noqa: F401
import sys as _sys

_sys.modules[__name__] = _impl
''',
            encoding="utf-8",
        )

        aliases_written += 1

    # Ensure old folding spelling aliases to canonical folding module.
    for old, new in ALIASES.items():
        sub = subpackage_for(new)

        if not sub:
            continue

        alias_path = PKG / f"{old}.py"

        if not alias_path.exists():
            alias_path.write_text(
                f'''"""Compatibility alias: {old} -> {PACKAGE_NAME}.{sub}.{new}."""

from .{sub} import {new} as _impl  # noqa: F401
import sys as _sys

_sys.modules[__name__] = _impl
''',
                encoding="utf-8",
            )

            aliases_written += 1

    return aliases_written


def main():
    check_package_exists()
    check_not_already_split()

    backup_package()

    collect_known_modules()
    canonicalize_folding()

    create_subpackage_dirs()

    moved = move_modules()

    rewrite_all_files()

    write_root_init()
    write_main()
    write_lab_compat()
    write_computation_folding_alias()

    aliases = write_root_aliases(moved)

    print()
    print(f"Split complete: {PKG}")
    print(f"Moved modules: {len(moved)}")
    print(f"Wrote compatibility aliases: {aliases}")
    print()
    print("Next steps:")
    print("  python -m pip install -e .")
    print("  python -m jacobs_lab test")
    print()
    print("Old import paths still work through root compatibility aliases.")


if __name__ == "__main__":
    main()
