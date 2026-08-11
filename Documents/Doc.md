# The Folding Laboratory

An executable, self-certifying laboratory grown from one informal symbolic
drawing (`text.txt`). A single tiny algebraic system — digital roots, the
doubling cycles mod 9, and the portal `6(9)` — is developed simultaneously
through arithmetic, algebra, category theory, computability, information
theory, and physics. **Every claim ships as an executed self-test**, and the
views cross-validate: the portal that collapses letters in the quotient is
the same natural isomorphism, the same 2-bit codec symbol, and the same
flexagon tip-gluing.

## Quick start

```text
python run_all_tests.py        # unified ledger of all self-tests
python run_all_tests.py --fast # skip slow labs
python <module>.py             # each module also demos itself
```

## The lens ladder

| Layer | Modules | What it makes executable |
|---|---|---|
| Numeric core | `general_recursive_mapper`, `Nested_mapper`, `recursive_lattice`, `Level_tree` | Reversible dimension-independent encodings; cyclic topology; lattice trees with portals |
| Symbolic | `named_aliases`, `triangle_state_machine`, `folding_graph` | The drawing as a tested state machine; fold graph with state edges |
| Math lenses | `galois_fields`, `set_theory`, `category_theory`, `natural_transformations` | Ring decomposition (units = 6-cycle, ideal = 3/6/9); quotients; groupoids; portal as η with P∘F = P∘G |
| Computation | `folding_computation`, `turing_universality`, `universality_probe`, `flexagon` | Folding VM; Minsky compiler (Turing-universal); computational-class ladder; flexagon faces = macro blocks |
| Instruments | `quintic_analysis`, `fold_codec`, `fold_complexity`, `prime_machinery`, `complexity_lab`, `pathfinding_lab`, `three_body_lab` | S₅ solvability certificates + numeric roots; algebraic compression; axiom-validated complexity measure; prime filter/test/certify/execute; verifier-vs-search; algebraic pathfinding; chaos diagnostic |

## Headline results (each witnessed by a self-test)

- Folding computer is Turing-universal (step-exact Minsky compilation).
- Computational ladder: pure folds = Z/9Z semiring ⊂ finite functions  universal.
- Codec never expands incompressible data; multi-level + symmetric orb encoding.
- Fold-complexity axioms: bounded, structure < noise, mirror-exact, shuffle-monotone.
- Quintics: Dedekind/S₅ certificate (no radicals) + Durand–Kerner roots.
- Primes: topology admissibility = mod-3 sieve; Lucas witnesses as proofs.
- Pathfinding: closed-form geodesics == BFS; quotient Dijkstra lossless.
- Three-body: figure-eight compressible (period found), perturbed run = 1.0.

## What it is good at

- **Teaching companion** for algebra, category theory, computability, information
  theory — one consistent system across all of them.
- **Research seed** in unconventional (quotient-based) computation,
  theory-relative complexity/MDL, algebraic features for learning.
- **Autoformalization specimen**: informal artifact → layered verified theory.
- **Outreach**: folding-as-computation, flexagons, portals-as-identifications.
