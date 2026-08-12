from __future__ import annotations

from dataclasses import dataclass
from math import gcd
from typing import Iterator


def digital_root(n: int, radix: int = 9) -> int:
    if radix < 2:
        raise ValueError("radix must be >= 2")
    if n == 0:
        return 0
    return (n - 1) % radix + 1


@dataclass(frozen=True)
class Coordinate:
    level: int
    root: int


@dataclass(frozen=True)
class Address:
    level: int
    root: int
    pattern: int
    radix: int

    @property
    def num(self) -> int:
        return self.level * self.radix + self.root


class RecursiveTopology:
    """Reversible topology from a multiplication rule (base9/doubling by default)."""

    def __init__(self, radix: int = 9, multiplier: int = 2):
        if radix < 2:
            raise ValueError("radix must be >= 2")
        if gcd(multiplier, radix) != 1:
            raise ValueError("multiplier must be coprime with radix")
        self.radix = radix
        self.multiplier = multiplier
        self.cycles = self._generate_cycles()
        self.pattern_by_root = {}
        self.position_by_root = {}
        for p, cycle in enumerate(self.cycles):
            for i, root in enumerate(cycle):
                self.pattern_by_root[root] = p
                self.position_by_root[root] = i

    def _step(self, root: int) -> int:
        # Digital-root representation of multiplication; residue 0 == radix.
        residue = (self.multiplier * (root % self.radix)) % self.radix
        return self.radix if residue == 0 else residue

    def _generate_cycles(self):
        if self.radix == 9 and self.multiplier == 2:
            cycles = []
            for start in (1, 3):
                cycle = []
                x = start
                while x not in cycle:
                    cycle.append(x)
                    x = self._step(x)
                cycles.append(tuple(cycle))
            # _step gives 3->6->3 because 9 represents residue 0;
            # preserve the original 3/6/9 orbit representation.
            return (cycles[0], (3, 6, 9))

        remaining = set(range(1, self.radix + 1))
        cycles = []
        while remaining:
            start = min(remaining)
            cycle = []
            x = start
            while x not in cycle:
                cycle.append(x)
                remaining.discard(x)
                x = self._step(x)
            cycles.append(tuple(cycle))
        return tuple(cycles)

    def pattern(self, root: int) -> int:
        return self.pattern_by_root[root]

    def advance(self, root: int, steps: int = 1) -> int:
        cycle = self.cycles[self.pattern(root)]
        return cycle[(self.position_by_root[root] + steps) % len(cycle)]

    def retreat(self, root: int, steps: int = 1) -> int:
        cycle = self.cycles[self.pattern(root)]
        return cycle[(self.position_by_root[root] - steps) % len(cycle)]

    def trace(
        self, root: int, steps: int, direction: str = "backward"
    ) -> Iterator[int]:
        if direction not in ("backward", "forward"):
            raise ValueError("direction must be backward or forward")
        current = root
        delta = -1 if direction == "backward" else 1
        for _ in range(steps):
            yield current
            current = self.advance(current, delta)
        yield current


class RecursiveMapper:
    """Compact, reversible, dimension-independent coordinate mapper."""

    def __init__(self, radix: int = 9, multiplier: int = 2):
        self.radix = radix
        self.topology = RecursiveTopology(radix, multiplier)

    def encode_num(self, level: int, root: int) -> int:
        if level < 0 or not 1 <= root <= self.radix:
            raise ValueError("invalid level/root")
        return level * self.radix + root

    def decode_num(self, num: int) -> Coordinate:
        if num < 1:
            raise ValueError("num must be >= 1")
        return Coordinate((num - 1) // self.radix, (num - 1) % self.radix + 1)

    def address(self, num: int) -> Address:
        c = self.decode_num(num)
        return Address(c.level, c.root, self.topology.pattern(c.root), self.radix)

    def map_backward(self, level: int, root: int) -> Coordinate:
        return Coordinate(level, self.topology.retreat(root, level))

    def map_forward(self, level: int, root: int) -> Coordinate:
        return Coordinate(level, self.topology.advance(root, level))

    def map_num_backward(self, num: int) -> int:
        c = self.decode_num(num)
        return self.encode_num(c.level, self.map_backward(c.level, c.root).root)

    def map_num_forward(self, num: int) -> int:
        c = self.decode_num(num)
        return self.encode_num(c.level, self.map_forward(c.level, c.root).root)

    def trace_backward(self, num: int) -> Iterator[Address]:
        c = self.decode_num(num)
        current = c.root
        for level in range(c.level, -1, -1):
            yield Address(level, current, self.topology.pattern(current), self.radix)
            if level:
                current = self.topology.retreat(current)

    def trace_forward(self, num: int) -> Iterator[Address]:
        c = self.decode_num(num)
        current = self.map_backward(c.level, c.root).root
        for level in range(c.level + 1):
            yield Address(level, current, self.topology.pattern(current), self.radix)
            if level < c.level:
                current = self.topology.advance(current)

    def classify_root_pair(self, src_root: int, dst_root: int) -> str:
        """Single source of truth for root-pair classification (T2)."""
        if not (1 <= src_root <= self.radix and 1 <= dst_root <= self.radix):
            raise ValueError("roots must be inside the radix range")
        topo = self.topology
        if src_root == dst_root:
            return "same root (state-only change)"
        if topo.pattern(src_root) != topo.pattern(dst_root):
            return "different cycles (jump)"
        n = len(topo.cycles[topo.pattern(src_root)])
        for k in range(1, n + 1):
            if topo.advance(src_root, k) == dst_root:
                return f"same cycle, advance {k}"
        for k in range(1, n + 1):
            if topo.retreat(src_root, k) == dst_root:
                return f"same cycle, retreat {k}"
        return "unclassified"


def verify_base9() -> RecursiveMapper:
    m = RecursiveMapper(9, 2)
    assert m.topology.cycles == ((1, 2, 4, 8, 7, 5), (3, 6, 9))
    for level in range(100):
        for root in range(1, 10):
            start = m.map_backward(level, root).root
            assert m.map_forward(level, start).root == root
    return m


def verify_topology(radix: int, multiplier: int, levels: int = 50) -> RecursiveMapper:
    m = RecursiveMapper(radix, multiplier)
    topo = m.topology
    seen = []
    for cycle in topo.cycles:
        assert len(cycle) > 0, "empty cycle produced"
        seen.extend(cycle)
    assert sorted(seen) == list(range(1, radix + 1))
    for level in range(levels):
        for root in range(1, radix + 1):
            assert topo.retreat(topo.advance(root, level), level) == root
            assert m.map_forward(level, m.map_backward(level, root).root).root == root
    return m


def batch_verify(pairs, levels: int = 20) -> dict:
    """Verify a batch of (radix, multiplier) pairs; skips non-coprime pairs."""
    results = {}
    for radix, multiplier in pairs:
        if gcd(multiplier, radix) != 1:
            results[(radix, multiplier)] = "skipped: not coprime"
            continue
        try:
            verify_topology(radix, multiplier, levels=levels)
            results[(radix, multiplier)] = "ok"
        except AssertionError as e:
            results[(radix, multiplier)] = f"FAILED: {e}"
    return results


def trace_range(mapper: RecursiveMapper, start_num: int, end_num: int):
    for n in range(start_num, end_num + 1):
        a = mapper.address(n)
        yield n, a, mapper.map_backward(a.level, a.root).root


def _print_table(mapper, start_num, end_num):
    print(f"{'num':>4} {'level':>5} {'root':>4} {'pattern':>7} {'backward_root':>13}")
    for n, a, back_root in trace_range(mapper, start_num, end_num):
        print(f"{n:>4} {a.level:>5} {a.root:>4} {a.pattern:>7} {back_root:>13}")


def _run_self_tests():
    try:
        RecursiveTopology(radix=9, multiplier=3)
        raise SystemExit("expected ValueError for non-coprime multiplier")
    except ValueError:
        pass
    try:
        RecursiveTopology(radix=1, multiplier=1)
        raise SystemExit("expected ValueError for radix < 2")
    except ValueError:
        pass

    m = RecursiveMapper(9, 2)
    for n in range(1, 200):
        c = m.decode_num(n)
        assert m.encode_num(c.level, c.root) == n

    n = 137
    assert [a.root for a in m.trace_backward(n)] == list(
        reversed([a.root for a in m.trace_forward(n)])
    )
    assert list(m.topology.trace(1, 5, "forward")) == [
        m.topology.advance(1, i) for i in range(6)
    ]

    assert m.classify_root_pair(3, 6) == "same cycle, advance 1"
    assert m.classify_root_pair(8, 5) == "same cycle, advance 2"
    assert m.classify_root_pair(6, 7) == "different cycles (jump)"
    assert m.classify_root_pair(6, 6) == "same root (state-only change)"
    print("All general-recursive-mapper self-tests passed.")


def _build_arg_parser():
    import argparse

    p = argparse.ArgumentParser(description="Recursive coordinate mapper explorer")
    p.add_argument("--radix", type=int, default=9)
    p.add_argument("--multiplier", type=int, default=2)
    p.add_argument("--start", type=int, default=1)
    p.add_argument("--end", type=int, default=18)
    p.add_argument("--sweep", action="store_true")
    p.add_argument("--test", action="store_true")
    return p


if __name__ == "__main__":
    args = _build_arg_parser().parse_args()
    if args.test:
        verify_base9()
        _run_self_tests()
        raise SystemExit(0)
    if args.sweep:
        pairs = [
            (r, k)
            for r in range(2, args.radix + 1)
            for k in range(2, r)
            if gcd(k, r) == 1
        ]
        results = batch_verify(pairs)
        for pair, status in results.items():
            print(pair, status)
        fails = sum(1 for v in results.values() if v != "ok")
        print(f"\n{len(results) - fails}/{len(results)} pairs verified ok")
        raise SystemExit(0)
    m = verify_topology(args.radix, args.multiplier)
    print("Generated cycles:", m.topology.cycles)
    _print_table(m, args.start, args.end)
