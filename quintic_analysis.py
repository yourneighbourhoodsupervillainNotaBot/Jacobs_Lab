from __future__ import annotations

from fractions import Fraction
from itertools import product
from typing import List, Optional, Sequence, Tuple

from galois_fields import GFp, is_prime
from general_recursive_mapper import digital_root

# Polynomials are ascending coefficient lists: coeffs[i] = coefficient of x^i.


# ----------------------------------------------------------------------
# evaluation / integer helpers
# ----------------------------------------------------------------------


def eval_poly(coeffs: Sequence, x) -> object:
    acc = 0
    for c in reversed(coeffs):
        acc = acc * x + c
    return acc


def divisors(n: int) -> List[int]:
    n = abs(n)
    if n == 0:
        return [1]
    return [d for d in range(1, n + 1) if n % d == 0]


def rational_roots(coeffs: Sequence[int]) -> List[Fraction]:
    """Exact rational roots via the rational root theorem."""
    a0, an = coeffs[0], coeffs[-1]
    roots = set()
    for p in divisors(a0):
        for q in divisors(an):
            for s in (1, -1):
                r = Fraction(s * p, q)
                if eval_poly(coeffs, r) == 0:
                    roots.add(r)
    return sorted(roots)


def mod9_sieve(coeffs: Sequence[int], candidates: Sequence[int]) -> List[int]:
    """Necessary condition: P(r) == 0 mod 9 (digital root 9)."""
    out = []
    for r in candidates:
        v = eval_poly(coeffs, r)
        if v == 0 or digital_root(abs(v)) == 9:
            out.append(r)
    return out


# ----------------------------------------------------------------------
# polynomial arithmetic over GF(p)
# ----------------------------------------------------------------------


def gf_divmod(F: GFp, num: Sequence[int], den: Sequence[int]):
    num = [c % F.p for c in num]
    den = [c % F.p for c in den]
    while len(den) > 1 and den[-1] == 0:
        den.pop()
    while len(num) > 1 and num[-1] == 0:
        num.pop()
    dn = len(den) - 1
    lead = den[-1]
    q = [0] * max(1, len(num) - dn)
    for i in range(len(num) - 1, dn - 1, -1):
        coeff = F.div(num[i], lead)
        if coeff:
            q[i - dn] = coeff
            for j in range(dn + 1):
                num[i - dn + j] = F.sub(num[i - dn + j], F.mul(coeff, den[j]))
    while len(num) > 1 and num[-1] == 0:
        num.pop()
    while len(q) > 1 and q[-1] == 0:
        q.pop()
    return q, num


def factor_mod_p(F: GFp, coeffs: Sequence[int]) -> List[Tuple[int, ...]]:
    """Monic irreducible factors of coeffs over GF(p)."""
    poly = [c % F.p for c in coeffs]
    while len(poly) > 1 and poly[-1] == 0:
        poly.pop()
    lead = poly[-1]
    poly = [F.div(c, lead) for c in poly]

    factors = []
    while len(poly) - 1 >= 1:
        found = None
        for k in range(1, (len(poly) - 1) // 2 + 1):
            for tail in product(range(F.p), repeat=k):
                div = tuple(tail) + (1,)
                q, r = gf_divmod(F, poly, div)
                if r == (0,) or r == [0]:
                    found = (div, q)
                    break
            if found:
                break
        if found is None:
            factors.append(tuple(poly))
            break
        factors.append(found[0])
        poly = list(found[1])
    return factors


def cycle_type(F: GFp, coeffs: Sequence[int]) -> Optional[List[int]]:
    """Dedekind: factorization degrees = cycle type of Frobenius at p.
    Returns None when p is ramified (repeated factor)."""
    factors = factor_mod_p(F, coeffs)
    if len(set(factors)) != len(factors):
        return None
    return sorted(len(f) - 1 for f in factors)


def s5_evidence(coeffs: Sequence[int], prime_limit: int = 64):
    """(prime giving a 5-cycle, prime giving a transposition) => Gal = S5,
    hence not solvable by radicals. Requires degree 5."""
    if len(coeffs) - 1 != 5:
        return None
    p5 = p2 = None
    for p in range(2, prime_limit):
        if not is_prime(p) or coeffs[-1] % p == 0:
            continue
        ct = cycle_type(GFp(p), coeffs)
        if ct is None:
            continue
        if ct == [5] and p5 is None:
            p5 = p  # irreducible mod p => 5-cycle (and irr. over Q)
        if ct == [1, 1, 1, 2] and p2 is None:
            p2 = p  # transposition
        if p5 and p2:
            return (p5, p2)
    return (p5, p2) if (p5 and p2) else None


# ----------------------------------------------------------------------
# numeric complex roots (Durand-Kerner)
# ----------------------------------------------------------------------


def durand_kerner(coeffs: Sequence, max_iter: int = 500, tol: float = 1e-12):
    cs = [complex(c) for c in coeffs]
    while len(cs) > 1 and cs[-1] == 0:
        cs.pop()
    n = len(cs) - 1
    cs = [c / cs[-1] for c in cs]
    z = [complex(0.4, 0.9) ** k for k in range(1, n + 1)]
    for _ in range(max_iter):
        worst = 0.0
        for i in range(n):
            num = eval_poly(cs, z[i])
            den = 1.0
            for j in range(n):
                if j != i:
                    den *= z[i] - z[j]
            delta = num / den if den else 0j
            z[i] -= delta
            worst = max(worst, abs(delta))
        if worst < tol:
            break
    return z


# ----------------------------------------------------------------------
# self-tests
# ----------------------------------------------------------------------


def _run_self_tests():
    # 1) mod-p factorization: known products and irreducibles over GF(2).
    F2 = GFp(2)
    assert factor_mod_p(F2, [1, 0, 0, 1, 0, 1]) == [(1, 0, 0, 1, 0, 1)]  # irr.
    f = factor_mod_p(
        F2, [1, 1, 0, 0, 0, 1]
    )  # x^5+x = (x^2+x+1)(x^3+x^2+1)? no: x^5+x+1
    assert sorted(len(x) - 1 for x in f) == [2, 3]

    # 2) S5 certificate on a CRT-built quintic:
    #    mod 2 = x^5+x^2+1  (irreducible  -> 5-cycle)
    #    mod 3 = x^5-x = x(x-1)(x+1)(x^2+1)  (-> transposition [1,1,1,2])
    crt = [3, 2, 0, 3, 0, 1]
    assert s5_evidence(crt) == (2, 3)

    # 3) Rational roots + mod-9 sieve.
    assert rational_roots([-32, 0, 0, 0, 0, 1]) == [Fraction(2)]
    sieved = mod9_sieve([-32, 0, 0, 0, 0, 1], [2, 4, 5, 11])
    assert 2 in sieved and 4 not in sieved

    # 4) Numeric roots.
    r = durand_kerner([2, -3, 1])  # x^2 - 3x + 2
    assert sorted(round(x.real) for x in r) == [1, 2]
    quint = [-1, -1, 0, 0, 0, 1]  # x^5 - x - 1
    for root in durand_kerner(quint):
        assert abs(eval_poly([complex(c) for c in quint], root)) < 1e-6
    print("All quintic-analysis self-tests passed.")


if __name__ == "__main__":
    _run_self_tests()

    quint = [-1, -1, 0, 0, 0, 1]  # x^5 - x - 1
    print("\nNumeric roots of x^5 - x - 1:")
    for root in durand_kerner(quint):
        print(f"  {root.real:+.10f} {root.imag:+.10f}i")
    ev = s5_evidence(
        quint, prime_limit=200
    )  # p=163 is needed for the transposition witness
    print(f"S5 evidence (5-cycle prime, transposition prime): {ev}")
    if ev is not None:
        print(
            "=> Galois group S5: roots exist numerically but are not "
            "expressible in radicals (Abel-Ruffini, certified)."
        )
    else:
        print(
            "=> No certificate found in this prime range -- claim NOT certified. "
            "(x^5-x-1 is known to have Galois group S5 by other means, but this "
            "script's own search did not prove it here.)"
        )
