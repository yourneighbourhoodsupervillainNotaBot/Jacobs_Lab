"""Unified test runner for the folding laboratory.

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
    "jacobs_lab.core.surface_quotients",
    "jacobs_lab.core.recursive_lattice",
    "jacobs_lab.core.addition_graph",
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

    print("fold laboratory - canonical self-test ledger\n")

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
