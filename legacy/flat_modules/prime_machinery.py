from __future__ import annotations

"""
Prime machinery over the existing layers.

Honest scope: no closed-form prime formula exists (or can be 'derived' --
the obstruction is a theorem, not a code limit).  What the codebase CAN do
is the four things that are possible:

  FILTER   : the topology's cycle partition is a mod-3 sieve in disguise --
             every prime > 3 has its digital root on the doubling cycle
             (1,2,4,8,7,5); the (3,6,9) orbit contains only the prime 3.
  TEST     : sieve of Eratosthenes as the practical baseline.
  CERTIFY  : Lucas certificates -- n is prime iff some a has ord_n(a)=n-1;
             a witness IS a machine-checkable proof.
  EXECUTE  : the folding computer is Turing-universal, so prime-related
             computation compiles to folds; here a Minsky mod-3 machine
             reproduces the admissibility filter on the universal VM.
"""

from math import gcd
from typing import List, Optional

from legacy.flat_modules.galois_fields import is_prime, multiplicative_order
from legacy.flat_modules.general_recursive_mapper import RecursiveTopology, digital_root
from legacy.flat_modules.turing_universality import MinskyInstr, MinskyMachine, run_minsky

TOPO = RecursiveTopology(9, 2)
DOUBLING = TOPO.pattern(1)  # the units cycle mod 9


# ----------------------------------------------------------------------
# 1) filter: topology admissibility (necessary condition)
# ----------------------------------------------------------------------


def is_admissible(n: int) -> bool:
    """Primes > 3 live on the doubling cycle; 3 is the only (3,6,9) prime."""
    if n < 2:
        return False
    if n == 3:
        return True
    return TOPO.pattern(digital_root(n)) == DOUBLING


# ----------------------------------------------------------------------
# 2) test: sieve baseline
# ----------------------------------------------------------------------


def sieve(limit: int) -> List[int]:
    if limit < 2:
        return []
    flags = [True] * (limit + 1)
    flags[0] = flags[1] = False
    for p in range(2, int(limit**0.5) + 1):
        if flags[p]:
            for m in range(p * p, limit + 1, p):
                flags[m] = False
    return [n for n in range(2, limit + 1) if flags[n]]


# ----------------------------------------------------------------------
# 3) certify: Lucas witnesses as proofs
# ----------------------------------------------------------------------


def lucas_certificate(n: int) -> Optional[int]:
    """A witness a with ord_n(a) == n-1 (proof of primality), else None."""
    if n < 4:
        return None  # 2, 3 handled as base cases
    for a in range(2, n):
        if gcd(a, n) != 1:
            continue
        if multiplicative_order(a, n) == n - 1:
            return a
    return None


def certified_prime(n: int) -> bool:
    if n in (2, 3):
        return True
    return lucas_certificate(n) is not None


# ----------------------------------------------------------------------
# 4) execute: Minsky mod-3 machine on the universal folding computer
# ----------------------------------------------------------------------


def mod3_machine() -> MinskyMachine:
    """c0 = n, c1 = result.  States 0/1/2 track consumed-mod-3; when a
    DEC finds the counter empty, the zero-branch deposits the remainder
    into c1 (states 3 = +1, 4/5 = +2).  States are contiguous so the
    compiler's dispatch is total; halt = 6."""
    return MinskyMachine(
        7,
        6,
        {
            0: MinskyInstr("DEC", 0, 1, 6),  # empty at consumed≡0 -> r=0, halt
            1: MinskyInstr("DEC", 0, 2, 3),  # empty at consumed≡1 -> deposit 1
            2: MinskyInstr("DEC", 0, 0, 4),  # empty at consumed≡2 -> deposit 2
            3: MinskyInstr("INC", 1, 6),
            4: MinskyInstr("INC", 1, 5),
            5: MinskyInstr("INC", 1, 6),
        },
    )


def folding_mod3(n: int) -> int:
    _, r = run_minsky(mod3_machine(), 2, (n, 0))
    return r


# ----------------------------------------------------------------------
# self-tests
# ----------------------------------------------------------------------


def _run_self_tests():
    primes = sieve(100)
    assert len(primes) == 25 and primes[0] == 2 and primes[-1] == 97

    # Filter: necessary, not sufficient.
    for p in primes:
        assert is_admissible(p)
    for n in range(4, 200):
        if n % 3 == 0:
            assert not is_admissible(n)
    assert is_admissible(25)  # passes filter, still composite

    # Certify: Lucas agrees with trial division, witnesses are proofs.
    for n in range(2, 120):
        assert certified_prime(n) == is_prime(n), n
    w = lucas_certificate(7)
    assert w is not None and multiplicative_order(w, 7) == 6

    # Execute: the universal folding computer reproduces mod-3,
    # i.e. the topology's admissibility filter, on the VM.
    for n in range(0, 16):
        assert folding_mod3(n) == n % 3, n
        if n > 3:
            assert (folding_mod3(n) != 0) == is_admissible(n)
    print("All prime-machinery self-tests passed.")


if __name__ == "__main__":
    _run_self_tests()
    print("\nprimes to 60 with digital roots (all >3 on the doubling cycle):")
    for p in sieve(60):
        print(
            f"  {p:>3}  dr={digital_root(p)}  cycle={'doubling' if is_admissible(p) and p != 3 else '3-6-9' if p == 3 else '?'}"
        )
    print(
        f"\nLucas witness for 97: a={lucas_certificate(97)} "
        f"(ord = 96 = 97-1, a machine-checkable proof)"
    )
    print(
        f"folding-VM mod-3 of 25: {folding_mod3(25)} "
        f"(admissible: {is_admissible(25)}, prime: {is_prime(25)})"
    )
