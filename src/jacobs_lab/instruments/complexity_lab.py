from __future__ import annotations

import random
import time
from typing import List, Optional, Sequence, Tuple

try:
    from jacobs_lab.computation.folding_computations import Combine, Instr, run_program
except ModuleNotFoundError:  # pragma: no cover
    from jacobs_lab.computation.folding_computations import Combine, Instr, run_program

from jacobs_lab.computation.turing_universality import (
    MinskyInstr,
    MinskyMachine,
    run_minsky,
)

# ----------------------------------------------------------------------
# 1) NP, empirically: verifier (polynomial) vs brute-force search (exponential)
# ----------------------------------------------------------------------


def make_instance(n: int, seed: int, hi: int = 50):
    rnd = random.Random(seed)
    vals = [rnd.randint(1, hi) for _ in range(n)]
    return vals, sum(vals)  # target = full sum: a solution exists


def verify_subset_sum(vals: Sequence[int], target: int, cert_mask: int) -> bool:
    """O(n) certificate check -- the 'NP' side: checking is easy."""
    s = 0
    for i, v in enumerate(vals):
        if (cert_mask >> i) & 1:
            s += v
    return s == target


def search_subset_sum(vals: Sequence[int], target: int) -> Optional[int]:
    """2^n brute force -- the 'P?' side: searching looks hard."""
    n = len(vals)
    for mask in range(1 << n):
        s = 0
        for i, v in enumerate(vals):
            if (mask >> i) & 1:
                s += v
        if s == target:
            return mask
    return None


# ----------------------------------------------------------------------
# 2) A verifier compiled to the universal folding computer (existence level)
# ----------------------------------------------------------------------


def eq_machine() -> MinskyMachine:
    """c0 == c1 ? result in c2.  halt = 4 (result stays 0 on inequality).

    MinskyInstr fields: (op, counter, next_state, zero_state).
    0: a empty?  yes -> 2 (then test t)   no  -> dec a, go 1
    1: t empty?  yes -> halt (unequal)    no  -> dec t, go 0
    2: t empty?  yes -> 3 (equal)         no  -> halt (unequal)
    3: INC result, halt
    """
    return MinskyMachine(
        5,
        4,
        {
            0: MinskyInstr("DEC", 0, 1, 2),
            1: MinskyInstr("DEC", 1, 0, 4),
            2: MinskyInstr("DEC", 1, 4, 3),
            3: MinskyInstr("INC", 2, 4),
        },
    )


def folding_eq(a: int, t: int) -> int:
    _, _, r = run_minsky(eq_machine(), 3, (a, t, 0))
    return r


# ----------------------------------------------------------------------
# 3) Time-bounded realizability: resource limits change what is computable
# ----------------------------------------------------------------------

ROOT_DOMAIN = [(3, 5), (6, 9), (8, 7)]


def _base_programs():
    base = [
        Instr("GLUE", 0, r)
        for r in (
            Combine.DIGITAL_SUM,
            Combine.DIGITAL_PRODUCT,
            Combine.KEEP_LEFT,
            Combine.KEEP_RIGHT,
        )
    ] + [
        Instr("FOLD", p, r)
        for p in (0, 1)
        for r in (Combine.DIGITAL_SUM, Combine.KEEP_LEFT)
    ]
    return [(p,) for p in base] + [(a, b) for a in base for b in base]


def realizable_count(budget: int) -> int:
    """How many distinct functions the fold computer computes within a
    step budget -- a tiny resource-bounded descriptional-complexity curve."""
    seen = set()
    for prog in _base_programs():
        try:
            table = []
            for x in ROOT_DOMAIN:
                _, out, _ = run_program(
                    list(x), list(prog) + [Instr("READ", 0)], max_steps=budget
                )
                table.append(out[0])
            seen.add(tuple(table))
        except (ValueError, RuntimeError):
            continue  # invalid or over-budget: not realizable
    return len(seen)


# ----------------------------------------------------------------------
# self-tests
# ----------------------------------------------------------------------


def _run_self_tests():
    # Verifier and search agree; checking a certificate is exact.
    vals, target = [3, 7, 11, 5, 9], 16
    mask = search_subset_sum(vals, target)
    assert mask is not None and verify_subset_sum(vals, target, mask)
    assert not verify_subset_sum(vals, 1000, mask)
    for n in (4, 8, 12):
        v, t = make_instance(n, 11)
        m = search_subset_sum(v, t)
        assert m is not None and verify_subset_sum(v, t, m)

    # The folding VM verifies equality (universality, existence-level).
    for a in range(7):
        for t in range(7):
            assert folding_eq(a, t) == (1 if a == t else 0), (a, t)

    # Time is a real constraint: no budget, no computation; more budget,
    # at least as much realized (resource-bounded realizability).
    assert realizable_count(1) == 0
    c2, c4 = realizable_count(2), realizable_count(4)
    assert c2 >= 4 and c4 >= c2

    # Measured asymmetry: verification polynomial, search exponential.
    v16, t16 = make_instance(16, 7)
    t0 = time.perf_counter()
    verify_subset_sum(v16, t16, (1 << 16) - 1)
    vt = time.perf_counter() - t0
    t0 = time.perf_counter()
    search_subset_sum(v16, t16)
    st = time.perf_counter() - t0
    assert st > vt
    return vt, st


if __name__ == "__main__":
    vt, st = _run_self_tests()
    print("All complexity-lab self-tests passed.")

    print(
        f"\nsubset-sum: verify(16) = {vt * 1e6:.1f} us | search(16) = {st * 1e3:.1f} ms"
    )
    print("\n n |   search time (ms)  (doubling => exponential)")
    for n in (6, 10, 14, 18):
        v, t = make_instance(n, 7)
        t0 = time.perf_counter()
        search_subset_sum(v, t)
        print(f"{n:>3} | {(time.perf_counter() - t0) * 1e3:>10.2f}")

    print("\nstep budget -> distinct functions realizable:")
    for b in (1, 2, 3, 4):
        print(f"  budget {b}: {realizable_count(b)}")
    print("\nDemonstration only: verification is easy, search is exponential,")
    print("and time bounds change what is computable -- the empirical face of")
    print("P vs NP.  The question itself remains a matter for new mathematics.")
