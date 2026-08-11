from __future__ import annotations

"""
Fold complexity: K_folding(strip) approximated by the fold codec.

Calibration (from universality_probe): the codec's predictors (eq / orb /
portal) are exactly the relations the pure-fold class computes, while the
deferred residuals are the lookup-table part.  complexity_split() therefore
decomposes a strip's code length into "fold-computable" vs "table" bits --
the probe's computational ladder, measured per-input.

FC(strip) = codec_bits / raw_bits in (0, 1]; 1.0 means incompressible.
"""

import random
from typing import Dict, Sequence

from fold_codec import (
    TAG_BITS,
    bits,
    codec_bits,
    encode,
    lifted_advance,
    raw_bits,
)


def fold_complexity_bits(strip: Sequence[int]) -> int:
    return codec_bits(encode(strip))


def fold_complexity(strip: Sequence[int]) -> float:
    if not strip:
        return 0.0
    return fold_complexity_bits(strip) / raw_bits(strip)


def complexity_split(strip: Sequence[int]) -> Dict:
    """Code-length split: predictable (fold-computable) vs table bits."""
    rec = encode(strip)
    raw = raw_bits(strip)
    if rec["mode"] == "raw":
        return {"total": raw, "predictable": 0, "table": raw, "ratio": 1.0}
    pred = table = 0
    for lvl in rec["levels"]:
        for kind, _i, _j, payload in lvl["items"]:
            if kind == "def":
                table += TAG_BITS[kind]
            else:
                pred += TAG_BITS[kind] + (bits(payload) if payload is not None else 0)
    table += raw_bits(rec["top"])
    total = pred + table
    return {"total": total, "predictable": pred, "table": table, "ratio": total / raw}


def _corpora() -> Dict[str, list]:
    rnd = random.Random(7)
    L = [rnd.randint(1, 63) for _ in range(20)]
    pal = L + [7] + L[::-1]
    W = [rnd.randint(1, 500) for _ in range(20)]
    orb_mirror = W + [5] + [lifted_advance(v, 1) for v in W[::-1]]
    lv = [rnd.randint(0, 6) for _ in range(10)]
    R = [9 * l + 3 for l in lv]
    R = R + [3] + R[::-1]
    nested = [0] * 41
    p = 20
    for t in range(10):
        nested[p - 1 - t], nested[p + 1 + t] = R[2 * t], R[2 * t + 1]
    for t in range(10, 20):
        v = rnd.randint(64, 500)
        nested[p - 1 - t] = nested[p + 1 + t] = v
    nested[p] = 7
    rand_ints = [rnd.randint(1, 63) for _ in range(41)]
    return {"pal": pal, "orb_mirror": orb_mirror, "nested": nested, "random": rand_ints}


def _run_self_tests():
    corpora = _corpora()
    fc = {name: fold_complexity(data) for name, data in corpora.items()}
    sp = {name: complexity_split(data) for name, data in corpora.items()}

    # Axiom 1: bounded, and incompressible data hits the ceiling.
    for name, v in fc.items():
        assert 0.0 < v <= 1.0, (name, v)
    assert fc["random"] >= 0.99

    # Axiom 2: structure is simple, and strictly simpler than noise.
    assert fc["pal"] < 0.8
    assert fc["orb_mirror"] < 0.9
    assert fc["nested"] < 0.85
    for name in ("pal", "orb_mirror", "nested"):
        assert fc[name] < fc["random"], name

    # Axiom 3: mirror-symmetry of the measure (exact under v2.2, which
    # stores the cheaper orb endpoint and is therefore reversal-invariant).
    assert fc["pal"] == fold_complexity(corpora["pal"][::-1])
    assert fc["orb_mirror"] == fold_complexity(corpora["orb_mirror"][::-1])

    # Axiom 4: destroying structure never makes it simpler.
    shuffled = list(corpora["pal"])
    random.Random(3).shuffle(shuffled)
    assert fold_complexity(shuffled) >= fc["pal"]

    # Axiom 5: the split is meaningful -- structure is mostly
    # fold-computable; noise is pure table.
    assert sp["pal"]["predictable"] / sp["pal"]["total"] > 0.5
    assert sp["random"]["predictable"] == 0
    print("All fold-complexity self-tests passed.")
    return fc, sp


if __name__ == "__main__":
    fc, sp = _run_self_tests()
    print(f"\n{'corpus':<11} {'FC':>5} {'bits':>5} {'predictable%':>12}")
    for name in ("pal", "orb_mirror", "nested", "random"):
        frac = 100.0 * sp[name]["predictable"] / sp[name]["total"]
        print(f"{name:<11} {fc[name]:>5.2f} {sp[name]['total']:>5} {frac:>11.1f}%")
    print("\nFC = computable upper bound on folding-theory Kolmogorov complexity;")
    print(
        "predictable% = share of bits explained by the probe's fold-computable class."
    )
