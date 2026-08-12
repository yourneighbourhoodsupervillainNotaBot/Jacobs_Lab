from __future__ import annotations
import importlib
import time
import traceback
from dataclasses import dataclass
from typing import List, Optional

# Every module in the lab that exposes a _run_self_tests() function.
# (sonify.py and test_harness.py itself are deliberately excluded --
# sonifying/visualizing sonify's own test would be a strange loop, and a
# module can't sensibly appear in a report of itself.)
MODULE_NAMES = [
    "Level_tree",
    "Nested_mapper",
    "category_theory",
    "complexity_lab",
    "flexagon",
    "fold_codec",
    "fold_complexity",
    "folding_computations",
    "folding_graph",
    "galois_fields",
    "general_recursive_mapper",
    "named_aliases",
    "natural_transformations",
    "pathfinding_lab",
    "prime_machinery",
    "quintic_analysis",
    "recursive_lattice",
    "set_theory",
    "three_body_lab",
    "triangle_state_machine",
    "turing_universality",
    "universality_probe",
]


@dataclass
class TestResult:
    module: str
    passed: bool
    duration: float
    error: Optional[str] = None


def run_all_tests(module_names: List[str] = None) -> List[TestResult]:
    """Import each module fresh and run its _run_self_tests(). Order is
    preserved from module_names (default MODULE_NAMES) -- this order becomes
    the sequence of steps fed to both the sonifier and the lattice walk, so
    it's deterministic and reproducible run to run."""
    names = module_names if module_names is not None else MODULE_NAMES
    results: List[TestResult] = []
    for name in names:
        start = time.perf_counter()
        try:
            mod = importlib.import_module(name)
            if not hasattr(mod, "_run_self_tests"):
                results.append(TestResult(name, False, 0.0, "no _run_self_tests() found"))
                continue
            # _run_self_tests() in this codebase prints on success and
            # raises AssertionError on failure -- both are handled here
            # rather than assumed.
            mod._run_self_tests()
            duration = time.perf_counter() - start
            results.append(TestResult(name, True, duration))
        except Exception as e:
            duration = time.perf_counter() - start
            results.append(TestResult(name, False, duration, f"{type(e).__name__}: {e}"))
    return results


def _run_self_tests():
    # A tiny synthetic module set to prove pass AND fail are both handled
    # correctly, without depending on any real module actually failing.
    import types

    ok_mod = types.ModuleType("ok_mod")
    ok_mod._run_self_tests = lambda: None
    fail_mod = types.ModuleType("fail_mod")
    def _boom():
        raise AssertionError("synthetic failure for testing")
    fail_mod._run_self_tests = _boom

    import sys
    sys.modules["ok_mod"] = ok_mod
    sys.modules["fail_mod"] = fail_mod

    results = run_all_tests(["ok_mod", "fail_mod"])
    assert len(results) == 2
    assert results[0].passed and results[0].error is None
    assert not results[1].passed and "synthetic failure" in results[1].error

    print("All test-harness self-tests passed.")


if __name__ == "__main__":
    _run_self_tests()
    print()
    print("Running the full lab suite...")
    results = run_all_tests()
    n_pass = sum(r.passed for r in results)
    for r in results:
        status = "PASS" if r.passed else "FAIL"
        print(f"  [{status}] {r.module:28s} {r.duration*1000:6.1f}ms" + (f"  {r.error}" if r.error else ""))
    print(f"\n{n_pass}/{len(results)} modules passed.")
