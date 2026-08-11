from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

try:
    from folding_computation import Instr, Pred, run_program
except ModuleNotFoundError:  # pragma: no cover
    from folding_computations import Instr, Pred, run_program

RADIX = 9
ROOT = 3  # counters live on root 3; level = counter value


def enc(level: int) -> int:
    return level * RADIX + ROOT


def dec_level(v: int) -> int:
    return (v - ROOT) // RADIX


@dataclass(frozen=True)
class MinskyInstr:
    op: str  # "INC" | "DEC"
    counter: int
    next_state: int
    zero_state: int = -1  # DEC only: state entered when the counter is 0


@dataclass(frozen=True)
class MinskyMachine:
    n_states: int
    halt: int
    program: Dict[int, MinskyInstr]


def compile_minsky(mm: MinskyMachine, n_counters: int) -> Tuple[Instr, ...]:
    """
    Exact simulation of a counter machine by the folding computer.

    Layout: cells 0..n-1 are counters (value = enc(level)), cell n is the
    program counter. INC/DEC are SLIDE +-1 (k= keyword!); zero-test is
    value_eq against enc(0); state changes are SLIDE deltas on the pc;
    the whole machine runs inside one WHILE (pc != halt).

    Two-counter machines are Turing-universal (Minsky 1961); this compiler
    is compositional and step-exact, so the folding computer is universal.
    """
    PC = n_counters

    def goto(k_from: int, k_to: int) -> Tuple[Instr, ...]:
        return (Instr("SLIDE", PC, k=k_to - k_from),)

    def compile_instr(k: int, ins: MinskyInstr) -> Tuple[Instr, ...]:
        if ins.op == "INC":
            return (Instr("SLIDE", ins.counter, k=1),) + goto(k, ins.next_state)
        if ins.op == "DEC":
            return (
                Instr(
                    "BRANCH",
                    pred=Pred("value_eq", ins.counter, enc(0)),
                    then_prog=goto(k, ins.zero_state),
                    else_prog=(Instr("SLIDE", ins.counter, k=-1),)
                    + goto(k, ins.next_state),
                ),
            )
        raise ValueError(ins.op)

    def dispatch(states) -> Tuple[Instr, ...]:
        if not states:
            return ()
        k = states[0]
        if len(states) == 1:
            return compile_instr(k, mm.program[k])
        return (
            Instr(
                "BRANCH",
                pred=Pred("value_eq", PC, enc(k)),
                then_prog=compile_instr(k, mm.program[k]),
                else_prog=dispatch(states[1:]),
            ),
        )

    running = [s for s in range(mm.n_states) if s != mm.halt]
    return (
        Instr(
            "WHILE", pred=Pred("value_neq", PC, enc(mm.halt)), body=dispatch(running)
        ),
    )


def run_minsky(
    mm: MinskyMachine, n_counters: int, counters: Tuple[int, ...], start_state: int = 0
) -> Tuple[int, ...]:
    prog = compile_minsky(mm, n_counters)
    values = [enc(c) for c in counters] + [enc(start_state)]
    cells, _, _ = run_program(values, prog)
    return tuple(dec_level(cells[i].value) for i in range(n_counters))


def _run_self_tests():
    # 1) Addition: transfer c1 into c0.
    # FIX: The machine needs two states in the loop: one to DEC c1, one to INC c0.
    add = MinskyMachine(
        3,
        2,
        {
            0: MinskyInstr(
                "DEC", 1, 1, 2
            ),  # dec c1; if >0 go to 1, if 0 go to 2 (halt)
            1: MinskyInstr("INC", 0, 0),  # inc c0; go back to 0
        },
    )
    assert run_minsky(add, 2, (2, 3)) == (5, 0)
    assert run_minsky(add, 2, (0, 4)) == (4, 0)

    # 2) Zero-test taken: DEC on an empty counter jumps to zero_state.
    z = MinskyMachine(2, 1, {0: MinskyInstr("DEC", 0, 0, 1)})
    assert run_minsky(z, 2, (0, 7)) == (0, 7)

    # 3) Doubling: while c0 > 0: dec c0; inc c1 twice.
    dbl = MinskyMachine(
        4,
        2,
        {
            0: MinskyInstr("DEC", 0, 1, 2),
            1: MinskyInstr("INC", 1, 3),
            3: MinskyInstr("INC", 1, 0),
        },
    )
    assert run_minsky(dbl, 2, (3, 0)) == (0, 6)
    assert run_minsky(dbl, 2, (5, 1)) == (0, 11)

    # 4) Compiled program terminates and produces the right counters.
    prog = compile_minsky(add, 2)
    cells, _, _ = run_program([enc(2), enc(3), enc(0)], prog)
    assert dec_level(cells[0].value) == 5
    print("All turing-universality self-tests passed.")


if __name__ == "__main__":
    _run_self_tests()
    print("\nComputational ladder (now closed):")
    print("  pure folds            == Z/9Z semiring expressions")
    print("  + BRANCH(value_eq)    == all finite functions (lookup-universal)")
    print("  + SLIDE + WHILE       == Turing-universal (Minsky reduction)")
