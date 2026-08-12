from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from .category_theory import FiniteCategory, thin_category
from .folding_graph import FoldingGraph
from .general_recursive_mapper import RecursiveMapper
from .named_aliases import LETTER_TO_ROOT, PORTAL_LETTERS
from .set_theory import portal_quotient, quotient_set

PORTAL_PAIR = PORTAL_LETTERS["G"]  # (6, 9)
_SWAP = {PORTAL_PAIR[0]: PORTAL_PAIR[1], PORTAL_PAIR[1]: PORTAL_PAIR[0]}
LETTERS = "ABCDEFG"


def letter_category() -> FiniteCategory:
    fg = FoldingGraph()
    pairs = []
    for e in fg.edges:
        pairs += [(e.src, e.dst), (e.dst, e.src)]
    return thin_category(list(LETTERS), pairs)


def root_category() -> FiniteCategory:
    topo = RecursiveMapper(9, 2).topology
    fg = FoldingGraph()
    pairs = [(r, topo.advance(r)) for r in range(1, 10)]
    for e in fg.edges:
        ra, rb = LETTER_TO_ROOT[e.src], LETTER_TO_ROOT[e.dst]
        pairs += [(ra, rb), (rb, ra)]
    pairs += [PORTAL_PAIR, PORTAL_PAIR[::-1]]
    return thin_category(range(1, 10), pairs)


@dataclass(frozen=True)
class ThinFunctor:
    """Functor between thin categories, given by its object map."""

    name: str
    objects: Dict

    def arrow(self, f):
        a, b = f
        return (self.objects[a], self.objects[b])

    def is_functor(self, C: FiniteCategory, D: FiniteCategory) -> bool:
        return all(
            (not hs) or D.hom(self.objects[a], self.objects[b])
            for (a, b), hs in C.homs.items()
        )


@dataclass
class NaturalTransformation:
    """eta : F => G with components eta_X : F X -> G X in D."""

    name: str
    F: ThinFunctor
    G: ThinFunctor
    C: FiniteCategory
    D: FiniteCategory
    components: Dict

    def is_natural(self) -> bool:
        for (a, b), hs in self.C.homs.items():
            if not hs:
                continue
            f = next(iter(hs))
            if self.D.compose(self.F.arrow(f), self.components[b]) != self.D.compose(
                self.components[a], self.G.arrow(f)
            ):
                return False
        return True

    def is_iso(self) -> bool:
        return all(self.D.hom(b, a) for (a, b) in self.components.values())

    def vertical_compose(self, other: "NaturalTransformation"):
        return NaturalTransformation(
            f"{self.name}*{other.name}",
            self.F,
            other.G,
            self.C,
            self.D,
            {
                x: self.D.compose(self.components[x], other.components[x])
                for x in self.components
            },
        )


def build_portal_natural_isomorphism():
    C, D = letter_category(), root_category()
    F = ThinFunctor("literal_root", {L: LETTER_TO_ROOT[L] for L in LETTERS})
    G = ThinFunctor(
        "portal_flipped_root",
        {L: _SWAP.get(LETTER_TO_ROOT[L], LETTER_TO_ROOT[L]) for L in LETTERS},
    )
    return (
        C,
        D,
        F,
        G,
        NaturalTransformation(
            "portal_eta", F, G, C, D, {L: (F.objects[L], G.objects[L]) for L in LETTERS}
        ),
    )


def portal_quotient_category():
    classes = quotient_set(range(1, 10), [PORTAL_PAIR])
    cls_of = {r: c for c in classes for r in c}
    topo = RecursiveMapper(9, 2).topology
    fg = FoldingGraph()
    gens = [(r, topo.advance(r)) for r in range(1, 10)]
    for e in fg.edges:
        ra, rb = LETTER_TO_ROOT[e.src], LETTER_TO_ROOT[e.dst]
        gens += [(ra, rb), (rb, ra)]
    gens += [PORTAL_PAIR, PORTAL_PAIR[::-1]]
    return thin_category(classes, [(cls_of[a], cls_of[b]) for a, b in gens]), cls_of


def _run_self_tests():
    C, D, F, G, eta = build_portal_natural_isomorphism()
    assert F.is_functor(C, D) and G.is_functor(C, D)
    for L in "ABCE":
        r = LETTER_TO_ROOT[L]
        assert eta.components[L] == (r, r)
    assert eta.components["D"] == (9, 6)
    assert eta.components["F"] == (6, 9)
    assert eta.components["G"] == (6, 9)
    assert eta.is_natural() and eta.is_iso()

    eta_inv = NaturalTransformation(
        "portal_eta_inv",
        G,
        F,
        C,
        D,
        {L: (b, a) for L, (a, b) in eta.components.items()},
    )
    assert eta_inv.is_natural()
    id_t = eta.vertical_compose(eta_inv)
    for L in LETTERS:
        assert id_t.components[L] == (F.objects[L], F.objects[L])

    Q, cls_of = portal_quotient_category()
    assert {L: cls_of[F.objects[L]] for L in LETTERS} == {
        L: cls_of[G.objects[L]] for L in LETTERS
    }
    classes, letter_map = portal_quotient()
    assert set(Q.objects) == set(classes)
    assert letter_map["F"] == letter_map["G"] == letter_map["D"] == cls_of[6]
    print("All natural-transformation self-tests passed.")


if __name__ == "__main__":
    _run_self_tests()
    C, D, F, G, eta = build_portal_natural_isomorphism()
    print("\neta : literal_root => portal_flipped_root")
    for L in LETTERS:
        a, b = eta.components[L]
        print(f"  eta_{L}: {a} -> {b}   [{'portal' if a != b else 'id'}]")
    print(f"natural: {eta.is_natural()}, iso: {eta.is_iso()}")
