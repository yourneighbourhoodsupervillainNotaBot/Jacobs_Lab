from __future__ import annotations

from typing import Callable, Dict, List, Sequence, Tuple

try:  # module may be named folding_computation.py or folding_computations.py
    from jacobs_lab.computation.folding_computations import Combine, Instr, Pred, run_program
except ModuleNotFoundError:  # pragma: no cover
    from jacobs_lab.computation.folding_computations import Combine, Instr, Pred, run_program

from jacobs_lab.core.general_recursive_mapper import RecursiveMapper, digital_root

MAPPER = RecursiveMapper(9, 2)
enc = MAPPER.encode_num

ROOT_DOMAIN = [(3, 5), (6, 9), (8, 7)]  # pure-root inputs
LEVEL_DOMAIN = [
    (enc(0, 3), enc(0, 5)),
    (enc(1, 6), enc(0, 9)),
    (enc(2, 8), enc(0, 7)),
]  # level-carrying inputs


def induced_value(program: Sequence[Instr], x: Tuple[int, ...]) -> int:
    _, out, _ = run_program(list(x), list(program) + [Instr("READ", 0)])
    return out[0]


def probe_pure_folds(domain) -> Dict[Tuple[int, ...], Tuple[Instr, ...]]:
    """Enumerate short fold-only programs; return {function table: program}."""
    base = [
        Instr("GLUE", 0, r)
        for r in (
            Combine.DIGITAL_SUM,
            Combine.DIGITAL_PRODUCT,
            Combine.KEEP_LEFT,
            Combine.KEEP_RIGHT,
        )
    ] + [
        Instr("FOLD", p, r)
        for p in (0, 1)
        for r in (Combine.DIGITAL_SUM, Combine.KEEP_LEFT)
    ]

    # FIX: every program is a tuple of Instr (1-op and 2-op sequences).
    programs = [(p,) for p in base] + [(a, b) for a in base for b in base]

    found: Dict[Tuple[int, ...], Tuple[Instr, ...]] = {}
    for prog in programs:
        try:
            table = tuple(induced_value(prog, x) for x in domain)
        except ValueError:
            # GLUE shrinks the strip; some 2-op sequences then address an
            # index that no longer exists. The VM is strict by design, so
            # such sequences are simply not valid programs on this domain.
            continue
        found.setdefault(table, prog)
    return found


def lookup_program(
    domain: Sequence[Tuple[int, ...]],
    f: Callable[[Tuple[int, ...]], int],
    n_in: int = 2,
) -> Tuple[Tuple[Instr, ...], List[int]]:
    """Branch-tree program computing ANY finite function f on the domain.
    Returns the program AND the exact constants list it expects."""
    constants = sorted({f(x) for x in domain})
    pairs = [(x, f(x)) for x in domain]

    def build(pairs, cell) -> Tuple[Instr, ...]:
        outs = {y for _, y in pairs}
        if len(outs) == 1:
            v = next(iter(outs))
            return (Instr("READ", n_in + constants.index(v)),)
        keys = sorted({x[cell] for x, _ in pairs})
        if len(keys) == 1:
            return build(pairs, cell + 1)
        first = keys[0]
        then = build([p for p in pairs if p[0][cell] == first], cell + 1)
        else_ = build([p for p in pairs if p[0][cell] != first], cell)
        return (
            Instr(
                "BRANCH",
                pred=Pred("value_eq", cell, first),
                then_prog=then,
                else_prog=else_,
            ),
        )

    return build(pairs, 0), constants


def run_with_constants(x, constants, program) -> int:
    _, out, _ = run_program(list(x) + list(constants), program)
    return out[0]


def _run_self_tests():
    # 1) Pure folds compute exactly the digital-root semiring + projections.
    found = probe_pure_folds(ROOT_DOMAIN)
    a, b = zip(*ROOT_DOMAIN)
    t_p0, t_p1 = tuple(a), tuple(b)
    t_sum = tuple(digital_root(x + y) for x, y in ROOT_DOMAIN)
    t_prod = tuple(digital_root(x * y) for x, y in ROOT_DOMAIN)
    t_max = tuple(max(x, y) for x, y in ROOT_DOMAIN)
    for t in (t_p0, t_p1, t_sum, t_prod):
        assert t in found, f"semiring function missing: {t}"
    assert t_max not in found  # max is NOT a fold-computable function
    assert t_sum != t_prod  # the two combining laws are distinct

    # 2) Branching + constants lifts the class to ALL finite functions.
    f_level = lambda x: MAPPER.decode_num(x[0]).level + 1  # non-semiring
    f_max = lambda x: max(x)
    for f in (f_level, f_max):
        prog, constants = lookup_program(LEVEL_DOMAIN, f)  # FIX: paired constants
        for x in LEVEL_DOMAIN:
            assert run_with_constants(x, constants, prog) == f(x)

    # 3) Level extraction is absent from the pure-fold class on level inputs.
    found_lvl = probe_pure_folds(LEVEL_DOMAIN)
    t_level = tuple(MAPPER.decode_num(x).level + 1 for x, _ in LEVEL_DOMAIN)
    assert t_level not in found_lvl
    assert tuple(x for x, _ in LEVEL_DOMAIN) in found_lvl  # projections work
    print("All universality-probe self-tests passed.")


if __name__ == "__main__":
    _run_self_tests()
    found = probe_pure_folds(ROOT_DOMAIN)
    print(f"\nPure-fold programs explored -> {len(found)} distinct functions:")
    names = {
        tuple(a for a, _ in ROOT_DOMAIN): "proj-left",
        tuple(b for _, b in ROOT_DOMAIN): "proj-right",
        tuple(digital_root(x + y) for x, y in ROOT_DOMAIN): "digital-sum",
        tuple(digital_root(x * y) for x, y in ROOT_DOMAIN): "digital-product",
    }
    for table in found:
        print(f"  {table}  <- {names.get(table, 'other')}")
    print(
        "max/level absent from the pure-fold class; "
        "branching+constants realizes them (lookup-universal)."
    )
