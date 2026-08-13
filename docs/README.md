# Jacobs Lab — a folding / digital-root laboratory

A self-testing Python laboratory that explores one structural idea from many
directions: **base-9 digital-root topology, read as folding, quotienting,
computation, music, and geometry.**

## Requirements

- Python 3.10+
- `numpy`        (audio synthesis)
- `matplotlib`   (static tree preview)
- `pyglet`       (live visualizer)

    pip install numpy matplotlib pyglet

## Run everything

    python run_all_tests.py            # full self-test ledger
    python run_all_tests.py --fast     # skip slow instrument labs

## Presentations

    python test_sonify.py              # sonify the suite -> test_suite.wav
    python test_tree_preview.py        # static lattice-walk PNG
    python pyglet_visualizer.py        # live walk synced to audio

## Layer map

| Layer        | Modules |
|--------------|---------|
| Core         | `general_recursive_mapper`, `named_aliases`, `recursive_lattice` |
| Structure    | `triangle_state_machine`, `folding_graph`, `set_theory`, `Level_tree`, `Nested_mapper`, `flexagon` |
| Computation  | `folding_computations`, `turing_universality`, `universality_probe`, `complexity_lab` |
| Math lenses  | `category_theory`, `natural_transformations`, `galois_fields`, `quintic_analysis` |
| Instruments  | `fold_codec`, `fold_complexity`, `prime_machinery`, `pathfinding_lab`, `three_body_lab` |
| Presentation | `sonify`, `test_sonify`, `test_walk_engine`, `test_tree_preview`, `pyglet_visualizer` |
| Testing      | `test_harness`, `run_all_tests` |

## Honest scope (read this first)

- **Primes:** no closed-form formula. The lab *filters* (topology admissibility),
  *tests* (sieve), *certifies* (Lucas witnesses), and *executes* (mod-3 on the VM).
- **P vs NP:** not solved. The lab shows the empirical asymmetry
  (verify = polynomial, search = exponential) and resource-bounded realizability.
- **Three-body:** no closed form. The lab integrates symplectically and
  *classifies* motion: regular orbits compress, perturbed/chaos does not.
- **Quintics:** no radicals (Abel–Ruffini). The lab certifies Galois = S5 via
  Dedekind cycle types and computes numeric roots.

## Documentation index

- `docs/ARCHITECTURE.md` — layers, dependency graph, design principles
- `docs/MODULE_REFERENCE.md` — per-module API and invariants
- `docs/MATHEMATICS.md` — topology, portals, quotients, categories, Galois, primes
- `docs/COMPUTATION_LADDER.md` — the folding VM and its universality results
- `docs/PRESENTATION_AND_TESTING.md` — audio, visuals, test harness
- `docs/GLOSSARY.md` — terminology