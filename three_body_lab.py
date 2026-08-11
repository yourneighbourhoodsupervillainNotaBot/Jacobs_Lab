from __future__ import annotations

import math
from typing import List, Optional, Tuple

# ----------------------------------------------------------------------
# physics: equal masses, G = 1, leapfrog (symplectic) integration
# ----------------------------------------------------------------------

FIG_X = [(0.97000436, -0.24308753), (-0.97000436, 0.24308753), (0.0, 0.0)]
FIG_V = [
    (0.466203685, 0.43236573),
    (0.466203685, 0.43236573),
    (-0.93240737, -0.86473146),
]
PERIOD = 6.32451


def accelerations(pos):
    acc = []
    for i in range(3):
        ax = ay = 0.0
        for j in range(3):
            if i == j:
                continue
            dx = pos[j][0] - pos[i][0]
            dy = pos[j][1] - pos[i][1]
            r2 = dx * dx + dy * dy
            inv = 1.0 / (r2 * math.sqrt(r2))
            ax += dx * inv
            ay += dy * inv
        acc.append((ax, ay))
    return acc


def leapfrog_step(pos, vel, dt):
    a = accelerations(pos)
    vel = [(v[0] + ax * dt / 2, v[1] + ay * dt / 2) for v, (ax, ay) in zip(vel, a)]
    pos = [(p[0] + v[0] * dt, p[1] + v[1] * dt) for p, v in zip(pos, vel)]
    a = accelerations(pos)
    vel = [(v[0] + ax * dt / 2, v[1] + ay * dt / 2) for v, (ax, ay) in zip(vel, a)]
    return pos, vel


def integrate(pos, vel, dt, steps):
    traj = [pos]
    for _ in range(steps):
        pos, vel = leapfrog_step(pos, vel, dt)
        traj.append(pos)
    return traj, pos, vel


def energy(pos, vel):
    ke = 0.5 * sum(v[0] ** 2 + v[1] ** 2 for v in vel)
    pe = -sum(
        1.0 / math.hypot(pos[j][0] - pos[i][0], pos[j][1] - pos[i][1])
        for i in range(3)
        for j in range(i + 1, 3)
    )
    return ke + pe


# ----------------------------------------------------------------------
# shape space: quotient out translation/scale; keep elongation + chirality
# (vocabulary mirrors the triangle language: balanced / flip-zone /
#  elongated, inside-outside ~ chirality sign)
# ----------------------------------------------------------------------


def oriented_area(pos):
    cx = sum(p[0] for p in pos) / 3
    cy = sum(p[1] for p in pos) / 3
    r = [(p[0] - cx, p[1] - cy) for p in pos]
    return 0.5 * (
        r[0][0] * r[1][1]
        - r[1][0] * r[0][1]
        + r[1][0] * r[2][1]
        - r[2][0] * r[1][1]
        + r[2][0] * r[0][1]
        - r[0][0] * r[2][1]
    )


def shape_symbol(pos) -> int:
    """1..8: base shape (balanced / collinear / which side longest) + chirality."""
    cx = sum(p[0] for p in pos) / 3
    cy = sum(p[1] for p in pos) / 3
    r = [(p[0] - cx, p[1] - cy) for p in pos]
    I = sum(x * x + y * y for x, y in r)
    a2 = oriented_area(pos)

    def d(i, j):
        return math.hypot(r[i][0] - r[j][0], r[i][1] - r[j][1])

    s = sorted((d(0, 1), d(1, 2), d(2, 0)))
    mean = (s[0] + s[1] + s[2]) / 3
    if mean == 0:
        return 1
    if s[2] - s[0] < 0.25 * mean:
        base = 0  # balanced (Lagrange-like)
    elif abs(a2) < 0.03 * I:
        base = 1  # near-collinear (Euler-like, flip zone)
    else:
        base = 2 + (d(1, 2), d(2, 0), d(0, 1)).index(max((d(1, 2), d(2, 0), d(0, 1))))
    return 1 + base + (4 if a2 < 0 else 0)


# ----------------------------------------------------------------------
# regularity diagnostic: periodicity => compressible symbol stream
# ----------------------------------------------------------------------


def find_period(stream, tol=0.95) -> Optional[int]:
    n = len(stream)
    for p in range(1, n // 2 + 1):
        agree = sum(1 for i in range(n - p) if stream[i] == stream[i + p])
        if agree >= tol * (n - p):
            return p
    return None


def symbol_complexity(stream):
    """(ratio, period): periodic streams encode as block+repeat_count (small ratio);
    aperiodic ones stay at 1.0 -- the chaos diagnostic."""
    n = len(stream)
    p = find_period(stream)
    if p is None:
        return 1.0, None
    # Encoding cost: one block of length p (3p bits) + repeat count (log2(n/p)) + overhead
    repeat_count = max(1, n // p)
    compressed = 3 * p + max(1, repeat_count.bit_length()) + 8
    raw = 3 * n
    return compressed / raw, p


# ----------------------------------------------------------------------
# self-tests
# ----------------------------------------------------------------------


def _run_self_tests():
    dt = 0.005
    spp = int(round(PERIOD / dt))

    # 1) symplectic integrator conserves energy over one period
    traj, pos_t, vel_t = integrate([p for p in FIG_X], [v for v in FIG_V], dt, spp)
    e0, e1 = energy(FIG_X, FIG_V), energy(pos_t, vel_t)
    assert abs(e1 - e0) / abs(e0) < 1e-2

    # 2) the orbit closes: back near the start after one period
    dev = max(math.hypot(a[0] - b[0], a[1] - b[1]) for a, b in zip(pos_t, FIG_X))
    assert dev < 0.05, dev

    # 3) figure-eight: periodic, compressible symbol stream; both chiralities
    #    FIX: integrate 4 periods so the period is 1/4 of the stream, not 1/2.
    traj2, _, _ = integrate(FIG_X, FIG_V, dt, 4 * spp)
    stream = [shape_symbol(traj2[k]) for k in range(0, 4 * spp + 1, 5)]
    ratio, p = symbol_complexity(stream)
    assert p is not None and ratio < 0.4, (ratio, p)
    areas = [oriented_area(traj2[k]) for k in range(0, 4 * spp + 1, 5)]
    assert any(a > 0 for a in areas) and any(a < 0 for a in areas)

    # 4) perturbed run diverges: aperiodic, incompressible
    pv = [(v[0] + (0.05 if i == 0 else 0.0), v[1]) for i, v in enumerate(FIG_V)]
    traj3, _, _ = integrate(FIG_X, pv, dt, 4 * spp)
    stream3 = [shape_symbol(traj3[k]) for k in range(0, 4 * spp + 1, 5)]
    ratio3, p3 = symbol_complexity(stream3)
    assert p3 is None and ratio3 == 1.0, (ratio3, p3)
    print("All three-body-lab self-tests passed.")
    return ratio, p, ratio3


if __name__ == "__main__":
    ratio, p, ratio3 = _run_self_tests()
    print(f"\nfigure-eight : symbol complexity {ratio:.3f} (period {p})")
    print(f"perturbed    : symbol complexity {ratio3:.3f} (no period)")
    try:
        from fold_complexity import fold_complexity

        stream = [
            shape_symbol(t)
            for t in integrate(FIG_X, FIG_V, 0.005, 4 * int(round(PERIOD / 0.005)))[0][
                ::5
            ]
        ]
        print(
            f"fold-complexity cross-read (informational): {fold_complexity(stream):.2f}"
        )
    except ModuleNotFoundError:
        pass
    print("\nThe codebase does not solve the three-body problem (no closed form")
    print("exists); it classifies its motion: regular orbits compress, chaos does not.")
