from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Sequence, Tuple

from jacobs_lab.core.general_recursive_mapper import digital_root
from jacobs_lab.core.named_aliases import LETTER_TO_ROOT, PORTAL_LETTERS
from jacobs_lab.math_lenses.set_theory import UnionFind
from jacobs_lab.structure.triangle_state_machine import AB, CPhase, TriangleStateMachine


class Combine(Enum):
    KEEP_LEFT = "keep_left"
    KEEP_RIGHT = "keep_right"
    DIGITAL_SUM = "digital_sum"
    DIGITAL_PRODUCT = "digital_product"
    PORTAL_MERGE = "portal_merge"


@dataclass(frozen=True)
class Cell:
    """A strip/lattice cell: combined value plus the members it glued."""

    value: int
    members: frozenset = field(default_factory=frozenset)

    @property
    def portal(self) -> bool:
        return {6, 9} <= self.members


def make_cell(v: int) -> Cell:
    return Cell(v, frozenset({v}))


def combine_cells(a: Cell, b: Cell, rule: Combine, radix: int = 9) -> Cell:
    members = a.members | b.members
    if rule is Combine.KEEP_LEFT:
        value = a.value
    elif rule is Combine.KEEP_RIGHT:
        value = b.value
    elif rule is Combine.DIGITAL_SUM:
        value = digital_root(a.value + b.value, radix)
    elif rule is Combine.DIGITAL_PRODUCT:
        value = digital_root(a.value * b.value, radix)
    elif rule is Combine.PORTAL_MERGE:
        value = 6 if {6, 9} <= members else digital_root(a.value + b.value, radix)
    else:
        raise ValueError(rule)
    return Cell(value, members)


@dataclass(frozen=True)
class FoldRecord:
    pivot: int
    pairs: Tuple[Tuple[int, int], ...]


@dataclass(frozen=True)
class FoldResult:
    cells: Tuple[Cell, ...]
    classes: Tuple[frozenset, ...]
    record: FoldRecord
    original: Tuple[Cell, ...]


def _quotient(strip, pairs, pivot, rule, radix) -> FoldResult:
    uf = UnionFind(range(len(strip)))
    for a, b in pairs:
        uf.union(a, b)
    classes = sorted(uf.classes(), key=min)
    cells = []
    for c in classes:
        idx = sorted(c)
        acc = strip[idx[0]]
        for k in idx[1:]:
            acc = combine_cells(acc, strip[k], rule, radix)
        cells.append(acc)
    return FoldResult(
        tuple(cells), tuple(classes), FoldRecord(pivot, tuple(pairs)), strip
    )


def fold_strip(
    strip, pivot: int, rule: Combine = Combine.PORTAL_MERGE, radix: int = 9
) -> FoldResult:
    """Fold at pivot: the left half reverses and overlays the right half."""
    strip = tuple(strip)
    if not 0 <= pivot < len(strip):
        raise ValueError("pivot out of range")
    pairs, i, j = [], pivot - 1, pivot + 1
    while i >= 0 and j < len(strip):
        pairs.append((i, j))
        i, j = i - 1, j + 1
    return _quotient(strip, pairs, pivot, rule, radix)


def glue_cells(
    strip, i: int, rule: Combine = Combine.DIGITAL_SUM, radix: int = 9
) -> FoldResult:
    """A crease: identify adjacent cells i and i+1."""
    strip = tuple(strip)
    if not 0 <= i < len(strip) - 1:
        raise ValueError("index out of range")
    return _quotient(strip, [(i, i + 1)], i, rule, radix)


def fold_reduce(values, rule: Combine = Combine.DIGITAL_SUM, radix: int = 9) -> int:
    cells = tuple(make_cell(v) for v in values)
    while len(cells) > 1:
        cells = glue_cells(cells, 0, rule, radix).cells
    return cells[0].value


@dataclass(frozen=True)
class Pred:
    kind: str  # len_eq | value_eq | value_neq | cell_eq | is_portal
    a: int = 0
    b: int = 0


def eval_pred(cells, p: Pred) -> bool:
    if p.kind == "len_eq":
        return len(cells) == p.a
    if p.kind == "value_eq":
        return cells[p.a].value == p.b
    if p.kind == "value_neq":
        return cells[p.a].value != p.b
    if p.kind == "cell_eq":
        return cells[p.a].value == cells[p.b].value
    if p.kind == "is_portal":
        return cells[p.a].portal
    raise ValueError(p.kind)


@dataclass(frozen=True)
class Instr:
    """NOTE: third positional slot is `rule`; SLIDE deltas must use k=."""

    op: str  # FOLD | GLUE | READ | BRANCH | SLIDE | WHILE
    arg: int = 0
    rule: Combine = Combine.PORTAL_MERGE
    pred: Optional[Pred] = None
    then_prog: Tuple["Instr", ...] = ()
    else_prog: Tuple["Instr", ...] = ()
    k: int = 0  # SLIDE: level-delta (keyword only in practice)
    body: Tuple["Instr", ...] = ()  # WHILE: loop body


def run_program(values, program, radix: int = 9, max_steps: int = 10_000_000):
    """Folding VM with a step budget (runaway-loop protection)."""
    out: List[int] = []
    history: List[Tuple[Tuple[int, ...], FoldRecord]] = []
    budget = [max_steps]

    def tick():
        budget[0] -= 1
        if budget[0] < 0:
            raise RuntimeError("step limit exceeded (runaway loop?)")

    def exec_prog(cells, prog):
        for ins in prog:
            tick()
            if ins.op == "READ":
                out.append(cells[ins.arg].value)
            elif ins.op == "BRANCH":
                cells = exec_prog(
                    cells,
                    ins.then_prog if eval_pred(cells, ins.pred) else ins.else_prog,
                )
            elif ins.op == "SLIDE":
                lst = list(cells)
                v = lst[ins.arg].value + ins.k * radix
                lst[ins.arg] = Cell(max(1, v), lst[ins.arg].members)
                cells = tuple(lst)
            elif ins.op == "WHILE":
                while eval_pred(cells, ins.pred):
                    cells = exec_prog(cells, ins.body)
            else:
                res = (
                    fold_strip(cells, ins.arg, ins.rule, radix)
                    if ins.op == "FOLD"
                    else glue_cells(cells, ins.arg, ins.rule, radix)
                )
                history.append((tuple(c.value for c in cells), res.record))
                cells = res.cells
        return cells

    cells = exec_prog(tuple(make_cell(v) for v in values), tuple(program))
    return cells, out, history


def fold_bags(bags, pivot: int):
    bags = list(bags)
    left = list(reversed(bags[:pivot]))
    right = bags[pivot + 1 :]
    n = min(len(left), len(right))
    return tuple([left[i] | right[i] for i in range(n)] + right[n:] + left[n:])


def find_fold_sequence(values, target, max_folds: int = 2):
    """Origami-analogue solver: fold program forcing target values into one cell."""
    target = frozenset(target)
    start = tuple(frozenset({v}) for v in values)
    dq = deque([(start, ())])
    seen = {start}
    while dq:
        bags, prog = dq.popleft()
        if len(prog) == max_folds:
            continue
        for pivot in range(len(bags)):
            nb = fold_bags(bags, pivot)
            if any(target <= b for b in nb):
                return prog + (pivot,)
            if nb not in seen:
                seen.add(nb)
                dq.append((nb, prog + (pivot,)))
    return None


@dataclass(frozen=True)
class FoldOp:
    kind: str  # ADVANCE | FLIP_ORIENTATION | C_STEP
    target: Optional[CPhase] = None


STATE_SCHEDULE = {
    "F": (FoldOp("C_STEP", CPhase.DOWN), FoldOp("ADVANCE")),  # F-E
    "G": (FoldOp("FLIP_ORIENTATION"), FoldOp("ADVANCE")),  # DISCONTINUE
    "E": (FoldOp("C_STEP", CPhase.BALANCED), FoldOp("ADVANCE")),  # E-F
    "D": (FoldOp("C_STEP", CPhase.UP), FoldOp("ADVANCE")),  # FLIP
    "C": (FoldOp("FLIP_ORIENTATION"), FoldOp("ADVANCE")),  # C-B
    "B": (FoldOp("C_STEP", CPhase.BALANCED), FoldOp("ADVANCE")),  # B-C
    "A": (FoldOp("ADVANCE"),),  # RESTART/A-F
}


@dataclass
class TriangleFoldSimulator:
    letter: str = "F"
    ab: AB = AB.OUTSIDE
    c: CPhase = CPhase.BALANCED

    def apply(self, op: FoldOp, sm: TriangleStateMachine) -> None:
        if op.kind == "ADVANCE":
            self.letter = sm.next_letter(self.letter)
        elif op.kind == "FLIP_ORIENTATION":
            self.ab = AB.INSIDE if self.ab is AB.OUTSIDE else AB.OUTSIDE
        elif op.kind == "C_STEP":
            self.c = op.target


def run_state_schedule():
    """Re-derive the F->G->E->D->C->B->A loop purely from fold ops."""
    sm = TriangleStateMachine()
    sim = TriangleFoldSimulator()
    visited = []
    for _ in range(7):
        visited.append((sim.letter, sim.ab, sim.c))
        for op in STATE_SCHEDULE[sim.letter]:
            sim.apply(op, sm)
    return visited, sim


@dataclass(frozen=True)
class LatticeFoldResult:
    classes: Tuple[frozenset, ...]
    crease: Tuple[Tuple[int, int], ...]


def fold_lattice(points) -> LatticeFoldResult:
    """Fold a point set across the diagonal: (x,y) ~ (y,x); crease = x==y portals."""
    pts = list(dict.fromkeys(points))
    present = set(pts)
    uf = UnionFind(pts)
    for p in pts:
        q = (p[1], p[0])
        if q in present:
            uf.union(p, q)
    return LatticeFoldResult(
        tuple(sorted(uf.classes(), key=lambda c: min(c))),
        tuple(p for p in pts if p[0] == p[1]),
    )


def _run_self_tests():
    letters = "GFEABCD"
    S = [LETTER_TO_ROOT[l] for l in letters]  # (6,6,7,3,5,8,9)

    # 1) Base fold reproduces the fold graph; the tip gluing IS the portal.
    res = fold_strip([make_cell(v) for v in S], pivot=3)
    assert frozenset({0, 6}) in res.classes  # G ~ D
    assert frozenset({1, 5}) in res.classes  # F ~ C
    assert frozenset({2, 4}) in res.classes  # E ~ B
    produced = {(letters[i], letters[j]) for i, j in res.record.pairs}
    assert produced == {("E", "B"), ("F", "C"), ("G", "D")}
    order = sorted(res.classes, key=min)
    tip = res.cells[order.index(frozenset({0, 6}))]
    assert tip.value == 6 and tip.portal

    # 2) Folding is arithmetic.
    assert fold_reduce((3, 5, 8), Combine.DIGITAL_SUM) == digital_root(3 + 5 + 8)
    assert fold_reduce((4, 8), Combine.DIGITAL_PRODUCT) == digital_root(4 * 8)

    # 3) Solver: one fold identifies 6 and 9.
    assert find_fold_sequence(S, (6, 9), max_folds=1) == (3,)

    # 4) Branching: portal-detected branch vs value-equality branch.
    _, out, _ = run_program(
        S,
        [
            Instr("FOLD", 3),
            Instr(
                "BRANCH",
                pred=Pred("is_portal", 0),
                then_prog=(Instr("READ", 0),),
                else_prog=(Instr("READ", 2),),
            ),
        ],
    )
    assert out == [6]
    _, out2, _ = run_program(
        S,
        [
            Instr(
                "BRANCH",
                pred=Pred("value_eq", 0, 7),
                then_prog=(Instr("READ", 2),),
                else_prog=(Instr("READ", 1),),
            ),
        ],
    )
    assert out2 == [6]

    # 5) Unbounded strips: cells may carry level-encoded values.
    _, out3, _ = run_program([10, 17], [Instr("GLUE", 0), Instr("READ", 0)])
    assert out3 == [digital_root(27)]

    # 6) SLIDE (k= keyword!) + WHILE give unbounded level arithmetic.
    _, out4, _ = run_program(
        [3],
        [
            Instr(
                "WHILE", pred=Pred("value_neq", 0, 30), body=(Instr("SLIDE", 0, k=1),)
            ),
            Instr("READ", 0),
        ],
        max_steps=100_000,
    )
    assert out4 == [30]

    # 7) The state schedule re-derives the whole state table and closes.
    visited, sim = run_state_schedule()
    sm = TriangleStateMachine()
    assert visited == [(L, sm.state(L).ab, sm.state(L).c) for L in "FGEDCBA"]
    assert (sim.letter, sim.ab, sim.c) == ("F", AB.OUTSIDE, CPhase.BALANCED)

    # 8) 2D fold: crease = diagonal portals; mirror gluing = the portal pair.
    lf = fold_lattice([(x, y) for x in range(1, 10) for y in range(1, 10)])
    assert len(lf.crease) == 9 and len(lf.classes) == 45
    assert frozenset({(6, 9), (9, 6)}) in lf.classes
    from jacobs_lab.structure.Level_tree import RecursiveLattice, build_level_tree, flatten

    lat = RecursiveLattice(radix=9, x_multiplier=2)
    tree = build_level_tree(lat, 1, 1, 2)
    pts = [(n.x_root, n.y_root) for n in flatten(tree)]
    lf2 = fold_lattice(pts)
    assert set(lf2.crease) == {(n.x_root, n.y_root) for n in flatten(tree) if n.portal}
    mirror = next(c for c in lf.classes if c == frozenset({(6, 9), (9, 6)}))
    assert {v for p in mirror for v in p} == set(PORTAL_LETTERS["G"])
    print("All folding-computation self-tests passed.")


# ----------------------------------------------------------------------
# Trace extension
# ----------------------------------------------------------------------
@dataclass(frozen=True)
class TraceStep:
    index: int
    path: str
    op: str
    detail: str
    before: Tuple[Cell, ...]
    after: Tuple[Cell, ...]
    outputs: Tuple[int, ...]
    branch_taken: Optional[bool] = None
    record: Optional[FoldRecord] = None
    changed_cells: Tuple[int, ...] = ()


def _pred_repr(p: Optional[Pred]) -> str:
    if p is None:
        return "?"
    if p.kind == "len_eq":
        return f"len(cells) == {p.a}"
    if p.kind == "value_eq":
        return f"cell[{p.a}].value == {p.b}"
    if p.kind == "value_neq":
        return f"cell[{p.a}].value != {p.b}"
    if p.kind == "cell_eq":
        return f"cell[{p.a}].value == cell[{p.b}].value"
    if p.kind == "is_portal":
        return f"cell[{p.a}].portal"
    return p.kind


def run_program_traced(values, program, radix: int = 9, max_steps: int = 10_000_000):
    """Exact traced version of run_program().

    Returns:
        cells, out, history, trace

    The first three values match run_program(); the fourth is a list of
    TraceStep objects describing each VM step.
    """
    out: List[int] = []
    history: List[Tuple[Tuple[int, ...], FoldRecord]] = []
    trace: List[TraceStep] = []
    budget = [max_steps]

    def tick():
        budget[0] -= 1
        if budget[0] < 0:
            raise RuntimeError("step limit exceeded (runaway loop?)")

    def snap(cells):
        return tuple(Cell(c.value, c.members) for c in cells)

    def add_step(
        path,
        ins,
        before,
        after,
        detail="",
        branch_taken=None,
        record=None,
        changed=(),
    ):
        trace.append(
            TraceStep(
                index=len(trace),
                path=path,
                op=ins.op if ins is not None else "INIT",
                detail=detail,
                before=before,
                after=after,
                outputs=tuple(out),
                branch_taken=branch_taken,
                record=record,
                changed_cells=changed,
            )
        )

    initial = tuple(make_cell(v) for v in values)
    add_step("init", None, initial, initial, f"initial strip: {list(values)}")

    def exec_prog(cells, prog, path):
        for i, ins in enumerate(prog):
            tick()
            p = f"{path}[{i}]" if path else f"[{i}]"
            before = snap(cells)

            if ins.op == "READ":
                val = cells[ins.arg].value
                out.append(val)
                add_step(
                    p,
                    ins,
                    before,
                    snap(cells),
                    f"READ cell {ins.arg} -> {val}",
                )

            elif ins.op == "BRANCH":
                cond = eval_pred(cells, ins.pred)
                add_step(
                    p,
                    ins,
                    before,
                    snap(cells),
                    f"BRANCH {_pred_repr(ins.pred)} -> {'then' if cond else 'else'}",
                    branch_taken=cond,
                )
                cells = exec_prog(
                    cells,
                    ins.then_prog if cond else ins.else_prog,
                    f"{p}.{'then' if cond else 'else'}",
                )

            elif ins.op == "SLIDE":
                old = cells[ins.arg].value
                new = max(1, old + ins.k * radix)
                lst = list(cells)
                lst[ins.arg] = Cell(new, lst[ins.arg].members)
                cells = tuple(lst)
                add_step(
                    p,
                    ins,
                    before,
                    snap(cells),
                    f"SLIDE cell {ins.arg} by k={ins.k}: {old} -> {new}",
                    changed=(ins.arg,),
                )

            elif ins.op == "WHILE":
                add_step(
                    p,
                    ins,
                    before,
                    snap(cells),
                    f"WHILE {_pred_repr(ins.pred)} enter",
                )

                check = 0
                while True:
                    tick()
                    cond = eval_pred(cells, ins.pred)
                    check_snap = snap(cells)
                    add_step(
                        f"{p}.check[{check}]",
                        ins,
                        check_snap,
                        check_snap,
                        f"WHILE check {check}: {_pred_repr(ins.pred)} = {cond}",
                        branch_taken=cond,
                    )
                    if not cond:
                        break
                    cells = exec_prog(cells, ins.body, f"{p}.body[{check}]")
                    check += 1

                add_step(
                    f"{p}.exit",
                    ins,
                    snap(cells),
                    snap(cells),
                    f"WHILE exited after {check} iteration(s)",
                )

            else:
                res = (
                    fold_strip(cells, ins.arg, ins.rule, radix)
                    if ins.op == "FOLD"
                    else glue_cells(cells, ins.arg, ins.rule, radix)
                )
                history.append((tuple(c.value for c in before), res.record))
                cells = res.cells
                after = snap(cells)

                changed = tuple(
                    idx for idx, c in enumerate(after) if len(c.members) > 1 or c.portal
                )

                if ins.op == "FOLD":
                    detail = f"FOLD pivot={ins.arg} rule={ins.rule.value}"
                else:
                    detail = f"GLUE index={ins.arg} rule={ins.rule.value}"

                add_step(
                    p,
                    ins,
                    before,
                    after,
                    detail,
                    record=res.record,
                    changed=changed,
                )

        return cells

    cells = exec_prog(initial, tuple(program), "")
    return cells, out, history, trace


if __name__ == "__main__":
    _run_self_tests()
    visited, _ = run_state_schedule()
    print("\nSchedule re-derivation:")
    for letter, ab, c in visited:
        print(f"  {letter}: {ab.value}/{c.value}")
