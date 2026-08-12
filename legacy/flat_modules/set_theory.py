from __future__ import annotations

from itertools import combinations
from typing import Dict, Iterable, List, Tuple

from legacy.flat_modules.folding_graph import FoldingGraph
from legacy.flat_modules.general_recursive_mapper import RecursiveTopology
from legacy.flat_modules.named_aliases import LETTER_TO_ROOT, PORTAL_LETTERS


class UnionFind:
    def __init__(self, elements: Iterable):
        self.parent = {e: e for e in elements}

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[rb] = ra

    def classes(self) -> List[frozenset]:
        groups: Dict[object, set] = {}
        for e in self.parent:
            groups.setdefault(self.find(e), set()).add(e)
        return [frozenset(g) for g in groups.values()]


def quotient_set(elements: Iterable, pairs: Iterable[Tuple]) -> List[frozenset]:
    uf = UnionFind(elements)
    for a, b in pairs:
        uf.union(a, b)
    return sorted(uf.classes(), key=lambda c: (len(c), sorted(map(str, c))))


def is_partition(elements, classes) -> bool:
    seen = []
    for c in classes:
        seen.extend(c)
    return sorted(seen) == sorted(elements) and all(c for c in classes)


def powerset(s: Iterable) -> List[frozenset]:
    items = list(s)
    out = []
    for r in range(len(items) + 1):
        out.extend(frozenset(c) for c in combinations(items, r))
    return out


class FiniteFunction:
    def __init__(self, domain, codomain, mapping: Dict):
        self.domain = frozenset(domain)
        self.codomain = frozenset(codomain)
        if set(mapping) != set(self.domain):
            raise ValueError("mapping must cover the domain")
        if any(v not in self.codomain for v in mapping.values()):
            raise ValueError("mapping must land in the codomain")
        self.mapping = dict(mapping)

    def __call__(self, x):
        return self.mapping[x]

    def injective(self):
        v = list(self.mapping.values())
        return len(v) == len(set(v))

    def surjective(self):
        return set(self.mapping.values()) == set(self.codomain)

    def bijective(self):
        return self.injective() and self.surjective()

    def compose(self, other: "FiniteFunction") -> "FiniteFunction":
        if other.codomain != self.domain:
            raise ValueError("codomain/domain mismatch")
        return FiniteFunction(
            other.domain, self.codomain, {x: self(other(x)) for x in other.domain}
        )

    def inverse(self) -> "FiniteFunction":
        if not self.bijective():
            raise ValueError("inverse needs a bijection")
        return FiniteFunction(
            self.codomain, self.domain, {v: k for k, v in self.mapping.items()}
        )


def topology_partition(radix=9, multiplier=2) -> List[frozenset]:
    return [frozenset(c) for c in RecursiveTopology(radix, multiplier).cycles]


def portal_quotient(radix=9):
    classes = quotient_set(range(1, radix + 1), list(PORTAL_LETTERS.values()))
    letter_map = {
        letter: next(c for c in classes if LETTER_TO_ROOT[letter] in c)
        for letter in LETTER_TO_ROOT
    }
    return classes, letter_map


def fold_quotient():
    return quotient_set(list("ABCDEFG"), FoldingGraph().CROSS_LINKS)


def _run_self_tests():
    parts = topology_partition()
    assert is_partition(list(range(1, 10)), parts) and len(parts) == 2
    classes, letter_map = portal_quotient()
    assert len(classes) == 8
    assert letter_map["F"] == letter_map["G"] == letter_map["D"]
    fq = fold_quotient()
    assert frozenset({"B", "E"}) in fq and frozenset({"C", "F"}) in fq
    f = FiniteFunction(set("ABCDEFG"), {3, 5, 6, 7, 8, 9}, LETTER_TO_ROOT)
    assert f.surjective() and not f.injective()
    assert len(powerset({1, 2})) == 4
    print("All set-theory self-tests passed.")


if __name__ == "__main__":
    _run_self_tests()
