# Architecture

## Dependency flow (simplified)

    general_recursive_mapper ──> named_aliases ──> recursive_lattice
            │                          │
            ├──────────────> triangle_state_machine ──> folding_graph
            │                          │
            ├──────────────> set_theory ──> category_theory ──> natural_transformations
            │                          │
            ├──────────────> galois_fields ──> quintic_analysis
            │                          │
            └──────────────> folding_computations ──> turing_universality
                                       │                  │
                                       ├─> universality_probe / complexity_lab
                                       ├─> prime_machinery
                                       ├─> fold_codec ──> fold_complexity
                                       ├─> pathfinding_lab
                                       └─> flexagon
    presentation: sonify / test_sonify / test_walk_engine / previews / visualizer
    testing:      test_harness / run_all_tests

## Design principles

1. **Every module self-tests.** Each exposes `_run_self_tests()` that prints on
   success and raises on failure. `run_all_tests.py` is the single ledger.
2. **Single source of truth.** Root-pair classification lives only in
   `RecursiveMapper.classify_root_pair`; the state machine, folding graph, and
   sonifier all read from it.
3. **Reversibility.** Coordinate maps (`map_forward`/`map_backward`,
   `NestedMapper.encode/decode`, `advance`/`retreat`) are exact inverses and are
   tested as such.
4. **Quotient as unifier.** Folding = identifying cells (`UnionFind`). Portals,
   flexagon faces, lattice mirror folds, and category quotients are all the same
   construction on different carriers.
5. **Honest scope.** Modules state what they can and cannot prove; self-tests
   assert the boundary (e.g. `max` is *not* fold-computable; perturbed three-body
   is *not* compressible).