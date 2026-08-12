from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

try:
    from folding_computation import (
        Combine,
        STATE_SCHEDULE,
        fold_strip,
        make_cell,
    )
except ModuleNotFoundError:  # pragma: no cover
    from legacy.flat_modules.folding_computations import (
        Combine,
        STATE_SCHEDULE,
        fold_strip,
        make_cell,
    )

from legacy.flat_modules.named_aliases import LETTER_TO_ROOT
from legacy.flat_modules.triangle_state_machine import MACRO_PATHS

STRIP = "GFEABCD"  # physical strip: fold chain reversed + main chain
PIVOT = 3  # the crease at A


@dataclass(frozen=True)
class Slot:
    """One folded slot: the two letters the fold brings together.
    The crease slot has the same letter on both sides."""

    front: str
    back: str


def fold_packet(strip: str = STRIP, pivot: int = PIVOT) -> Tuple[Slot, ...]:
    """Fold the strip at A; slot 0 = crease, then distance from the crease."""
    res = fold_strip(
        [make_cell(LETTER_TO_ROOT[c]) for c in strip], pivot, Combine.KEEP_RIGHT
    )
    # FIX: order by distance from the pivot (crease first), not absolute index.
    order = sorted(res.classes, key=lambda c: pivot - min(c))
    slots = []
    for cls in order:
        idx = sorted(cls)
        slots.append(Slot(front=strip[idx[-1]], back=strip[idx[0]]))
    return tuple(slots)


def face(packet: Tuple[Slot, ...]) -> Tuple[str, ...]:
    return tuple(s.front for s in packet)


def flex(packet: Tuple[Slot, ...]) -> Tuple[Slot, ...]:
    """The flexagon move: turn the packet over (reverse slots, swap sides)."""
    return tuple(Slot(s.back, s.front) for s in reversed(packet))


def face_of(letter: str) -> int:
    """Which face a letter is exposed on (A reads on face 1)."""
    if letter in ("D", "C", "B"):
        return 1
    if letter in ("F", "G", "E"):
        return 2
    return 1


def _run_self_tests():
    packet = fold_packet()

    # Slot 0 is the crease; the glued pairs follow at increasing distance.
    assert packet[0] == Slot("A", "A")
    assert set(packet[1:]) == {Slot("B", "E"), Slot("C", "F"), Slot("D", "G")}

    # The two faces are the text's two macro blocks (as letter sets);
    # face 1 read tip-inward is the literal D-C-B-A sequence.
    f1, f2 = face(packet), face(flex(packet))
    assert f1 == ("A", "B", "C", "D")
    assert f2 == ("G", "F", "E", "A")
    assert set(f1) == set(MACRO_PATHS["discontinues_1"])  # {A,D,C,B}
    assert set(f2) == set(MACRO_PATHS["continues_0"])  # {A,E,G,F}
    assert tuple(reversed(f1)) == ("D", "C", "B", "A")

    # Conservation laws: letter multiset (crease A is two-sided), period-2 flex.
    all_letters = [c for s in packet for c in (s.front, s.back)]
    assert sorted(all_letters) == sorted(STRIP + "A")
    assert flex(flex(packet)) == packet

    # The state loop uses exactly two flexes per lap (the two orientation
    # flips), matching the two face-changes in the loop's face trace.
    flips = sum(
        1
        for ops in STATE_SCHEDULE.values()
        for op in ops
        if op.kind == "FLIP_ORIENTATION"
    )
    loop = "FGEDCBA"
    trace = [face_of(l) for l in loop] + [face_of("F")]
    changes = sum(1 for a, b in zip(trace, trace[1:]) if a != b)
    assert flips == 2 == changes
    print("All flexagon self-tests passed.")


if __name__ == "__main__":
    _run_self_tests()
    p = fold_packet()
    print("\nPacket (crease first):", p)
    print("Face 1 (discontinues):", face(p))
    print("Face 2 (continues):   ", face(flex(p)))
