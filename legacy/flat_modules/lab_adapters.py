from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

from lab_compat import import_folding
from lab_trace import TraceBuilder


# ----------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------
def _cell_dict(cell: Any) -> Dict[str, Any]:
    return {
        "value": int(cell.value),
        "members": sorted(cell.members),
        "portal": bool(cell.portal),
    }


def _pred_repr(p: Any) -> str:
    if p is None:
        return "?"

    kind = getattr(p, "kind", "?")
    a = getattr(p, "a", 0)
    b = getattr(p, "b", 0)

    if kind == "len_eq":
        return f"len(cells) == {a}"
    if kind == "value_eq":
        return f"cell[{a}].value == {b}"
    if kind == "value_neq":
        return f"cell[{a}].value != {b}"
    if kind == "cell_eq":
        return f"cell[{a}].value == cell[{b}].value"
    if kind == "is_portal":
        return f"cell[{a}].portal"

    return kind


# ----------------------------------------------------------------------
# triangle state machine trace
# ----------------------------------------------------------------------
def trace_triangle_walk(loops: int = 2, start: str = "F"):
    from legacy.flat_modules.triangle_state_machine import TriangleStateMachine

    sm = TriangleStateMachine()
    letter = start
    state = sm.state(letter)

    def state_dict(letter_name: str) -> Dict[str, Any]:
        s = sm.state(letter_name)
        return {
            "letter": s.letter,
            "root": s.root,
            "mode": s.mode.value,
            "ab": s.ab.value,
            "c": s.c.value,
        }

    initial = state_dict(letter)

    b = TraceBuilder(
        source="triangle_state_machine",
        title=f"Triangle state walk x{loops}",
        initial=initial,
        meta={"start": start, "loops": loops},
    )

    b.event("init", path="start", after=initial)

    total = loops * len(sm.transitions)

    for i in range(total):
        before = state_dict(letter)
        t = sm.transition(letter)
        after = state_dict(t.dst)
        topo_label = sm.classify_transition(t)

        b.event(
            "transition",
            path=f"[{i}]",
            before=before,
            after=after,
            action=t.action,
            topo=topo_label,
            note=t.note,
        )

        letter = t.dst

    return b.build()


# ----------------------------------------------------------------------
# test-walk trace
# ----------------------------------------------------------------------
def trace_test_walk(
    results: Optional[List[Any]] = None,
    run_real: bool = False,
    inject_failure: bool = False,
):
    from legacy.flat_modules.recursive_lattice import RecursiveLattice
    from legacy.flat_modules.test_harness import TestResult
    from legacy.flat_modules.test_walk_engine import build_test_tree, taken_path

    if results is None:
        if run_real:
            from legacy.flat_modules.test_harness import run_all_tests

            results = run_all_tests()
        else:
            names = [
                "core_topology",
                "recursive_mapper",
                "lattice",
                "state_machine",
                "fold_vm",
                "universality",
                "pathfinding",
                "complexity",
            ]

            results = [TestResult(n, True, 0.001, None) for n in names]

            if inject_failure:
                results[3] = TestResult(
                    names[3],
                    False,
                    0.002,
                    "synthetic failure for trace demo",
                )

    lattice = RecursiveLattice(radix=9, x_multiplier=2)
    root, result_by_depth = build_test_tree(
        results,
        lattice,
        start_x=1,
        start_y=1,
    )

    path = taken_path(root)

    initial = {
        "x_root": root.x_root,
        "y_root": root.y_root,
        "depth": root.depth,
        "portal": root.portal,
    }

    b = TraceBuilder(
        source="test_walk",
        title="Test suite lattice walk",
        initial=initial,
        meta={"n_tests": len(results), "real": bool(run_real)},
    )

    b.event("init", path="root", after=initial)

    final_state = initial

    for i, node in enumerate(path[1:], start=1):
        parent = path[i - 1]
        r = result_by_depth.get(i)

        preview = parent.children[1] if len(parent.children) > 1 else None

        before = {
            "x_root": parent.x_root,
            "y_root": parent.y_root,
            "depth": parent.depth,
            "portal": parent.portal,
        }

        after = {
            "x_root": node.x_root,
            "y_root": node.y_root,
            "depth": node.depth,
            "portal": node.portal,
        }

        preview_state = None
        if preview is not None:
            preview_state = {
                "x_root": preview.x_root,
                "y_root": preview.y_root,
                "move": preview.move,
                "portal": preview.portal,
            }

        b.event(
            "test_node",
            path=f"[{i}]",
            before=before,
            after=after,
            module=r.module if r is not None else None,
            passed=bool(r.passed) if r is not None else None,
            duration=r.duration if r is not None else None,
            error=r.error if r is not None else None,
            move=node.move,
            portal=node.portal,
            preview=preview_state,
        )

        final_state = after

    return b.build(final=final_state)


# ----------------------------------------------------------------------
# folding VM trace
# ----------------------------------------------------------------------
def trace_fold_program(
    values: Sequence[int],
    program: Sequence[Any],
    title: str = "Folding program",
    radix: int = 9,
    max_steps: int = 100_000,
):
    fc = import_folding()

    out: List[int] = []
    budget = [max_steps]

    def tick():
        budget[0] -= 1
        if budget[0] < 0:
            raise RuntimeError("step limit exceeded (runaway loop?)")

    def cell_state(cells: Tuple[Any, ...]) -> Dict[str, Any]:
        return {
            "cells": [_cell_dict(c) for c in cells],
            "outputs": list(out),
        }

    initial_cells = tuple(fc.make_cell(v) for v in values)
    initial_state = cell_state(initial_cells)

    b = TraceBuilder(
        source="folding_vm",
        title=title,
        initial=initial_state,
        meta={
            "radix": radix,
            "values": list(values),
        },
    )

    b.event("init", path="init", after=initial_state)

    def exec_prog(
        cells: Tuple[Any, ...], prog: Sequence[Any], path: str
    ) -> Tuple[Any, ...]:
        for i, ins in enumerate(prog):
            tick()
            p = f"{path}[{i}]" if path else f"[{i}]"
            before = cell_state(cells)

            if ins.op == "READ":
                val = cells[ins.arg].value
                out.append(val)
                after = cell_state(cells)

                b.event(
                    "read",
                    path=p,
                    before=before,
                    after=after,
                    detail=f"READ cell {ins.arg} -> {val}",
                )

            elif ins.op == "BRANCH":
                cond = fc.eval_pred(cells, ins.pred)

                b.event(
                    "branch",
                    path=p,
                    before=before,
                    after=before,
                    detail=f"BRANCH {_pred_repr(ins.pred)} -> {'then' if cond else 'else'}",
                    branch_taken=cond,
                )

                cells = exec_prog(
                    cells,
                    ins.then_prog if cond else ins.else_prog,
                    f"{p}.{'then' if cond else 'else'}",
                )

            elif ins.op == "SLIDE":
                lst = list(cells)
                old = lst[ins.arg].value
                new = max(1, old + ins.k * radix)
                lst[ins.arg] = fc.Cell(new, lst[ins.arg].members)
                cells = tuple(lst)

                after = cell_state(cells)

                b.event(
                    "slide",
                    path=p,
                    before=before,
                    after=after,
                    detail=f"SLIDE cell {ins.arg} by k={ins.k}: {old} -> {new}",
                    changed=[ins.arg],
                    old=old,
                    new=new,
                )

            elif ins.op == "WHILE":
                b.event(
                    "while_enter",
                    path=p,
                    before=before,
                    after=before,
                    detail=f"WHILE {_pred_repr(ins.pred)}",
                )

                check = 0

                while True:
                    tick()
                    cond = fc.eval_pred(cells, ins.pred)
                    check_state = cell_state(cells)

                    b.event(
                        "while_check",
                        path=f"{p}.check[{check}]",
                        before=check_state,
                        after=check_state,
                        detail=f"WHILE check {check}: {_pred_repr(ins.pred)} = {cond}",
                        branch_taken=cond,
                    )

                    if not cond:
                        break

                    cells = exec_prog(cells, ins.body, f"{p}.body[{check}]")
                    check += 1

                b.event(
                    "while_exit",
                    path=f"{p}.exit",
                    before=cell_state(cells),
                    after=cell_state(cells),
                    detail=f"WHILE exited after {check} iteration(s)",
                    iterations=check,
                )

            else:
                res = (
                    fc.fold_strip(cells, ins.arg, ins.rule, radix)
                    if ins.op == "FOLD"
                    else fc.glue_cells(cells, ins.arg, ins.rule, radix)
                )

                cells = res.cells
                after = cell_state(cells)

                detail = (
                    f"FOLD pivot={ins.arg} rule={getattr(ins.rule, 'value', str(ins.rule))}"
                    if ins.op == "FOLD"
                    else f"GLUE index={ins.arg} rule={getattr(ins.rule, 'value', str(ins.rule))}"
                )

                b.event(
                    ins.op.lower(),
                    path=p,
                    before=before,
                    after=after,
                    detail=detail,
                    pivot=ins.arg,
                    rule=getattr(ins.rule, "value", str(ins.rule)),
                    pairs=[list(pair) for pair in res.record.pairs],
                )

        return cells

    cells = exec_prog(initial_cells, tuple(program), "")
    return b.build(final=cell_state(cells))


def fold_demo_program(name: str) -> Tuple[List[int], Tuple[Any, ...]]:
    fc = import_folding()

    if name == "fold":
        values = [6, 6, 7, 3, 5, 8, 9]
        program = (
            fc.Instr("FOLD", 3),
            fc.Instr(
                "BRANCH",
                pred=fc.Pred("is_portal", 0),
                then_prog=(fc.Instr("READ", 0),),
                else_prog=(fc.Instr("READ", 2),),
            ),
            fc.Instr("SLIDE", 0, k=1),
            fc.Instr("READ", 0),
        )
        return values, program

    if name == "glue":
        values = [3, 5, 8]
        program = (
            fc.Instr("GLUE", 0, fc.Combine.DIGITAL_SUM),
            fc.Instr("GLUE", 0, fc.Combine.DIGITAL_SUM),
            fc.Instr("READ", 0),
        )
        return values, program

    if name == "while":
        values = [3]
        program = (
            fc.Instr(
                "WHILE",
                pred=fc.Pred("value_neq", 0, 30),
                body=(fc.Instr("SLIDE", 0, k=1),),
            ),
            fc.Instr("READ", 0),
        )
        return values, program

    raise ValueError(f"unknown fold demo: {name}")


def trace_fold_demo(name: str = "fold"):
    values, program = fold_demo_program(name)
    return trace_fold_program(values, program, title=f"Folding demo: {name}")


# ----------------------------------------------------------------------
# flexagon trace
# ----------------------------------------------------------------------
def trace_flexagon():
    from flexagon import STRIP, PIVOT, face, flex, fold_packet

    packet = fold_packet()

    def slot_dict(s):
        return {"front": s.front, "back": s.back}

    def packet_state(p):
        return {
            "packet": [slot_dict(s) for s in p],
            "face": list(face(p)),
        }

    initial = packet_state(packet)

    b = TraceBuilder(
        source="flexagon",
        title="Flexagon packet trace",
        initial=initial,
        meta={"strip": STRIP, "pivot": PIVOT},
    )

    b.event("fold_packet", path="fold", after=initial)

    flexed = flex(packet)
    b.event(
        "flex",
        path="flex[0]",
        before=packet_state(packet),
        after=packet_state(flexed),
        face=list(face(flexed)),
    )

    back = flex(flexed)
    b.event(
        "flex_return",
        path="flex[1]",
        before=packet_state(flexed),
        after=packet_state(back),
        face=list(face(back)),
    )

    return b.build(final=packet_state(back))


# ----------------------------------------------------------------------
# category-theory transformation trace
# ----------------------------------------------------------------------
def trace_portal_natural_transformation():
    from natural_transformations import build_portal_natural_isomorphism

    C, D, F, G, eta = build_portal_natural_isomorphism()

    b = TraceBuilder(
        source="category_theory",
        title="Portal natural isomorphism",
        initial={"functor": F.name},
        meta={
            "natural": eta.is_natural(),
            "iso": eta.is_iso(),
        },
    )

    b.event("init", path="eta", after={"functor": F.name})

    for L, comp in eta.components.items():
        a, bb = comp
        b.event(
            "component",
            path=f"eta[{L}]",
            before={"root": a},
            after={"root": bb},
            portal=(a != bb),
        )

    return b.build(
        final={
            "natural": eta.is_natural(),
            "iso": eta.is_iso(),
        }
    )


# ----------------------------------------------------------------------
# self-tests
# ----------------------------------------------------------------------
def _run_self_tests():
    tr = trace_triangle_walk(loops=1)
    assert len(tr.events) >= 8
    assert any(e.kind == "transition" for e in tr.events)

    tr = trace_test_walk(run_real=False, inject_failure=True)
    assert any(e.kind == "test_node" for e in tr.events)
    assert any(e.meta.get("passed") is False for e in tr.events)

    tr = trace_fold_demo("glue")
    assert tr.final["outputs"] == [7]

    tr = trace_flexagon()
    assert any(e.kind == "flex" for e in tr.events)

    print("All lab-adapters self-tests passed.")


if __name__ == "__main__":
    _run_self_tests()
