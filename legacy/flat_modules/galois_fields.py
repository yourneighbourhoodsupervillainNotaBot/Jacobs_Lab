from __future__ import annotations

from itertools import product
from math import gcd
from typing import Dict, List, Tuple

from legacy.flat_modules.general_recursive_mapper import RecursiveTopology


def is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0:
        return False
    d = 3
    while d * d <= n:
        if n % d == 0:
            return False
        d += 2
    return True


def egcd(a: int, b: int) -> Tuple[int, int, int]:
    if b == 0:
        return (a, 1, 0)
    g, x, y = egcd(b, a % b)
    return (g, y, x - (a // b) * y)


def modinv(a: int, m: int) -> int:
    g, x, _ = egcd(a % m, m)
    if g != 1:
        raise ValueError(f"{a} not invertible mod {m}")
    return x % m


def multiplicative_order(a: int, m: int) -> int:
    if gcd(a, m) != 1:
        raise ValueError("order defined only for units")
    k, x = 1, a % m
    while x != 1:
        x = (x * a) % m
        k += 1
    return k


class GFp:
    """Prime field GF(p), elements 0..p-1."""

    def __init__(self, p: int):
        if not is_prime(p):
            raise ValueError("p must be prime")
        self.p = p

    def add(self, a, b):
        return (a + b) % self.p

    def sub(self, a, b):
        return (a - b) % self.p

    def mul(self, a, b):
        return (a * b) % self.p

    def neg(self, a):
        return (-a) % self.p

    def inv(self, a):
        return modinv(a, self.p)

    def div(self, a, b):
        return self.mul(a, self.inv(b))

    def pow(self, a, e):
        return pow(a, e, self.p)

    def order(self, a):
        return multiplicative_order(a, self.p)

    def primitive_roots(self) -> List[int]:
        return [g for g in range(2, self.p) if self.order(g) == self.p - 1]


def ring_decomposition(radix: int) -> Dict[str, List[int]]:
    return {
        "zero": [0],
        "units": [a for a in range(1, radix) if gcd(a, radix) == 1],
        "zero_divisors": [a for a in range(1, radix) if gcd(a, radix) != 1],
    }


def galois_view(radix: int, multiplier: int = 2) -> Dict:
    """Algebraic reading of RecursiveTopology: prime radix => GF(p)* orbit;
    composite radix => units orbit + zero-divisor orbits (a ring, not a field)."""
    topo = RecursiveTopology(radix, multiplier)
    view = {
        "is_field": is_prime(radix),
        "decomposition": ring_decomposition(radix),
        "cycles": topo.cycles,
    }
    if is_prime(radix):
        order = multiplicative_order(multiplier, radix)
        view["multiplier_order"] = order
        view["multiplier_is_primitive_root"] = order == radix - 1
    elif gcd(multiplier, radix) == 1:
        view["units_orbit_len"] = multiplicative_order(multiplier % radix, radix)
    return view


class GFpn:
    """GF(p^n) as polynomials mod a monic irreducible; elements = coeff tuples."""

    def __init__(self, p: int, n: int, poly: Tuple[int, ...]):
        if not is_prime(p):
            raise ValueError("p must be prime")
        if len(poly) != n + 1 or poly[-1] != 1:
            raise ValueError("poly must be monic of degree n")
        self.p, self.n, self.poly = p, n, tuple(poly)
        self.q = p**n

    def zero(self):
        return (0,) * self.n

    def one(self):
        return (1,) + (0,) * (self.n - 1)

    def add(self, a, b):
        return tuple((x + y) % self.p for x, y in zip(a, b))

    def mul(self, a, b):
        p, n = self.p, self.n
        res = [0] * (2 * n - 1)
        for i, ca in enumerate(a):
            for j, cb in enumerate(b):
                if ca and cb:
                    res[i + j] = (res[i + j] + ca * cb) % p
        for d in range(2 * n - 2, n - 1, -1):
            c = res[d] % p
            if c:
                for i in range(n + 1):
                    res[d - n + i] = (res[d - n + i] - c * self.poly[i]) % p
        return tuple(res[:n])

    def pow(self, a, e):
        result, base = self.one(), a
        while e:
            if e & 1:
                result = self.mul(result, base)
            base = self.mul(base, base)
            e >>= 1
        return result

    def inv(self, a):
        r = self.pow(a, self.q - 2)
        if self.mul(a, r) != self.one():
            raise ValueError("not invertible (modulus not irreducible?)")
        return r

    def frobenius(self, a):
        return self.pow(a, self.p)

    def elements(self):
        return list(product(range(self.p), repeat=self.n))

    def is_field(self) -> bool:
        return all(
            (not any(e)) or self.mul(e, self.pow(e, self.q - 2)) == self.one()
            for e in self.elements()
        )


def find_irreducible(p: int, n: int) -> Tuple[int, ...]:
    for tail in product(range(p), repeat=n):
        if tail[0] == 0:
            continue
        poly = tuple(tail) + (1,)
        if GFpn(p, n, poly).is_field():
            return poly
    raise ValueError("none found")


def _run_self_tests():
    f = GFp(7)
    for a in range(1, 7):
        assert f.mul(a, f.inv(a)) == 1
        assert f.pow(a, 7) == a
    assert 3 in f.primitive_roots()

    view = galois_view(9, 2)
    assert not view["is_field"]
    assert set(view["decomposition"]["units"]) == {1, 2, 4, 5, 7, 8}
    assert view["units_orbit_len"] == 6
    view7 = galois_view(7, 3)
    assert view7["is_field"] and view7["multiplier_is_primitive_root"]

    F8 = GFpn(2, 3, find_irreducible(2, 3))
    assert F8.is_field() and F8.q == 8
    known = GFpn(2, 3, (1, 1, 0, 1))  # x^3 + x + 1
    x = (0, 1, 0)
    assert all(known.pow(x, k) != known.one() for k in range(1, 7))
    assert known.pow(x, 7) == known.one()
    a = (0, 1, 1)
    assert F8.frobenius(F8.frobenius(F8.frobenius(a))) == a
    print("All Galois-field self-tests passed.")


if __name__ == "__main__":
    _run_self_tests()
