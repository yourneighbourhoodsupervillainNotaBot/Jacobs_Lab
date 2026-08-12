from __future__ import annotations

import argparse
import pathlib
import shutil

ROOT = pathlib.Path(__file__).resolve().parents[1]
PKG = ROOT / "src" / "jacobs_lab"
BACKUP = ROOT / "backup_jacobs_lab_precanonical"

PACKAGE_NAME = "jacobs_lab"

KEEP_ROOT_FILES = {
    "__init__.py",
    "__main__.py",
    "lab_compat.py",
}

TEXT_REPLACEMENTS = [
    # Canonicalize old non-PEP8 module names.
    ("jacobs_lab.core.Nested_mapper", "jacobs_lab.core.nested_mapper"),
    ("jacobs_lab.structure.Level_tree", "jacobs_lab.structure.level_tree"),
    ("from .Nested_mapper", "from .nested_mapper"),
    ("from .Level_tree", "from .level_tree"),
    ("Nested_mapper", "nested_mapper"),
    ("Level_tree", "level_tree"),
]


TEST_HARNESS = '''from __future__ import annotations

import importlib
import time
from dataclasses import dataclass
from typing import List, Optional


MODULE_NAMES = [
    "jacobs_lab.core.general_recursive_mapper",
    "jacobs_lab.core.named_aliases",
    "jacobs_lab.core.recursive_lattice",
    "jacobs_lab.core.nested_mapper",

    "jacobs_lab.structure.triangle_state_machine",
    "jacobs_lab.structure.folding_graph",
    "jacobs_lab.structure.flexagon",
    "jacobs_lab.structure.level_tree",

    "jacobs_lab.math_lenses.galois_fields",
    "jacobs_lab.math_lenses.set_theory",
    "jacobs_lab.math_lenses.category_theory",
    "jacobs_lab.math_lenses.natural_transformations",
    "jacobs_lab.math_lenses.quintic_analysis",

    "jacobs_lab.computation.folding_computations",
    "jacobs_lab.computation.turing_universality",
    "jacobs_lab.computation.universality_probe",
    "jacobs_lab.computation.complexity_lab",

    "jacobs_lab.instruments.fold_codec",
    "jacobs_lab.instruments.fold_complexity",
    "jacobs_lab.instruments.prime_machinery",
    "jacobs_lab.instruments.pathfinding_lab",
    "jacobs_lab.instruments.three_body_lab",
]


ALIASES = {
    "folding_computation": "jacobs_lab.computation.folding_computations",
    "Nested_mapper": "jacobs_lab.core.nested_mapper",
    "Level_tree": "jacobs_lab.structure.level_tree",
}


@dataclass
class TestResult:
    module: str
    passed: bool
    duration: float
    error: Optional[str] = None


def _import(name: str):
    try:
        return importlib.import_module(name)
    except ModuleNotFoundError:
        target = ALIASES.get(name)
        if target:
            return importlib.import_module(target)
        raise


def run_all_tests(module_names: List[str] = None) -> List[TestResult]:
    """Import each module and run its _run_self_tests()."""
    names = MODULE_NAMES if module_names is None else module_names
    results: List[TestResult] = []

    for name in names:
        start = time.perf_counter()

        try:
            mod = _import(name)
            fn = getattr(mod, "_run_self_tests", None)

            if fn is None:
                results.append(
                    TestResult(
                        name,
                        False,
                        0.0,
                        "no _run_self_tests() found",
                    )
                )
                continue

            fn()
            duration = time.perf_counter() - start
            results.append(TestResult(name, True, duration))

        except Exception as e:
            duration = time.perf_counter() - start
            results.append(
                TestResult(
                    name,
                    False,
                    duration,
                    f"{type(e).__name__}: {e}",
                )
            )

    return results


def _run_self_tests():
    import sys
    import types

    ok_mod = types.ModuleType("ok_mod")
    ok_mod._run_self_tests = lambda: None

    fail_mod = types.ModuleType("fail_mod")

    def _boom():
        raise AssertionError("synthetic failure for testing")

    fail_mod._run_self_tests = _boom

    sys.modules["ok_mod"] = ok_mod
    sys.modules["fail_mod"] = fail_mod

    results = run_all_tests(["ok_mod", "fail_mod"])

    assert len(results) == 2
    assert results[0].passed and results[0].error is None
    assert not results[1].passed and "synthetic failure" in results[1].error

    print("All test-harness self-tests passed.")
'''


RUN_ALL_TESTS = '''"""Unified test runner for the folding laboratory.

Canonical subpackage version.

Usage:
    python -m jacobs_lab.testing.run_all_tests
    python -m jacobs_lab.testing.run_all_tests --fast
"""

from __future__ import annotations

import argparse
import importlib
import sys
import time
import traceback


CORE = [
    "jacobs_lab.core.general_recursive_mapper",
    "jacobs_lab.core.named_aliases",
    "jacobs_lab.core.recursive_lattice",
    "jacobs_lab.core.nested_mapper",
]

STRUCTURE = [
    "jacobs_lab.structure.triangle_state_machine",
    "jacobs_lab.structure.folding_graph",
    "jacobs_lab.structure.flexagon",
    "jacobs_lab.structure.level_tree",
]

LENSES = [
    "jacobs_lab.math_lenses.galois_fields",
    "jacobs_lab.math_lenses.set_theory",
    "jacobs_lab.math_lenses.category_theory",
    "jacobs_lab.math_lenses.natural_transformations",
    "jacobs_lab.math_lenses.quintic_analysis",
]

COMPUTATION = [
    "jacobs_lab.computation.folding_computations",
    "jacobs_lab.computation.turing_universality",
    "jacobs_lab.computation.universality_probe",
]

INSTRUMENTS = [
    "jacobs_lab.instruments.fold_codec",
    "jacobs_lab.instruments.fold_complexity",
    "jacobs_lab.instruments.prime_machinery",
    "jacobs_lab.instruments.complexity_lab",
    "jacobs_lab.instruments.pathfinding_lab",
    "jacobs_lab.instruments.three_body_lab",
]

SLOW = {
    "jacobs_lab.instruments.complexity_lab",
    "jacobs_lab.instruments.three_body_lab",
}

ALIASES = {
    "folding_computation": "jacobs_lab.computation.folding_computations",
    "Nested_mapper": "jacobs_lab.core.nested_mapper",
    "Level_tree": "jacobs_lab.structure.level_tree",
}


def _import(name: str):
    try:
        return importlib.import_module(name)
    except ModuleNotFoundError:
        target = ALIASES.get(name)

        if target:
            try:
                return importlib.import_module(target)
            except ModuleNotFoundError:
                return None

        return None


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Unified test runner for the folding laboratory."
    )
    ap.add_argument("--fast", action="store_true", help="skip slow labs")
    args = ap.parse_args(argv)

    passed = failed = missing = 0

    print("fold laboratory - canonical self-test ledger\\n")

    for group, names in (
        ("CORE", CORE),
        ("STRUCTURE", STRUCTURE),
        ("MATH LENSES", LENSES),
        ("COMPUTATION", COMPUTATION),
        ("INSTRUMENTS", INSTRUMENTS),
    ):
        print(f"-- {group} " + "-" * max(1, 50 - len(group)))

        for name in names:
            short = name.rsplit(".", 1)[-1]

            if args.fast and name in SLOW:
                print(f"   {short:<28} SKIPPED (--fast)")
                continue

            mod = _import(name)
            fn = getattr(mod, "_run_self_tests", None) if mod else None

            if mod is None or fn is None:
                missing += 1
                status = "MISSING" if mod is None else "NO SELF-TESTS"
                print(f"   {short:<28} {status}")
                continue

            t0 = time.perf_counter()

            try:
                fn()
                passed += 1
                print(f"   {short:<28} PASS {time.perf_counter() - t0:6.2f}s")
            except Exception:
                failed += 1
                print(f"   {short:<28} FAIL")
                traceback.print_exc()

        print()

    print(
        f"ledger: {passed}/{passed + failed} passed, "
        f"{failed} failed, {missing} missing"
    )

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
'''


LAB_COMPAT = '''from __future__ import annotations

import importlib


def import_folding():
    """Import the folding VM module from the canonical package layout."""
    try:
        return importlib.import_module(
            "jacobs_lab.computation.folding_computation"
        )
    except ModuleNotFoundError:
        return importlib.import_module(
            "jacobs_lab.computation.folding_computations"
        )


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


ROOT_INIT = '''"""Jacobs Lab package (canonical refinement)."""

__version__ = "0.4.0"
'''


def check_split_package():
    if not PKG.exists():
        raise SystemExit(
            f"Missing package directory: {PKG}\n" "Run tools/refine_package.py first."
        )

    if not (PKG / "core").exists():
        raise SystemExit(
            f"{PKG} does not appear to be split into subpackages.\n"
            "Run tools/split_subpackages.py first."
        )


def backup_package():
    if BACKUP.exists():
        shutil.rmtree(BACKUP)

    shutil.copytree(PKG, BACKUP)
    print(f"Backed up existing package to: {BACKUP}")


def rename_modules():
    renames = [
        ("core", "Nested_mapper.py", "core", "nested_mapper.py"),
        ("structure", "Level_tree.py", "structure", "level_tree.py"),
    ]

    for old_sub, old_name, new_sub, new_name in renames:
        src = PKG / old_sub / old_name
        dest = PKG / new_sub / new_name

        if not src.exists():
            continue

        dest.parent.mkdir(parents=True, exist_ok=True)

        if dest.exists():
            dest.write_bytes(src.read_bytes())
            src.unlink()
        else:
            src.rename(dest)

        print(f"Renamed {old_sub}/{old_name} -> {new_sub}/{new_name}")


def rewrite_all_files():
    count = 0

    for py in PKG.rglob("*.py"):
        if "__pycache__" in py.parts:
            continue

        text = py.read_text(encoding="utf-8", errors="ignore")
        original = text

        for old, new in TEXT_REPLACEMENTS:
            text = text.replace(old, new)

        if text != original:
            py.write_text(text, encoding="utf-8")
            count += 1

    print(f"Rewrote imports/references in {count} files")


def write_canonical_test_runners():
    testing = PKG / "testing"
    testing.mkdir(parents=True, exist_ok=True)

    (testing / "test_harness.py").write_text(TEST_HARNESS, encoding="utf-8")
    (testing / "run_all_tests.py").write_text(RUN_ALL_TESTS, encoding="utf-8")

    print("Wrote canonical testing/test_harness.py")
    print("Wrote canonical testing/run_all_tests.py")


def write_root_core_files():
    (PKG / "__init__.py").write_text(ROOT_INIT, encoding="utf-8")
    (PKG / "lab_compat.py").write_text(LAB_COMPAT, encoding="utf-8")

    print("Wrote package root __init__.py and lab_compat.py")


def write_subpackage_alias(sub: str, old_stem: str, new_stem: str):
    alias = PKG / sub / f"{old_stem}.py"

    alias.write_text(
        f'''"""Deprecated alias: {old_stem} -> {new_stem}."""

from . import {new_stem} as _impl  # noqa: F401
import sys as _sys

_sys.modules[__name__] = _impl
''',
        encoding="utf-8",
    )


def write_root_alias(alias_stem: str, sub: str, target_stem: str):
    alias = PKG / f"{alias_stem}.py"

    alias.write_text(
        f'''"""Compatibility alias: {alias_stem} -> {PACKAGE_NAME}.{sub}.{target_stem}."""

from .{sub} import {target_stem} as _impl  # noqa: F401
import sys as _sys

_sys.modules[__name__] = _impl
''',
        encoding="utf-8",
    )


def write_renamed_aliases():
    # Old-name aliases inside subpackages.
    write_subpackage_alias("core", "Nested_mapper", "nested_mapper")
    write_subpackage_alias("structure", "Level_tree", "level_tree")

    # Root compatibility aliases.
    write_root_alias("nested_mapper", "core", "nested_mapper")
    write_root_alias("Nested_mapper", "core", "nested_mapper")

    write_root_alias("level_tree", "structure", "level_tree")
    write_root_alias("Level_tree", "structure", "level_tree")

    print("Wrote temporary compatibility aliases for renamed modules")


def remove_root_aliases():
    removed = 0

    for py in PKG.glob("*.py"):
        if py.name in KEEP_ROOT_FILES:
            continue

        py.unlink()
        removed += 1

    print(f"Removed {removed} root-level compatibility aliases")


def main():
    ap = argparse.ArgumentParser(
        description="Canonicalize the split jacobs_lab package."
    )
    ap.add_argument(
        "--remove-root-aliases",
        action="store_true",
        help=(
            "Remove root-level compatibility aliases after canonicalization. "
            "Only do this once you are ready to require subpackage import paths."
        ),
    )

    args = ap.parse_args()

    check_split_package()
    backup_package()

    rename_modules()
    rewrite_all_files()

    write_canonical_test_runners()
    write_root_core_files()

    if not args.remove_root_aliases:
        write_renamed_aliases()
    else:
        remove_root_aliases()

    print()
    print(f"Canonical package written to: {PKG}")
    print()
    print("Next steps:")
    print("  python -m pip install -e .")
    print("  python -m jacobs_lab test")
    print()
    print("Canonical imports are now:")
    print("  jacobs_lab.core.nested_mapper")
    print("  jacobs_lab.structure.level_tree")
    print("  jacobs_lab.computation.folding_computations")
    print("  jacobs_lab.testing.test_harness")

    if not args.remove_root_aliases:
        print()
        print("Root compatibility aliases are still present.")
        print("When ready, remove them with:")
        print("  python tools/canonicalize_package.py --remove-root-aliases")


if __name__ == "__main__":
    main()
