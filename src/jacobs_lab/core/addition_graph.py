from __future__ import annotations

"""
Addition graph: a digital-root Cayley graph (addition, not multiplication).

Where RecursiveTopology gives every root exactly one successor (a fixed
multiplier, producing disjoint cycles), AdditionGraph gives every root
radix+1 successors -- one per chosen digit.  It is NOT a reversible encoding
scheme and must not be used as one (see design doc section 3.4); it is a
complementary, choice-driven way of moving between digital roots.

Provenance (design doc section 4): decoded from the hand-drawn
``digital_roots.canvas``.  Of the 15 checkable single-step edges (raw sum <= 9),
13 match digital_root(a+b) exactly and are reproduced in
CANVAS_CONFIRMED_EDGES.  Two match a*b instead -- arithmetic slips made while
drawing -- and are recorded in CANVAS_DISCREPANCIES rather than silently
reproduced.  The canvas also draws sums of 10 as looping to root 0; this
module uses the correct value digital_root(10) == 1 (CANVAS_SUM_TEN_LOOPS).
"""

import heapq
import itertools
from typing import Dict, List, Optional, Sequence, Tuple

from jacobs_lab.core.general_recursive_mapper import digital_root

# ----------------------------------------------------------------------
# Provenance data (verified against the canvas, then against the rule)
# ----------------------------------------------------------------------
CANVAS_CONFIRMED_EDGES: Tuple[Tuple[int, int, int], ...] = (
    (1, 2, 3),
    (1, 3, 4),
    (1, 4, 5),
    (1, 6, 7),
    (1, 7, 8),
    (1, 8, 9),
    (2, 2, 4),
    (2, 4, 6),
    (2, 5, 7),
    (2, 6, 8),
    (3, 3, 6),
    (3, 4, 7),
    (4, 5, 9),
)  # 13 edges, all with a + b <= 9

CANVAS_DISCREPANCIES: Tuple[Tuple[int, int, int], ...] = (
    (2, 3, 6),  # drawn 6 == 2*3; correct sum root is 5
    (1, 5, 5),  # drawn 5 == 1*5; correct sum root is 6
)

CANVAS_SUM_TEN_LOOPS: Tuple[Tuple[int, int], ...] = (
    (2, 8),  # canvas drew -> 0; digital_root(10) == 1
    (5, 5),  # canvas drew -> 0; digital_root(10) == 1
)


class AdditionGraph:
    """Cayley graph of digital roots under addition of a chosen digit."""

    def __init__(self, radix: int = 9):
        if radix < 2:
            raise ValueError("radix must be >= 2")
        self.radix = radix
        self.roots = tuple(range(0, radix + 1))  # includes the transient 0
        self.digits = tuple(range(0, radix + 1))

    # -- core API (design doc section 2) -------------------------------
    def step(self, r: int, d: int) -> int:
        """Add digit d to root r and reduce via digital root."""
        return digital_root(r + d, self.radix)

    def neighbors(self, r: int) -> Dict[int, int]:
        """Every digit 0..radix that can be added from r, and where it lands."""
        return {d: self.step(r, d) for d in self.digits}

    def all_edges(self) -> List[Tuple[int, int, int]]:
        """(from_root, digit_added, to_root) for every possible edge."""
        return [(r, d, self.step(r, d)) for r in self.roots for d in self.digits]

    def path(self, start: int, digits: Sequence[int]) -> List[int]:
        """Walk from `start`, adding each digit in `digits` in turn."""
        out = [start]
        cur = start
        for d in digits:
            cur = self.step(cur, d)
            out.append(cur)
        return out

    # -- extension: inverse queries (document the non-invertibility) ----
    def digits_to_reach(self, src: int, dst: int) -> List[int]:
        """All digits that move src to dst (0, 1, or 2 of them)."""
        return [d for d in self.digits if self.step(src, d) == dst]

    def digit_to_reach(self, src: int, dst: int) -> Optional[int]:
        """Cheapest digit achieving src -> dst, or None if impossible."""
        ds = self.digits_to_reach(src, dst)
        return min(ds) if ds else None

    # -- extension: collision / source-state analysis (section 3.3/3.4) -
    def collision_profile(self) -> Dict[int, Dict]:
        prof = {}
        for r in self.roots:
            seen: Dict[int, int] = {}
            collisions = []
            for d in self.digits:
                t = self.step(r, d)
                if t in seen:
                    collisions.append((seen[t], d, t))
                else:
                    seen[t] = d
            prof[r] = {"distinct": len(seen), "collisions": collisions}
        return prof

    def reachability_summary(self) -> Dict:
        return {
            "source_state": 0,
            "zero_in_edges": [
                (r, d) for r in self.roots for d in self.digits if self.step(r, d) == 0
            ],
            "nonzero_mutually_reachable": all(
                self.digit_to_reach(r, t) is not None
                for r in range(1, self.radix + 1)
                for t in range(1, self.radix + 1)
            ),
        }

    # -- extension: restricted / weighted shortest paths (section 5.4) --
    def shortest_path(
        self,
        src: int,
        dst: int,
        allowed_digits: Optional[Sequence[int]] = None,
        weight_fn=None,
    ) -> Tuple[Optional[int], Optional[List[int]]]:
        """Dijkstra over (root, digit) edges.

        allowed_digits turns the dense graph into a genuine Cayley graph on a
        generator set (e.g. (1, 2)), making shortest paths non-trivial.
        weight_fn(d) assigns the cost of using digit d (default 1 per hop).
        Returns (cost, digits) or (None, None) when unreachable.
        """
        allowed = tuple(allowed_digits) if allowed_digits is not None else self.digits
        w = weight_fn if weight_fn is not None else (lambda d: 1)

        best: Dict[int, int] = {}
        ctr = itertools.count()
        heap = [(0, next(ctr), src, ())]

        while heap:
            cost, _, node, digits = heapq.heappop(heap)
            if node in best and best[node] <= cost:
                continue
            best[node] = cost
            if node == dst:
                return cost, list(digits)
            for d in allowed:
                nxt = self.step(node, d)
                nd = cost + w(d)
                if nxt not in best or nd < best.get(nxt, float("inf")):
                    heapq.heappush(heap, (nd, next(ctr), nxt, digits + (d,)))

        return None, None

    def cayley_table(self) -> List[List[int]]:
        return [[self.step(r, d) for d in self.digits] for r in self.roots]


# ----------------------------------------------------------------------
# Extension: "casting out nines" checksum utilities (section 5.5)
# ----------------------------------------------------------------------
def check_sum(a: int, b: int, c: int, radix: int = 9) -> bool:
    """Necessary condition for a + b == c (classic casting-out-nines)."""
    lhs = digital_root(digital_root(a, radix) + digital_root(b, radix), radix)
    return lhs == digital_root(c, radix)


def check_product(a: int, b: int, c: int, radix: int = 9) -> bool:
    """Necessary condition for a * b == c."""
    lhs = digital_root(digital_root(a, radix) * digital_root(b, radix), radix)
    return lhs == digital_root(c, radix)


# ----------------------------------------------------------------------
# Extension: deterministic digit walks for the test-suite pipeline (5.1/5.6)
# ----------------------------------------------------------------------
def digit_for_result(result, index: int, radix: int = 9) -> int:
    """Deterministic digit 0..radix for a TestResult-like object.

    Keyed off the module name (stable across runs); a failure shifts the
    digit by 5 so failures audibly/visibly change the walk.
    """
    name = getattr(result, "module", str(result))
    base = sum(ord(ch) for ch in name) % (radix + 1)
    if not getattr(result, "passed", True):
        base = (base + 5) % (radix + 1)
    return base


def walk_for_results(graph: AdditionGraph, results, start_root: int = 1):
    """(digits, root_walk) -- a richer replacement for the binary PASS/FAIL
    move selection in test_walk_engine (design doc section 5.1)."""
    digits = [digit_for_result(r, i, graph.radix) for i, r in enumerate(results)]
    return digits, graph.path(start_root, digits)


# ----------------------------------------------------------------------
# self-tests (design doc section 6)
# ----------------------------------------------------------------------
def _run_self_tests():
    g = AdditionGraph()

    # 3.1 full graph size: (radix+1)^2 edges, radix+1 neighbors each.
    assert len(g.all_edges()) == (g.radix + 1) ** 2 == 100
    assert all(len(g.neighbors(r)) == g.radix + 1 for r in g.roots)

    # Section 2 concrete row for root 5.
    assert g.neighbors(5) == {
        0: 5,
        1: 6,
        2: 7,
        3: 8,
        4: 9,
        5: 1,
        6: 2,
        7: 3,
        8: 4,
        9: 5,
    }

    # 4) provenance: 13 confirmed edges, 2 recorded slips, sum-10 fix.
    assert len(CANVAS_CONFIRMED_EDGES) == 13
    for a, b, c in CANVAS_CONFIRMED_EDGES:
        assert a + b <= 9 and g.step(a, b) == c
    for a, b, drawn in CANVAS_DISCREPANCIES:
        assert g.step(a, b) != drawn
        assert digital_root(a * b) == drawn  # what the canvas matched
        assert g.step(a, b) == digital_root(a + b)  # the correct rule
    for a, b in CANVAS_SUM_TEN_LOOPS:
        assert digital_root(10) == 1 and g.step(a, b) == 1

    # 3.3 root 0 is a source/transient state.
    assert g.neighbors(0) == {d: d for d in g.digits}
    assert all(g.step(r, d) != 0 for r in range(1, 10) for d in g.digits)
    assert g.reachability_summary()["zero_in_edges"] == [(0, 0)]

    # 3.2 nonzero roots fully connected in one step (exhaustive).
    for r in range(1, 10):
        for t in range(1, 10):
            assert g.digit_to_reach(r, t) is not None
    assert g.digit_to_reach(0, 7) == 7

    # 3.4 collision structure: 0 is bijective; every nonzero root has the
    # single {0, radix} collision.
    prof = g.collision_profile()
    assert prof[0]["distinct"] == 10 and not prof[0]["collisions"]
    for r in range(1, 10):
        assert prof[r]["distinct"] == 9
        assert g.digits_to_reach(r, r) == [0, 9]

    # Extension: restricted-generator shortest paths are non-trivial.
    cost, digits = g.shortest_path(1, 9, allowed_digits=(1, 2))
    assert cost == 4 and all(d in (1, 2) for d in digits)
    assert g.path(1, digits)[-1] == 9
    assert g.shortest_path(5, 0)[0] is None  # 0 unreachable
    cost2, _ = g.shortest_path(5, 7, weight_fn=lambda d: d)
    assert cost2 == 2  # digit 2 is cheapest

    # Extension: casting-out-nines checksums.
    assert check_sum(123, 456, 579) and not check_sum(123, 456, 578)
    assert check_product(12, 13, 156) and not check_product(12, 13, 157)

    # Extension: deterministic result-walks.
    class _R:
        def __init__(self, module, passed):
            self.module, self.passed = module, passed

    digits, walk = walk_for_results(g, [_R("a", True), _R("b", False)], 1)
    assert len(walk) == 3 and walk[0] == 1 and walk == g.path(1, digits)

    print("All addition-graph self-tests passed.")


if __name__ == "__main__":
    _run_self_tests()

    g = AdditionGraph()
    print("\nAll moves from root 5:")
    for d, t in g.neighbors(5).items():
        print(f"  5 + {d} -> {t}")

    print("\nCollision profile (distinct targets / collisions):")
    for r, info in g.collision_profile().items():
        print(
            f"  root {r}: {info['distinct']} distinct, collisions={info['collisions']}"
        )

    cost, digits = g.shortest_path(1, 9, allowed_digits=(1, 2))
    print(
        f"\nshortest path 1 -> 9 with generators {{1,2}}: cost {cost}, digits {digits}"
    )

    try:  # optional: sonify a digit walk with the existing 9-EDO layer
        from sonify import SonifiedStep, chord_freqs, render, write_wav

        digits = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        walk = g.path(1, digits)
        steps = [
            SonifiedStep(
                letter=str(d),
                root=r,
                freqs=chord_freqs(r),
                duration=0.3,
                accent=(d in (0, 9)),
                label=f"+{d}",
                arpeggiate=(d % 2 == 0),
            )
            for d, r in zip(digits, walk[1:])
        ]
        write_wav("addition_walk.wav", render(steps))
        print("\nWrote addition_walk.wav (digit walk sonified)")
    except ModuleNotFoundError:
        pass
