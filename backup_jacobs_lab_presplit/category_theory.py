from __future__ import annotations

from typing import Dict, List, Tuple

from .folding_graph import FoldingGraph
from .general_recursive_mapper import RecursiveMapper, RecursiveTopology
from .named_aliases import LETTER_TO_ROOT
from .set_theory import UnionFind


class FiniteCategory:
    """Finite category given by explicit hom-sets and a compose rule."""

    def __init__(self, objects, homs: Dict[Tuple, frozenset], compose, identities):
        self.objects = frozenset(objects)
        self.homs = {(a, b): frozenset(h) for (a, b), h in homs.items()}
        self.compose = compose
        self.identities = identities

    def hom(self, a, b):
        return self.homs.get((a, b), frozenset())

    def connected_components(self) -> List[frozenset]:
        uf = UnionFind(self.objects)
        for (a, b), hs in self.homs.items():
            if hs:
                uf.union(a, b)
        return uf.classes()


def topology_groupoid(topo: RecursiveTopology) -> FiniteCategory:
    """Action groupoid of Z on the cycles: morphisms (r, k, s)."""
    objects = list(range(1, topo.radix + 1))
    homs = {}
    for cycle in topo.cycles:
        n = len(cycle)
        pos = {r: i for i, r in enumerate(cycle)}
        for r in cycle:
            for s in cycle:
                homs[(r, s)] = frozenset({(r, (pos[s] - pos[r]) % n, s)})

    def compose(m1, m2):
        r, k, s = m1
        s2, j, t = m2
        assert s == s2
        return (r, (k + j) % len(topo.cycles[topo.pattern(r)]), t)

    return FiniteCategory(objects, homs, compose, {o: (o, 0, o) for o in objects})


def thin_category(objects, generating_pairs) -> FiniteCategory:
    """Thin (preorder) category from reflexive-transitive reachability."""
    objs = list(objects)
    reach = {(a, b): (a == b) for a in objs for b in objs}
    for a, b in generating_pairs:
        reach[(a, b)] = True
    for c in objs:
        for a in objs:
            for b in objs:
                if reach[(a, c)] and reach[(c, b)]:
                    reach[(a, b)] = True
    homs = {
        (a, b): (frozenset({(a, b)}) if reach[(a, b)] else frozenset())
        for a in objs
        for b in objs
    }

    def compose(m1, m2):
        a, b = m1
        b2, c = m2
        assert b == b2
        return (a, c)

    return FiniteCategory(objs, homs, compose, {o: (o, o) for o in objs})


def _run_self_tests():
    topo = RecursiveMapper(9, 2).topology

    G = topology_groupoid(topo)
    assert len(G.connected_components()) == 2
    m = next(iter(G.hom(1, 2)))
    assert G.compose(G.identities[1], m) == m
    assert G.compose(m, G.identities[2]) == m
    assert G.compose(m, next(iter(G.hom(2, 4)))) == next(iter(G.hom(1, 4)))

    step_pairs = [(r, topo.advance(r)) for r in range(1, 10)]
    assert len(thin_category(range(1, 10), step_pairs).connected_components()) == 2

    fg = FoldingGraph()
    fold_pairs = []
    for e in fg.edges:
        ra, rb = LETTER_TO_ROOT[e.src], LETTER_TO_ROOT[e.dst]
        fold_pairs += [(ra, rb), (rb, ra)]
    FT = thin_category(range(1, 10), step_pairs + fold_pairs)
    assert len(FT.connected_components()) == 1
    for e in fg.edges:
        assert FT.hom(LETTER_TO_ROOT[e.src], LETTER_TO_ROOT[e.dst])
    print("All category-theory self-tests passed.")


if __name__ == "__main__":
    _run_self_tests()
