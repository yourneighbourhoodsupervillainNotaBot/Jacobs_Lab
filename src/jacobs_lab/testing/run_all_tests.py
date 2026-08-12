"""Unified test runner for the folding laboratory.

Usage:
    python run_all_tests.py            # run every module's self-tests
    python run_all_tests.py --fast     # skip the slower instrument labs

Every module carries its own executed self-tests; this runner imports each
module, invokes them, and prints a ledger.  Non-zero exit code on failure.
"""

from __future__ import annotations

import argparse
import importlib
import sys
import time
import traceback

CORE = [
    "general_recursive_mapper",
    "named_aliases",
    "recursive_lattice",
    "triangle_state_machine",
    "folding_graph",
    "Nested_mapper",
    "Level_tree",
]
LENSES = [
    "galois_fields",
    "set_theory",
    "category_theory",
    "natural_transformations",
]
COMPUTATION = [
    "folding_computation",
    "turing_universality",
    "universality_probe",
    "flexagon",
]
INSTRUMENTS = [
    "quintic_analysis",
    "fold_codec",
    "fold_complexity",
    "prime_machinery",
    "complexity_lab",
    "pathfinding_lab",
    "three_body_lab",
]
SLOW = {"complexity_lab", "three_body_lab"}


def _import(name):
    try:
        return importlib.import_module(f"jacobs_lab.{name}")
    except ModuleNotFoundError:
        if name == "folding_computation":  # local spelling variant
            try:
                return importlib.import_module("jacobs_lab.computation.folding_computations")
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
    print("fold laboratory - unified self-test ledger\n")
    for group, names in (
        ("CORE", CORE),
        ("MATH LENSES", LENSES),
        ("COMPUTATION", COMPUTATION),
        ("INSTRUMENTS", INSTRUMENTS),
    ):
        print(f"-- {group} " + "-" * max(1, 50 - len(group)))
        for name in names:
            if args.fast and name in SLOW:
                print(f"   {name:<26} SKIPPED (--fast)")
                continue
            mod = _import(name)
            fn = getattr(mod, "_run_self_tests", None) if mod else None
            if mod is None or fn is None:
                missing += 1
                print(f"   {name:<26} {'MISSING' if mod is None else 'NO SELF-TESTS'}")
                continue
            t0 = time.perf_counter()
            try:
                fn()
                passed += 1
                print(f"   {name:<26} PASS {time.perf_counter() - t0:6.2f}s")
            except Exception:
                failed += 1
                print(f"   {name:<26} FAIL")
                traceback.print_exc()
        print()

    print(
        f"ledger: {passed}/{passed + failed} passed, "
        f"{failed} failed, {missing} missing"
    )
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
