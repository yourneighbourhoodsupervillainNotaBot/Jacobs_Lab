from __future__ import annotations

from typing import Tuple

from lab_trace import TraceBuilder


# ----------------------------------------------------------------------
# pathfinding
# ----------------------------------------------------------------------
def trace_pathfinding(start: Tuple[int, int] = (1, 1), goal: Tuple[int, int] = (8, 7)):
    from pathfinding_lab import LAT, astar, geodesic

    initial = {
        "start": list(start),
        "goal": list(goal),
    }

    b = TraceBuilder(
        source="pathfinding",
        title=f"Pathfinding {start} -> {goal}",
        initial=initial,
    )

    b.event("init", path="start", after=initial)

    gd, gpath = geodesic(LAT, start, goal)

    if gpath is None:
        b.event("no_path", after=initial)
        return b.build(final={"reachable": False})

    for i in range(1, len(gpath)):
        before = {"pos": list(gpath[i - 1])}
        after = {"pos": list(gpath[i])}

        move = "RIGHT" if gpath[i][0] != gpath[i - 1][0] else "UP"

        b.event(
            "move",
            path=f"[{i}]",
            before=before,
            after=after,
            move=move,
        )

    ad, expansions, apath = astar(LAT, start, goal)

    b.event(
        "astar_summary",
        after={
            "distance": ad,
            "expansions": expansions,
            "path_len": len(apath),
        },
    )

    return b.build(
        final={
            "pos": list(goal),
            "geodesic": gd,
            "astar_distance": ad,
            "expansions": expansions,
            "reachable": True,
        }
    )


# ----------------------------------------------------------------------
# three-body lab
# ----------------------------------------------------------------------
def trace_three_body(periods: int = 2, sample_every: int = 20):
    from three_body_lab import (
        FIG_V,
        FIG_X,
        PERIOD,
        energy,
        integrate,
        shape_symbol,
        symbol_complexity,
    )

    dt = 0.005
    spp = int(round(PERIOD / dt))
    steps = periods * spp

    traj, pos, vel = integrate([p for p in FIG_X], [v for v in FIG_V], dt, steps)

    e0 = energy(FIG_X, FIG_V)
    e1 = energy(pos, vel)

    b = TraceBuilder(
        source="three_body",
        title=f"Three-body figure-eight x{periods}",
        initial={"energy": e0},
        meta={"dt": dt, "steps": steps},
    )

    b.event(
        "init",
        after={
            "energy": e0,
            "positions": [list(p) for p in FIG_X],
        },
    )

    stream = []

    for k in range(0, steps + 1, sample_every):
        positions = [list(p) for p in traj[k]]
        sym = shape_symbol(traj[k])
        stream.append(sym)

        b.event(
            "symbol",
            path=f"[{k}]",
            before={"step": max(0, k - sample_every)},
            after={
                "step": k,
                "symbol": sym,
                "positions": positions,
            },
            symbol=sym,
        )

    ratio, p = symbol_complexity(stream)

    b.event(
        "complexity",
        after={
            "ratio": ratio,
            "period": p,
        },
    )

    drift = abs(e1 - e0) / abs(e0)

    b.event(
        "energy",
        after={
            "initial": e0,
            "final": e1,
            "drift": drift,
        },
    )

    return b.build(
        final={
            "symbol_ratio": ratio,
            "period": p,
            "energy_drift": drift,
        }
    )


# ----------------------------------------------------------------------
# fold codec
# ----------------------------------------------------------------------
def trace_fold_codec(kind: str = "palindrome"):
    import random

    from fold_codec import codec_bits, decode, encode, lifted_advance, raw_bits

    rnd = random.Random(11)

    if kind == "palindrome":
        L = [rnd.randint(1, 63) for _ in range(8)]
        strip = L + [7] + L[::-1]

    elif kind == "orb_mirror":
        W = [rnd.randint(1, 500) for _ in range(8)]
        strip = W + [5] + [lifted_advance(v, 1) for v in W[::-1]]

    else:
        strip = [rnd.randint(1, 63) for _ in range(17)]

    rec = encode(strip)

    b = TraceBuilder(
        source="fold_codec",
        title=f"Fold codec trace ({kind})",
        initial={"strip": strip},
    )

    b.event(
        "init",
        after={
            "strip": strip,
            "raw_bits": raw_bits(strip),
        },
    )

    if rec["mode"] == "fold":
        for i, lvl in enumerate(rec["levels"]):
            b.event(
                "encode_level",
                path=f"levels[{i}]",
                after={
                    "n": lvl["n"],
                    "p": lvl["p"],
                    "items_count": len(lvl["items"]),
                },
                items=lvl["items"],
            )

        b.event("top_residual", after={"top": rec["top"]})

    else:
        b.event("raw_fallback", after={"values": rec["values"]})

    decoded = decode(rec)
    ok = decoded == list(strip)

    cb = codec_bits(rec)
    rb = raw_bits(strip)

    b.event(
        "roundtrip",
        after={
            "ok": ok,
            "codec_bits": cb,
            "raw_bits": rb,
        },
    )

    return b.build(
        final={
            "ok": ok,
            "bits": cb,
            "raw": rb,
            "mode": rec["mode"],
        }
    )


# ----------------------------------------------------------------------
# fold complexity
# ----------------------------------------------------------------------
def trace_fold_complexity():
    from fold_complexity import _corpora, complexity_split, fold_complexity

    b = TraceBuilder(
        source="fold_complexity",
        title="Fold complexity corpora",
        initial={},
    )

    summary = {}

    for name, data in _corpora().items():
        fc = fold_complexity(data)
        split = complexity_split(data)

        summary[name] = fc

        b.event(
            "corpus",
            path=name,
            after={
                "fc": fc,
                "total": split["total"],
                "predictable": split["predictable"],
                "table": split["table"],
            },
            corpus=name,
            length=len(data),
        )

    return b.build(final=summary)


# ----------------------------------------------------------------------
# prime machinery
# ----------------------------------------------------------------------
def trace_prime_machinery(limit: int = 30, vm_limit: int = 10):
    from prime_machinery import (
        folding_mod3,
        is_admissible,
        lucas_certificate,
        sieve,
    )

    primes = sieve(limit)

    b = TraceBuilder(
        source="prime_machinery",
        title=f"Prime machinery to {limit}",
        initial={"limit": limit},
    )

    b.event("sieve", after={"primes": primes})

    for n in range(2, limit + 1):
        admissible = is_admissible(n)

        b.event(
            "filter",
            path=str(n),
            before={"n": n},
            after={"n": n, "admissible": admissible},
            admissible=admissible,
        )

    for p in primes[:6]:
        w = lucas_certificate(p)

        b.event(
            "certificate",
            path=str(p),
            before={"p": p},
            after={"p": p, "witness": w},
            witness=w,
        )

    for n in range(vm_limit + 1):
        r = folding_mod3(n)

        b.event(
            "vm_mod3",
            path=str(n),
            before={"n": n},
            after={"n": n, "mod3": r},
            mod3=r,
        )

    return b.build(final={"primes": primes})


# ----------------------------------------------------------------------
# universality probe
# ----------------------------------------------------------------------
def trace_universality_probe(max_functions: int = 12):
    from universality_probe import (
        LEVEL_DOMAIN,
        ROOT_DOMAIN,
        lookup_program,
        probe_pure_folds,
        run_with_constants,
    )

    b = TraceBuilder(
        source="universality_probe",
        title="Universality probe",
        initial={"root_domain": [list(x) for x in ROOT_DOMAIN]},
    )

    found = probe_pure_folds(ROOT_DOMAIN)

    b.event("probe_pure_folds", after={"distinct_functions": len(found)})

    for i, (table, prog) in enumerate(list(found.items())[:max_functions]):
        b.event(
            "pure_function",
            path=f"[{i}]",
            after={
                "table": list(table),
                "program_len": len(prog),
            },
            table=list(table),
            program_len=len(prog),
        )

    def f_max(x):
        return max(x)

    prog, constants = lookup_program(LEVEL_DOMAIN, f_max)

    b.event(
        "lookup_program",
        after={
            "constants": constants,
            "program_len": len(prog),
        },
    )

    for x in LEVEL_DOMAIN:
        y = run_with_constants(x, constants, prog)

        b.event(
            "lookup_eval",
            before={"x": list(x)},
            after={"x": list(x), "y": y},
            expected=max(x),
        )

    return b.build(final={"pure_functions": len(found)})


# ----------------------------------------------------------------------
# self-tests
# ----------------------------------------------------------------------
def _run_self_tests():
    tr = trace_pathfinding()
    assert any(e.kind == "move" for e in tr.events)

    tr = trace_three_body(periods=1, sample_every=200)
    assert any(e.kind == "symbol" for e in tr.events)

    tr = trace_fold_codec("palindrome")
    assert tr.final.get("ok") is True

    tr = trace_fold_complexity()
    assert any(e.kind == "corpus" for e in tr.events)

    tr = trace_prime_machinery(limit=12, vm_limit=4)
    assert any(e.kind == "sieve" for e in tr.events)

    tr = trace_universality_probe(max_functions=3)
    assert any(e.kind == "pure_function" for e in tr.events)

    print("All lab-adapters-extended self-tests passed.")


if __name__ == "__main__":
    _run_self_tests()
