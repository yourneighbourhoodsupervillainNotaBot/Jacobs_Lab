from __future__ import annotations

"""
Surface quotients: square -> cylinder -> torus as staged cell quotients.

Decoded from the hand-drawn canvas (Square / Half-Plane / Plane / Cylinder /
Torus panels).  Combinatorial content:

Square   : V = A,B,C,D;  E = E(A->B), F(B->C), G(C->D), H(D->A);  1 face.
Cylinder : glue the vertical pair F~H  => vertices {A,B},{C,D}; seam (F,H).
Torus    : glue the horizontal pair E~G => one vertex class A=B=C=D and the
two edge cycles (E,G), (F,H).  V=1, E=2, F=1, chi=0, genus 1.

The "Half-Plane" and "Plane" panels are COVERS, not quotient steps: the
circle grid is the torus's universal cover (a Z^2 lattice of fundamental
domains), the sheared strip the cylinder's cover.  They visualize lifts.

Provenance labels (canvas): cylinder "c-A=B", "D=C-a", "H=F";
torus "A=B=C=D", "E=G", "H=F".  All verified in _run_self_tests().
"""

from dataclasses import dataclass
from typing import Tuple

from jacobs_lab.core.general_recursive_mapper import RecursiveTopology
from jacobs_lab.math_lenses.set_theory import UnionFind
from jacobs_lab.core.recursive_lattice import RecursiveLattice

VERTICES = ("A", "B", "C", "D")
EDGES = ("E", "F", "G", "H")
EDGE_ENDPOINTS = {
    "E": ("A", "B"),
    "F": ("B", "C"),
    "G": ("C", "D"),
    "H": ("D", "A"),
}
FACES = 1


@dataclass(frozen=True)
class Stage:
    name: str
    vertex_classes: Tuple[frozenset, ...]
    edge_classes: Tuple[frozenset, ...]
    faces: int = FACES
    orientable: bool = True

    @property
    def euler(self) -> int:
        return len(self.vertex_classes) - len(self.edge_classes) + self.faces

    @property
    def genus(self) -> int:
        """For closed orientable surfaces: chi = 2 - 2g."""
        return (2 - self.euler) // 2

    def class_of(self, cell: str) -> frozenset:
        for c in self.vertex_classes + self.edge_classes:
            if cell in c:
                return c
        raise KeyError(cell)


def gluing_consistency(edge_pairs, vertex_pairs) -> bool:
    """Every glued edge pair must glue its endpoints pairwise."""
    vp = {frozenset(p) for p in vertex_pairs}
    for e1, e2 in edge_pairs:
        a1, b1 = EDGE_ENDPOINTS[e1]
        a2, b2 = EDGE_ENDPOINTS[e2]
        straight = {frozenset((a1, a2)), frozenset((b1, b2))}
        twisted = {frozenset((a1, b2)), frozenset((b1, a2))}
        if not (straight <= vp or twisted <= vp):
            return False
    return True


def _stage(name, vertex_pairs, edge_pairs, orientable=True) -> Stage:
    uv = UnionFind(VERTICES)
    for a, b in vertex_pairs:
        uv.union(a, b)
    ue = UnionFind(EDGES)
    for a, b in edge_pairs:
        ue.union(a, b)
    vc = tuple(sorted(uv.classes(), key=lambda c: sorted(c)))
    ec = tuple(sorted(ue.classes(), key=lambda c: sorted(c)))
    return Stage(name, vc, ec, FACES, orientable)


def stage_square() -> Stage:
    return _stage("Square", (), ())


def stage_cylinder() -> Stage:
    # Join/fold along the vertical pair: B~A and C~D, seam F~H.
    return _stage("Cylinder", (("A", "B"), ("D", "C")), (("F", "H"),))


def stage_torus() -> Stage:
    # Second fold along the horizontal pair: A~D and B~C, seam E~G.
    return _stage(
        "Torus",
        (("A", "B"), ("D", "C"), ("A", "D"), ("B", "C")),
        (("F", "H"), ("E", "G")),
    )


def stage_klein() -> Stage:
    """Extension beyond the canvas: same first fold, TWISTED second fold."""
    return _stage(
        "Klein bottle",
        (("A", "B"), ("D", "C"), ("A", "C"), ("B", "D")),
        (("F", "H"), ("E", "G")),
        orientable=False,
    )


SEQUENCE = (stage_square(), stage_cylinder(), stage_torus())


def discrete_torus(radix: int = 9, multiplier: int = 2) -> Tuple[int, int]:
    """The recursive lattice's state space is a discrete torus:
    a product of two independent cycles (S1_x x S1_y)."""
    topo = RecursiveTopology(radix, multiplier)
    return tuple(len(c) for c in topo.cycles)


# ----------------------------------------------------------------------
# Covers: lifting lattice walks to the canvas's "Plane" / "Half-Plane"
# ----------------------------------------------------------------------
@dataclass(frozen=True)
class CoverPoint:
    i: int  # x cover coordinate (unwrapped, or wrapped residue)
    j: int  # y cover coordinate
    x_root: int  # projected lattice root
    y_root: int


_SQUARE_CORNERS = {(0, 0): "A", (1, 0): "B", (1, 1): "C", (0, 1): "D"}


def corner_label(i: int, j: int) -> str:
    """Which square corner (A,B,C,D) a lifted vertex sits over.

    The four corners of the fundamental square lift to the period-2
    sublattice of the plane cover -- the corner tags on the canvas's
    circle grid.
    """
    return _SQUARE_CORNERS[(i % 2, j % 2)]


class TorusCover:
    """Covering-space machinery for the discrete torus S1_x x S1_y.

    The torus is the lattice component containing `anchor`: a product of
    two root cycles of lengths L1 x L2.  Its universal cover is Z^2 (the
    canvas "Plane" panel); unwrapping one axis gives the cylinder cover
    (the "Half-Plane" panel).  Deck transformations are translations by
    (L1, 0) and (0, L2).
    """

    def __init__(self, radix: int = 9, multiplier: int = 2, anchor=(1, 1)):
        self.topo = RecursiveTopology(radix, multiplier)
        self.cycle_x = self._cycle_for(anchor[0])
        self.cycle_y = self._cycle_for(anchor[1])
        self.L1 = len(self.cycle_x)
        self.L2 = len(self.cycle_y)
        self.px = self.cycle_x.index(anchor[0])
        self.py = self.cycle_y.index(anchor[1])

    def _cycle_for(self, root: int):
        for c in self.topo.cycles:
            if root in c:
                return c
        raise ValueError(f"root {root} not on any cycle")

    def project(self, i: int, j: int) -> Tuple[int, int]:
        """Cover point -> torus (lattice) point."""
        return (
            self.cycle_x[(self.px + i) % self.L1],
            self.cycle_y[(self.py + j) % self.L2],
        )

    def lift_to_cover(
        self,
        moves: Sequence[str],
        start: Tuple[int, int] = (0, 0),
        unwrap: str = "both",
    ) -> List[CoverPoint]:
        """The unique lift of a RIGHT/UP/LEFT/DOWN walk.

        unwrap="both": plane cover Z^2 (universal cover of the torus)
        unwrap="x"   : cylinder cover (x unwrapped, y wrapped)
        unwrap="y"   : cylinder cover (y unwrapped, x wrapped)
        unwrap="none": the wrapped torus walk itself
        """
        if unwrap not in ("both", "x", "y", "none"):
            raise ValueError("unwrap must be both/x/y/none")

        i, j = start
        x, y = self.project(i, j)
        out = [CoverPoint(i, j, x, y)]

        for m in moves:
            if m == "RIGHT":
                i += 1
            elif m == "LEFT":
                i -= 1
            elif m == "UP":
                j += 1
            elif m == "DOWN":
                j -= 1
            else:
                raise ValueError(f"unknown move: {m}")

            wi = i if unwrap in ("both", "x") else (self.px + i) % self.L1
            wj = j if unwrap in ("both", "y") else (self.py + j) % self.L2
            x, y = self.project(i, j)
            out.append(CoverPoint(wi, wj, x, y))

        return out


def lift_to_cover(
    moves: Sequence[str],
    anchor=(1, 1),
    start=(0, 0),
    unwrap: str = "both",
    radix: int = 9,
    multiplier: int = 2,
) -> List[CoverPoint]:
    """Convenience wrapper: lift a lattice walk to the chosen cover."""
    return TorusCover(radix, multiplier, anchor).lift_to_cover(moves, start, unwrap)


def euler_report() -> str:
    lines = [f"{'stage':<14}{'V':>3}{'E':>3}{'F':>3}{'chi':>5}  orientable"]
    for s in (*SEQUENCE, stage_klein()):
        lines.append(
            f"{s.name:<14}{len(s.vertex_classes):>3}{len(s.edge_classes):>3}"
            f"{s.faces:>3}{s.euler:>5}  {s.orientable}"
        )
    return "\n".join(lines)


def _run_self_tests():
    sq, cy, to = stage_square(), stage_cylinder(), stage_torus()

    # Euler characteristics: disc -> cylinder -> torus.
    assert (len(sq.vertex_classes), len(sq.edge_classes), sq.euler) == (4, 4, 1)
    assert (len(cy.vertex_classes), len(cy.edge_classes), cy.euler) == (2, 3, 0)
    assert (len(to.vertex_classes), len(to.edge_classes), to.euler) == (1, 2, 0)
    assert to.genus == 1

    # Exact canvas merge classes.
    assert frozenset({"A", "B"}) in cy.vertex_classes  # "c-A=B"
    assert frozenset({"C", "D"}) in cy.vertex_classes  # "D=C-a"
    assert frozenset({"F", "H"}) in cy.edge_classes  # "H=F"
    assert to.vertex_classes[0] == frozenset({"A", "B", "C", "D"})  # "A=B=C=D"
    assert frozenset({"E", "G"}) in to.edge_classes  # "E=G"
    assert frozenset({"F", "H"}) in to.edge_classes  # "H=F"

    # Gluings are legal: glued edges' endpoints are glued vertices.
    assert gluing_consistency((("F", "H"),), (("A", "B"), ("D", "C")))
    assert gluing_consistency(
        (("F", "H"), ("E", "G")),
        (("A", "B"), ("D", "C"), ("A", "D"), ("B", "C")),
    )

    # Extension: the twisted variant has the same counts but is Klein.
    kl = stage_klein()
    assert kl.euler == 0 and len(kl.vertex_classes) == 1
    assert not kl.orientable and to.orientable

    # The lattice analogue: product of two cycles = discrete torus.
    assert discrete_torus() == (6, 3)

    # --- covers: lift_to_cover -----------------------------------------
    tc = TorusCover()
    assert (tc.L1, tc.L2) == (6, 6)

    moves = ["RIGHT", "RIGHT", "UP", "RIGHT", "UP", "UP"]
    plane = tc.lift_to_cover(moves)

    # The plane lift projects onto the RecursiveLattice walk exactly.
    lat = RecursiveLattice(9, 2)
    x, y = 1, 1
    assert (plane[0].x_root, plane[0].y_root) == (1, 1)
    for p, m in zip(plane[1:], moves):
        x, y = lat.move(x, y, m)
        assert (p.x_root, p.y_root) == (x, y)
    assert (plane[-1].i, plane[-1].j) == (
        sum(1 for m in moves if m == "RIGHT") - sum(1 for m in moves if m == "LEFT"),
        sum(1 for m in moves if m == "UP") - sum(1 for m in moves if m == "DOWN"),
    )  # net cover displacement = (3, 3) for this move list

    # Winding: L1 RIGHTs close on the torus but wrap once on the cover.
    loop = tc.lift_to_cover(["RIGHT"] * tc.L1)
    assert loop[-1].i == tc.L1
    assert (loop[-1].x_root, loop[-1].y_root) == (1, 1)

    # Deck transformations: (L1,0)/(0,L2) translations fix the projection.
    for a in range(3):
        for b in range(3):
            assert tc.project(2 + a * tc.L1, 3 + b * tc.L2) == tc.project(2, 3)

    # Cylinder cover: unwrapped axis matches the plane lift, wrapped axis
    # stays a residue in [0, L).
    cyl = tc.lift_to_cover(moves, unwrap="x")
    assert [p.i for p in cyl] == [p.i for p in plane]
    assert all(0 <= p.j < tc.L2 for p in cyl)

    # LEFT/DOWN retreat: the lift returns home on cover and torus.
    back = tc.lift_to_cover(["RIGHT", "UP", "LEFT", "DOWN"])
    assert (back[-1].i, back[-1].j) == (0, 0)
    assert (back[-1].x_root, back[-1].y_root) == (1, 1)

    # Square corners lift with period 2 (canvas Plane panel tags).
    assert [
        corner_label(0, 0),
        corner_label(1, 0),
        corner_label(1, 1),
        corner_label(0, 1),
    ] == ["A", "B", "C", "D"]
    assert corner_label(2, 2) == "A"

    print("All surface-quotient self-tests passed.")


if __name__ == "__main__":
    _run_self_tests()
    print()
    print(euler_report())
    print(
        "\nHalf-Plane/Plane panels are covers (lifts), not quotient steps;"
        "\nthe circle grid is the torus's Z^2 universal cover."
    )
