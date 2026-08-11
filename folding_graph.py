from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

from named_aliases import LETTER_TO_ROOT
from triangle_state_machine import TriangleStateMachine


@dataclass(frozen=True)
class FoldEdge:
    src: str
    dst: str
    kind: str  # "chain", "jump", or "state"
    action: Optional[str] = None
    topo_label: Optional[str] = None


class FoldingGraph:
    """Structural fold graph (T0-fixed) plus the state-machine layer (T3)."""

    MAIN_CHAIN = ("A", "B", "C", "D")
    FOLD_CHAIN = ("A", "E", "F", "G")
    CROSS_LINKS = (("E", "B"), ("F", "C"))

    def __init__(self):
        self.state_machine = TriangleStateMachine()
        self.structural_edges: List[FoldEdge] = []
        self.state_edges: List[FoldEdge] = []
        for chain in (self.MAIN_CHAIN, self.FOLD_CHAIN):
            for a, b in zip(chain, chain[1:]):
                self.structural_edges.append(FoldEdge(a, b, "chain"))
        for a, b in self.CROSS_LINKS:
            self.structural_edges.append(FoldEdge(a, b, "jump"))
        for e in self.state_machine.state_edges():
            self.state_edges.append(
                FoldEdge(e.src, e.dst, e.kind, e.action, e.topo_label)
            )
        self.edges = self.structural_edges  # backward-compatible alias

    @property
    def all_edges(self) -> List[FoldEdge]:
        return self.structural_edges + self.state_edges

    def neighbors(self, letter: str, include_state: bool = True) -> List[FoldEdge]:
        source = self.all_edges if include_state else self.structural_edges
        return [e for e in source if e.src == letter or e.dst == letter]

    def label_edge(self, edge: FoldEdge) -> str:
        if edge.topo_label:
            return edge.topo_label
        return self.state_machine.mapper.classify_root_pair(
            LETTER_TO_ROOT[edge.src], LETTER_TO_ROOT[edge.dst]
        )

    def classify_edges(self, include_state: bool = True) -> List[Tuple[FoldEdge, str]]:
        source = self.all_edges if include_state else self.structural_edges
        return [(e, self.label_edge(e)) for e in source]


def _run_self_tests():
    fg = FoldingGraph()
    assert len(fg.structural_edges) == 8 and len(fg.edges) == 8
    assert len(fg.state_edges) == 7 and len(fg.all_edges) == 15
    assert FoldEdge("A", "B", "chain") in fg.structural_edges
    assert FoldEdge("E", "B", "jump") in fg.structural_edges
    assert not any(e.src in ("D", "G") for e in fg.structural_edges)
    assert any(e.src == "D" for e in fg.state_edges)
    assert any(e.src == "G" for e in fg.state_edges)
    labels = {(e.src, e.dst): lab for e, lab in fg.classify_edges(True)}
    assert labels[("A", "F")] == "same cycle, advance 1"
    assert labels[("F", "G")] == "same root (state-only change)"
    print("All folding-graph self-tests passed.")
    return fg.classify_edges(True)


if __name__ == "__main__":
    classified = _run_self_tests()
    print()
    for edge, label in classified:
        action = f" [{edge.action}]" if edge.action else ""
        print(f"{edge.src} -> {edge.dst} ({edge.kind}){action}: {label}")
