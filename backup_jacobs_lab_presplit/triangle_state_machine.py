from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple

from .general_recursive_mapper import RecursiveMapper
from .named_aliases import LETTER_TO_ROOT, PORTAL_LETTERS, resolve_letter_root


class Mode(Enum):
    CONTINUE = "continues"
    DISCONTINUE = "discontinues"


class AB(Enum):
    OUTSIDE = "outside"
    INSIDE = "inside"


class CPhase(Enum):
    BALANCED = "balanced"
    DOWN = "down"
    UP = "up"


@dataclass(frozen=True)
class TriangleState:
    letter: str
    bits: Tuple[str, str, str]
    mode: Mode
    ab: AB
    c: CPhase
    note: str = ""

    @property
    def root(self) -> int:
        return LETTER_TO_ROOT[self.letter]


@dataclass(frozen=True)
class TriangleTransition:
    src: str
    dst: str
    action: str
    note: str = ""


STATES: Dict[str, TriangleState] = {
    "F": TriangleState(
        "F",
        ("100", "010", "001"),
        Mode.CONTINUE,
        AB.OUTSIDE,
        CPhase.BALANCED,
        "restart loop",
    ),
    "G": TriangleState(
        "G", ("010", "100", "010"), Mode.CONTINUE, AB.OUTSIDE, CPhase.DOWN, "after F-E"
    ),
    "E": TriangleState(
        "E", ("001", "100", "100"), Mode.DISCONTINUE, AB.INSIDE, CPhase.DOWN
    ),
    "D": TriangleState(
        "D",
        ("001", "010", "100"),
        Mode.DISCONTINUE,
        AB.INSIDE,
        CPhase.BALANCED,
        "about to flip",
    ),
    "C": TriangleState(
        "C", ("001", "001", "100"), Mode.DISCONTINUE, AB.INSIDE, CPhase.UP
    ),
    "B": TriangleState(
        "B", ("010", "001", "010"), Mode.CONTINUE, AB.OUTSIDE, CPhase.UP, "after C-B"
    ),
    "A": TriangleState(
        "A",
        ("100", "001", "001"),
        Mode.CONTINUE,
        AB.OUTSIDE,
        CPhase.BALANCED,
        "after B-C",
    ),
}

TRANSITIONS: Tuple[TriangleTransition, ...] = (
    TriangleTransition("F", "G", "F-E", "C balanced -> down"),
    TriangleTransition("G", "E", "DISCONTINUE", "outside -> inside"),
    TriangleTransition("E", "D", "E-F", "C down -> balanced, flip pending"),
    TriangleTransition("D", "C", "FLIP", "C balanced -> up"),
    TriangleTransition("C", "B", "C-B", "inside -> outside"),
    TriangleTransition("B", "A", "B-C", "C up -> balanced"),
    TriangleTransition("A", "F", "RESTART/A-F", "close loop"),
)

MACRO_PATHS: Dict[str, Tuple[str, ...]] = {
    "continues_0": ("A", "E", "G", "F"),
    "discontinues_1": ("A", "D", "C", "B"),
}


@dataclass(frozen=True)
class StateEdge:
    src: str
    dst: str
    kind: str
    action: str
    topo_label: str


class TriangleStateMachine:
    """Executable state machine for the triangle language (source of truth)."""

    def __init__(self, radix: int = 9, multiplier: int = 2):
        self.states = STATES
        self.transitions = TRANSITIONS
        self._next = {t.src: t for t in TRANSITIONS}
        self.mapper = RecursiveMapper(radix, multiplier)

    def state(self, letter: str) -> TriangleState:
        return self.states[letter]

    def transition(self, letter: str) -> TriangleTransition:
        return self._next[letter]

    def next_letter(self, letter: str) -> str:
        return self.transition(letter).dst

    def letters(self, start: str, steps: int) -> List[str]:
        out, current = [], start
        for _ in range(steps):
            out.append(current)
            current = self.next_letter(current)
        return out

    def classify_transition(self, t: TriangleTransition) -> str:
        return self.mapper.classify_root_pair(
            self.states[t.src].root, self.states[t.dst].root
        )

    def classify_all(self) -> List[Tuple[TriangleTransition, str]]:
        return [(t, self.classify_transition(t)) for t in self.transitions]

    def state_edges(self) -> List[StateEdge]:
        return [
            StateEdge(t.src, t.dst, "state", t.action, self.classify_transition(t))
            for t in self.transitions
        ]

    def resolve_root(self, letter: str, context: Optional[str] = None) -> int:
        return resolve_letter_root(letter, context)

    def validate_macro(self, name: str) -> bool:
        return name in MACRO_PATHS and all(l in self.states for l in MACRO_PATHS[name])


def _run_self_tests():
    sm = TriangleStateMachine()
    assert sm.letters("F", 7) == ["F", "G", "E", "D", "C", "B", "A"]
    assert sm.next_letter("A") == "F"
    assert [sm.states[l].root for l in "ABCDEFG"] == [3, 5, 8, 9, 7, 6, 6]
    assert sm.resolve_root("G") == 6 and sm.resolve_root("G", "D") == 9
    labels = {(t.src, t.dst): lab for t, lab in sm.classify_all()}
    assert labels[("A", "F")] == "same cycle, advance 1"
    assert labels[("C", "B")] == "same cycle, advance 2"
    assert labels[("G", "E")] == "different cycles (jump)"
    assert labels[("F", "G")] == "same root (state-only change)"
    assert len(sm.state_edges()) == 7
    assert sm.validate_macro("continues_0") and sm.validate_macro("discontinues_1")
    print("All triangle-state-machine self-tests passed.")


if __name__ == "__main__":
    _run_self_tests()
