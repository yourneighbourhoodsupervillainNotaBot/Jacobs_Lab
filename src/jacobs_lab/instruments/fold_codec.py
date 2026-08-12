from __future__ import annotations

import random
from typing import Dict, List, Sequence

from jacobs_lab.core.general_recursive_mapper import RecursiveMapper, RecursiveTopology

TOPO = RecursiveTopology(9, 2)
MAPPER = RecursiveMapper(9, 2)

# orb kinds: o<|k|><f|b><l|r>  = step magnitude, left->right sign, stored side.
TAG_BITS = {
    "eq": 1,
    "def": 2,
    "p69": 3,
    "p96": 3,
    **{k: 4 for k in ("o1fl", "o1fr", "o1bl", "o1br", "o2fl", "o2fr", "o2bl", "o2br")},
}


def bits(v: int) -> int:
    return max(1, v.bit_length())


def raw_bits(values: Sequence[int]) -> int:
    return sum(bits(v) for v in values)


def run_bits(L: int) -> int:
    return 2 * bits(L) - 1


def lifted_advance(v: int, k: int) -> int:
    """Advance the root of a level-encoded value, keeping its level."""
    c = MAPPER.decode_num(v)
    return MAPPER.encode_num(c.level, TOPO.advance(c.root, k))


# ----------------------------------------------------------------------
# pair prediction
# ----------------------------------------------------------------------


def _classify_pair(a: int, b: int):
    if {a, b} == {6, 9}:
        return ("portal", 0 if a == 6 else 1)
    if a == b:
        return ("eq", a)
    ca, cb = MAPPER.decode_num(a), MAPPER.decode_num(b)
    if ca.level != cb.level:
        return None
    if TOPO.pattern(ca.root) != TOPO.pattern(cb.root):
        return None
    L = len(TOPO.cycles[TOPO.pattern(ca.root)])
    k = (TOPO.position_by_root[cb.root] - TOPO.position_by_root[ca.root]) % L
    if k in (1, 2):
        return ("orb", k)
    if L - k in (1, 2):
        return ("orb", -(L - k))
    return None


def _orb_kind(k: int, stored_left: bool) -> str:
    return f"o{abs(k)}{'f' if k > 0 else 'b'}{'l' if stored_left else 'r'}"


def _parse_orb(kind: str):
    m = int(kind[1])
    sign = 1 if kind[2] == "f" else -1
    return sign * m, kind[3] == "l"


def _pairs_for(n: int, p: int):
    pairs, i, j = [], p - 1, p + 1
    while i >= 0 and j < n:
        pairs.append((i, j))
        i, j = i - 1, j + 1
    return pairs


def choose_pivot(strip: Sequence[int]) -> int:
    best_p, best = 0, -1
    for p in range(len(strip)):
        score = sum(
            1
            for i, j in _pairs_for(len(strip), p)
            if _classify_pair(strip[i], strip[j]) is not None
        )
        if score > best:
            best_p, best = p, score
    return best_p


# ----------------------------------------------------------------------
# one fold level
# ----------------------------------------------------------------------


def encode_fold_level(cur: Sequence[int]):
    n = len(cur)
    p = choose_pivot(cur)
    paired, items, residual = set(), [], []
    stored = bits(n + 1) + bits(p + 1)
    predictable = 0
    for i, j in _pairs_for(n, p):
        a, b = cur[i], cur[j]
        paired.update((i, j))
        cl = _classify_pair(a, b)
        if cl is None:
            items.append(("def", i, j, None))
            residual += [a, b]
            stored += TAG_BITS["def"]
        elif cl[0] == "portal":
            kind = "p69" if cl[1] == 0 else "p96"
            predictable += 1
            items.append((kind, i, j, None))
            stored += TAG_BITS[kind]
        elif cl[0] == "eq":
            predictable += 1
            items.append(("eq", i, j, a))
            stored += TAG_BITS["eq"] + bits(a)
        else:
            # v2.2: store the cheaper endpoint -> mirror-symmetric cost.
            k = cl[1]
            stored_left = bits(a) <= bits(b)
            kind = _orb_kind(k, stored_left)
            predictable += 1
            items.append((kind, i, j, a if stored_left else b))
            stored += TAG_BITS[kind] + min(bits(a), bits(b))
    for idx in range(n):
        if idx not in paired:
            items.append(("def", idx, idx, None))
            residual.append(cur[idx])
            stored += TAG_BITS["def"]
    return {"n": n, "p": p, "items": items}, residual, stored, predictable


def level_bits(rec: Dict) -> int:
    total = bits(rec["n"] + 1) + bits(rec["p"] + 1)
    for kind, _i, _j, payload in rec["items"]:
        total += TAG_BITS[kind]
        if payload is not None:
            total += bits(payload)
    return total


def _fill_level(rec: Dict, residual: Sequence[int]) -> List[int]:
    out = [None] * rec["n"]
    it = iter(residual)
    for kind, i, j, payload in rec["items"]:
        if kind == "def":
            if i == j:
                out[i] = next(it)
            else:
                out[i], out[j] = next(it), next(it)
        elif kind == "eq":
            out[i] = out[j] = payload
        elif kind == "p69":
            out[i], out[j] = 6, 9
        elif kind == "p96":
            out[i], out[j] = 9, 6
        else:
            k, stored_left = _parse_orb(kind)
            if stored_left:
                out[i] = payload
                out[j] = lifted_advance(payload, k)
            else:
                out[j] = payload
                out[i] = lifted_advance(payload, -k)
    return out


# ----------------------------------------------------------------------
# multi-level codec with raw fallback
# ----------------------------------------------------------------------


def encode(strip: Sequence[int], max_levels: int = 4) -> Dict:
    strip = list(strip)
    if not strip:
        return {"mode": "raw", "values": []}
    levels, cur, stored_total = [], strip, 0
    while len(cur) >= 4 and len(levels) < max_levels:
        rec, residual, stored, predictable = encode_fold_level(cur)
        if predictable == 0:
            break
        levels.append(rec)
        stored_total += stored
        if not residual:
            cur = []
            break
        cur = residual
    if levels and stored_total + raw_bits(cur) < raw_bits(strip):
        return {"mode": "fold", "levels": levels, "top": cur}
    return {"mode": "raw", "values": strip}


def decode(rec: Dict) -> List[int]:
    if rec["mode"] == "raw":
        return list(rec["values"])
    values = list(rec["top"])
    for lvl in reversed(rec["levels"]):
        values = _fill_level(lvl, values)
    return values


def codec_bits(rec: Dict) -> int:
    if rec["mode"] == "raw":
        return raw_bits(rec["values"])
    return sum(level_bits(l) for l in rec["levels"]) + raw_bits(rec["top"])


# ----------------------------------------------------------------------
# orbit coder with run-length deltas (roots only)
# ----------------------------------------------------------------------


def encode_orbit(seq: Sequence[int]) -> Dict:
    seq = list(seq)
    if not seq:
        return {"items": []}
    deltas = []
    for a, b in zip(seq, seq[1:]):
        if TOPO.pattern(a) == TOPO.pattern(b):
            L = len(TOPO.cycles[TOPO.pattern(a)])
            k = (TOPO.position_by_root[b] - TOPO.position_by_root[a]) % L
            if k in (1, 2):
                deltas.append(("d", k))
                continue
        deltas.append(("j", b))

    items, i = [("start", seq[0], None)], 0
    while i < len(deltas):
        kind, v = deltas[i]
        if kind == "d":
            run = 1
            while i + run < len(deltas) and deltas[i + run] == ("d", v):
                run += 1
            if run >= 3:
                items.append(("r", v, run))
                i += run
                continue
        items.append((kind, v, None))
        i += 1
    return {"items": items}


def decode_orbit(rec: Dict) -> List[int]:
    out = []
    for kind, v, extra in rec["items"]:
        if kind == "start":
            out.append(v)
        elif kind == "d":
            out.append(TOPO.advance(out[-1], v))
        elif kind == "r":
            for _ in range(extra):
                out.append(TOPO.advance(out[-1], v))
        else:
            out.append(v)
    return out


def orbit_bits(rec: Dict) -> int:
    total = 0
    for kind, v, extra in rec["items"]:
        if kind == "start":
            total += bits(v)
        elif kind == "d":
            total += 2
        elif kind == "r":
            total += 2 + run_bits(extra)
        else:
            total += 1 + bits(v)
    return total


# ----------------------------------------------------------------------
# self-tests
# ----------------------------------------------------------------------


def _run_self_tests():
    rnd = random.Random(7)

    walk, x = [], 1
    for _ in range(60):
        walk.append(x)
        x = TOPO.advance(x)
    L = [rnd.randint(1, 63) for _ in range(20)]
    pal = L + [7] + L[::-1]
    rand_ints = [rnd.randint(1, 63) for _ in range(41)]
    rand_roots = [rnd.randint(1, 9) for _ in range(60)]
    W = [rnd.randint(1, 500) for _ in range(20)]
    orb_mirror = W + [5] + [lifted_advance(v, 1) for v in W[::-1]]

    # round-trips
    for data in (pal, rand_ints, orb_mirror, [5], []):
        assert decode(encode(data)) == list(data)
    for data in (walk, rand_roots, [8]):
        assert decode_orbit(encode_orbit(data)) == list(data)

    # v2.2: exact mirror-symmetry of code length on orb structure.
    assert codec_bits(encode(orb_mirror)) == codec_bits(encode(orb_mirror[::-1]))

    # mirror structure compresses
    assert codec_bits(encode(pal)) / raw_bits(pal) < 0.8
    assert codec_bits(encode(orb_mirror)) / raw_bits(orb_mirror) < 0.9

    # portal pairs still detected and used
    rich = [6, 11, 13, 7, 13, 11, 9]
    rec = encode(rich)
    assert decode(rec) == rich
    assert codec_bits(rec) < raw_bits(rich)
    assert any(k in ("p69", "p96") for lvl in rec["levels"] for k, *_ in lvl["items"])

    # multi-level beats single-level on nested structure
    lv = [rnd.randint(0, 6) for _ in range(10)]
    R = [9 * l + 3 for l in lv]
    R = R + [3] + R[::-1]
    strip = [0] * 41
    p = 20
    for t in range(10):
        strip[p - 1 - t], strip[p + 1 + t] = R[2 * t], R[2 * t + 1]
    for t in range(10, 20):
        v = rnd.randint(64, 500)
        strip[p - 1 - t] = strip[p + 1 + t] = v
    strip[p] = 7
    assert decode(encode(strip)) == strip
    multi = codec_bits(encode(strip)) / raw_bits(strip)
    single = codec_bits(encode(strip, max_levels=1)) / raw_bits(strip)
    assert multi < 0.85 and multi < single, (multi, single)

    # random data: raw fallback, never worse than storing as-is
    assert codec_bits(encode(rand_ints)) / raw_bits(rand_ints) <= 1.0

    # orbit coder: RLE crushes walks, honest on random
    r_walk = orbit_bits(encode_orbit(walk)) / raw_bits(walk)
    r_rr = orbit_bits(encode_orbit(rand_roots)) / raw_bits(rand_roots)
    assert r_walk < 0.3
    assert 0.9 <= r_rr <= 1.4
    print("All fold-codec v2.2 self-tests passed.")


if __name__ == "__main__":
    _run_self_tests()
