from __future__ import annotations

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
