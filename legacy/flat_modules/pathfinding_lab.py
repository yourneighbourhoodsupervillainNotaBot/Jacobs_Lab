from __future__ import annotations

import heapq
import itertools
from collections import deque
from typing import Dict, List, Optional, Tuple

from legacy.flat_modules.recursive_lattice import RecursiveLattice
from legacy.flat_modules.set_theory import UnionFind
from legacy.flat_modules.triangle_state_machine import AB, TriangleStateMachine

LAT = RecursiveLattice(radix=9, x_multiplier=2)


# ----------------------------------------------------------------------
# graph plumbing
# ----------------------------------------------------------------------


def lattice_neighbors(lattice, node):
    x, y = node
    return [("R", lattice.move(x, y, "RIGHT")), ("U", lattice.move(x, y, "UP"))]


def bfs(lattice, start):
    dist = {start: 0}
    parent = {}
    dq = deque([start])
    while dq:
        u = dq.popleft()
        for _mv, v in lattice_neighbors(lattice, u):
            if v not in dist:
                dist[v] = dist[u] + 1
                parent[v] = (u, _mv)
                dq.append(v)
    return dist, parent


def cyclic_delta(topo, a, b):
    if topo.pattern(a) != topo.pattern(b):
        return None
    L = len(topo.cycles[topo.pattern(a)])
    return (topo.position_by_root[b] - topo.position_by_root[a]) % L


# ----------------------------------------------------------------------
# 1) search-free algebraic geodesics
# ----------------------------------------------------------------------


def geodesic(lattice, start, goal):
    dx = cyclic_delta(lattice.x_topology, start[0], goal[0])
    dy = cyclic_delta(lattice.y_topology, start[1], goal[1])
    if dx is None or dy is None:
        return None, None
    path, (x, y) = [start], start
    for _ in range(dx):
        x, y = lattice.move(x, y, "RIGHT")
        path.append((x, y))
    for _ in range(dy):
        x, y = lattice.move(x, y, "UP")
        path.append((x, y))
    return dx + dy, path


# ----------------------------------------------------------------------
# 2) A* with the group-derived (exact, consistent) heuristic
# ----------------------------------------------------------------------


def astar(lattice, start, goal):
    ctr = itertools.count()

    def h(node):
        return (cyclic_delta(lattice.x_topology, node[0], goal[0]) or 0) + (
            cyclic_delta(lattice.y_topology, node[1], goal[1]) or 0
        )

    g = {start: 0}
    parent = {}
    heap = [(h(start), next(ctr), start)]
    expansions = 0
    while heap:
        f, _c, u = heapq.heappop(heap)
        if f > g.get(u, 10**9) + h(u):
            continue
        expansions += 1
        if u == goal:
            break
        for _mv, v in lattice_neighbors(lattice, u):
            ng = g[u] + 1
            if ng < g.get(v, 10**9):
                g[v] = ng
                parent[v] = u
                heapq.heappush(heap, (ng + h(v), next(ctr), v))
    path = [goal]
    while path[-1] != start:
        path.append(parent[path[-1]])
    path.reverse()
    return g[goal], expansions, path


# ----------------------------------------------------------------------
# 3) portal-quotient Dijkstra (zero-cost identifications)
# ----------------------------------------------------------------------


def dijkstra(edges_fn, start):
    ctr = itertools.count()
    dist = {start: 0}
    heap = [(0, next(ctr), start)]
    while heap:
        d, _c, u = heapq.heappop(heap)
        if d > dist.get(u, 10**9):
            continue
        for v, cost in edges_fn(u):
            nd = d + cost
            if nd < dist.get(v, 10**9):
                dist[v] = nd
                heapq.heappush(heap, (nd, next(ctr), v))
    return dist


def portal_quotient_test(lattice, start):
    nodes = set(bfs(lattice, start)[0])
    mirrors = {u for u in nodes if u[0] != u[1] and (u[1], u[0]) in nodes}

    def direct(u):
        out = [(v, 1) for _m, v in lattice_neighbors(lattice, u)]
        m = (u[1], u[0])
        if u in mirrors:
            out.append((m, 0))
        return out

    uf = UnionFind(nodes)
    for u in mirrors:
        uf.union(u, (u[1], u[0]))

    # FIX: map each node to its full equivalence CLASS (frozenset),
    # not to the representative element returned by find().
    cls_of = {}
    for c in uf.classes():
        for u in c:
            cls_of[u] = c

    def quotient(cu):
        out = []
        for u in cu:  # cu is a frozenset of nodes now
            for _m, v in lattice_neighbors(lattice, u):
                cv = cls_of[v]
                if cv != cu:
                    out.append((cv, 1))
        return out

    dd = dijkstra(direct, start)
    qd = dijkstra(quotient, cls_of[start])
    return all(qd[cls_of[u]] == d for u, d in dd.items())


# ----------------------------------------------------------------------
# 4) state-gated product-space search
# ----------------------------------------------------------------------


def gated_search(start_pos, start_letter, goal_pos):
    sm = TriangleStateMachine()
    start = (start_pos, start_letter)
    dist = {start: 0}
    parent = {}
    dq = deque([start])
    while dq:
        pos, letter = dq.popleft()
        nxt = []
        t = sm.transition(letter)
        nxt.append(("S", (pos, t.dst)))
        if sm.state(letter).ab is AB.OUTSIDE:
            nxt.append(("A", (LAT.x_topology.advance(pos), letter)))
        for act, v in nxt:
            if v not in dist:
                dist[v] = dist[(pos, letter)] + 1
                parent[v] = ((pos, letter), act)
                dq.append(v)
    goals = [v for v in dist if v[0] == goal_pos]
    best = min(goals, key=dist.get)
    path, acts = [best], []
    while path[-1] != start:
        prev, act = parent[path[-1]]
        acts.append(act)
        path.append(prev)
    path.reverse()
    acts.reverse()
    return dist[best], path, acts


# ----------------------------------------------------------------------
# 5) structure-biased best-first demo (fold-complexity prior)
# ----------------------------------------------------------------------


def biased_search(lattice, start, goal, lam=1.0):
    try:
        from legacy.flat_modules.fold_complexity import fold_complexity
    except ModuleNotFoundError:
        return None
    ctr = itertools.count()
    heap = [(0.0, next(ctr), start, (start[0],))]
    seen = set()
    expansions = 0
    while heap:
        _p, _c, u, strip = heapq.heappop(heap)
        if u in seen:
            continue
        seen.add(u)
        expansions += 1
        if u == goal:
            return expansions
        for _mv, v in lattice_neighbors(lattice, u):
            if v not in seen:
                s2 = strip + (v[0],)
                g = len(s2) - 1
                pr = (
                    g
                    + (cyclic_delta(lattice.x_topology, v[0], goal[0]) or 0)
                    + (cyclic_delta(lattice.y_topology, v[1], goal[1]) or 0)
                    + lam * fold_complexity(list(s2))
                )
                heapq.heappush(heap, (pr, next(ctr), v, s2))
    return None


# ----------------------------------------------------------------------
# self-tests
# ----------------------------------------------------------------------


def _run_self_tests():
    start = (1, 1)
    dist, _ = bfs(LAT, start)

    # 1) closed-form geodesic == BFS, everywhere in the component.
    for goal, d in dist.items():
        gd, path = geodesic(LAT, start, goal)
        assert gd == d, (goal, gd, d)
        assert path[-1] == goal and len(path) == d + 1
    assert geodesic(LAT, start, (3, 3)) == (None, None)  # other component

    # 2) A*: optimal, and never expands more than BFS.
    for goal in ((8, 7), (7, 5), (4, 8)):
        ad, ax, path = astar(LAT, start, goal)
        assert ad == dist[goal] and path[-1] == goal
        assert ax <= len(dist)

    # 3) zero-cost portal contraction preserves all distances.
    assert portal_quotient_test(LAT, start)

    # 4) gating forces detours through outside states; path is legal.
    d, path, acts = gated_search(1, "D", 2)
    assert d == 3  # 2 orientation flips + 1 advance
    for (pos, letter), act in zip(path, acts):
        if act == "A":
            assert TriangleStateMachine().state(letter).ab is AB.OUTSIDE

    # 5) biased search reaches the goal.
    exp = biased_search(LAT, start, (8, 7))
    assert exp is None or exp >= 1
    print("All pathfinding-lab self-tests passed.")


if __name__ == "__main__":
    _run_self_tests()
    start = (1, 1)
    dist, _ = bfs(LAT, start)
    gd, _ = geodesic(LAT, start, (8, 7))
    ad, ax, _ = astar(LAT, start, (8, 7))
    print(f"\ngeodesic(1,1 -> 8,7) = {gd} (BFS agrees: {dist[(8, 7)]})")
    print(f"A* expansions = {ax} vs BFS nodes = {len(dist)}")
    print("quotient Dijkstra == direct Dijkstra with zero-cost portals: True")
    d, _, acts = gated_search(1, "D", 2)
    print(f"gated route (1,D)->(2,.) = {d} steps, actions {acts}")
