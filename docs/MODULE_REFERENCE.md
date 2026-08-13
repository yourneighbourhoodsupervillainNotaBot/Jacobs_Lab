# Module reference

## Core

### general_recursive_mapper.py
- `digital_root(n, radix=9)` — `(n-1) % 9 + 1`.
- `RecursiveTopology(radix, multiplier)` — cycles of the multiplication rule.
  For (9,2): `((1,2,4,8,7,5), (3,6,9))`. API: `pattern`, `advance`, `retreat`,
  `trace`, and `classify_root_pair` (labels: same root / jump / advance k /
  retreat k).
- `RecursiveMapper` — `encode_num(level, root) = level*radix + root`,
  `decode_num`, `address`, `map_backward`/`map_forward` (R' = T^∓L(R)),
  `trace_backward`/`trace_forward`.
- Verification: `verify_base9`, `verify_topology`, `batch_verify`.
- Invariants tested: forward∘backward = id, encode/decode round-trip, cycle
  coverage.

### named_aliases.py
- `LETTER_TO_ROOT`: A=3 B=5 C=8 D=9 E=7 F=6 G=6.
- `PORTAL_LETTERS = {"G": (6,9)}`; `PORTAL_CONTEXTS = {"G": {"D": 9}}`
  (in a D-aligned context G acts as 9).
- `UNNAMED_ROOTS = (1,2,4)`.
- `root_to_letters`, `letter_to_root`, `resolve_letter_root`, `NamedMapper`.

### recursive_lattice.py
- `RecursiveLattice(radix=9, x_multiplier=2, y_multiplier=None)`.
- `move(x, y, "RIGHT"|"UP")` advances the X or Y root on its own topology.

## Structure

### triangle_state_machine.py
- 7-state executable loop `F→G→E→D→C→B→A→F`.
- `TriangleState(letter, bits, mode, ab, c)`; enums `Mode`(CONTINUE/DISCONTINUE),
  `AB`(OUTSIDE/INSIDE), `CPhase`(BALANCED/DOWN/UP).
- `TriangleStateMachine`: `state`, `transition`, `next_letter`, `letters`,
  `classify_transition`, `classify_all`, `state_edges`, `resolve_root`,
  `validate_macro`.
- `MACRO_PATHS`: `continues_0=(A,E,G,F)`, `discontinues_1=(A,D,C,B)`.

### folding_graph.py
- `FoldingGraph`: structural edges = MAIN_CHAIN `A-B-C-D`, FOLD_CHAIN `A-E-F-G`,
  CROSS_LINKS `(E,B)`, `(F,C)`; plus the 7 state edges.
- `classify_edges` labels every edge via the mapper.

### set_theory.py
- `UnionFind`, `quotient_set`, `is_partition`, `powerset`, `FiniteFunction`
  (injective/surjective/bijective/compose/inverse).
- `topology_partition` (the two cycles), `portal_quotient` (8 classes; F,G,D
  share one), `fold_quotient` (B~E, C~F).

### Level_tree.py
- `TreeNode(x_root, y_root, depth, move, portal, children, triangle_state,
  state_action)`.
- `build_level_tree` (binary RIGHT/UP tree), `build_triangle_state_path`,
  `flatten`, `count_nodes`, `count_portals`.

### Nested_mapper.py
- `RecursiveNode` chain; `NestedMapper.encode/decode` (ND reversible encoding,
  `R' = T^-L(R)`).
- `annotate_with_triangle_states` attaches per-dimension metadata that does not
  affect equality or decoding.

### flexagon.py
- `STRIP="GFEABCD"`, `PIVOT=3`; `Slot(front, back)`; `fold_packet` (crease first,
  ordered by distance from pivot), `face`, `flex` (period 2), `face_of`.
- Conservation laws tested: letter multiset preserved, flex∘flex = id, exactly
  two orientation flips per loop.

## Computation

### folding_computations.py
- `Cell(value, members)`; `.portal` iff `{6,9} ⊆ members`.
- `Combine`: KEEP_LEFT/RIGHT, DIGITAL_SUM/PRODUCT, PORTAL_MERGE.
- `fold_strip(strip, pivot)` — mirror pairs around pivot; `glue_cells`;
  `fold_reduce`.
- `Pred`/`eval_pred`; `Instr` (FOLD|GLUE|READ|BRANCH|SLIDE|WHILE; note the third
  positional slot is `rule`, SLIDE deltas use `k=`); `run_program` with a step
  budget.
- `find_fold_sequence` (origami solver), `fold_bags`.
- `STATE_SCHEDULE` + `TriangleFoldSimulator` + `run_state_schedule` re-derive the
  whole state loop from fold ops.
- `fold_lattice(points)` — diagonal quotient `(x,y)~(y,x)`; crease = `x==y`
  portals.

### turing_universality.py
- Counters live on root 3 (`enc(level) = level*9+3`).
- `compile_minsky` — INC = SLIDE+1; DEC = BRANCH on `value_eq enc(0)`; dispatch
  via BRANCH on the program counter; whole machine in one WHILE.
- Two-counter Minsky machines are universal ⇒ the folding computer is universal.

### universality_probe.py
- `probe_pure_folds` — enumerates fold-only programs; finds exactly the
  digital-root semiring + projections; `max` and level-extraction are absent.
- `lookup_program` + `run_with_constants` — BRANCH + constants realizes *any*
  finite function (lookup-universal).

### complexity_lab.py
- `verify_subset_sum` (O(n)) vs `search_subset_sum` (2^n); `make_instance`.
- `eq_machine`/`folding_eq` — a verifier compiled to the VM.
- `realizable_count(budget)` — resource-bounded realizability curve.

## Math lenses

### category_theory.py
- `FiniteCategory`, `topology_groupoid` (Z-action groupoid on cycles),
  `thin_category` (reflexive–transitive closure), `connected_components`.

### natural_transformations.py
- `ThinFunctor`, `NaturalTransformation` (`is_natural`, `is_iso`,
  `vertical_compose`).
- `build_portal_natural_isomorphism` — `eta: literal_root => portal_flipped_root`,
  components swap 6↔9 on F, G, D; proven natural and iso.
- `portal_quotient_category`.

### galois_fields.py
- `GFp`, `GFpn` (polynomials mod an irreducible; `frobenius`), `find_irreducible`.
- `galois_view(radix, multiplier)` — reads the topology as a field orbit (prime
  radix) or a ring decomposition (composite radix).

### quintic_analysis.py
- `rational_roots`, `mod9_sieve`, `factor_mod_p`, `cycle_type` (Dedekind),
  `s5_evidence` (5-cycle + transposition ⇒ Galois = S5), `durand_kerner`.

## Instruments

### fold_codec.py
- Multi-level folding codec. Predictors: `eq` (equal pair), `orb` (same-cycle
  ±1/±2 step), `portal` ({6,9}); fallback `def`; global raw fallback.
- `encode`/`decode`/`codec_bits`; `lifted_advance`; orbit coder
  `encode_orbit`/`decode_orbit`/`orbit_bits` with run-length deltas.
- v2.2 stores the cheaper orb endpoint ⇒ exact mirror symmetry of code length.

### fold_complexity.py
- `fold_complexity(strip) = codec_bits / raw_bits ∈ (0,1]` (1 = incompressible).
- `complexity_split` — predictable (fold-computable) vs table bits.
- Axioms tested: bounded; random ≈ 1; structured < random; mirror-symmetric;
  shuffling never simplifies.

### prime_machinery.py
- `is_admissible` (primes >3 lie on the doubling cycle; 3 is the only 3-6-9 prime).
- `sieve`, `lucas_certificate`/`certified_prime`, `mod3_machine`/`folding_mod3`
  (the admissibility filter reproduced on the universal VM).

### pathfinding_lab.py
- `bfs`, `cyclic_delta`, `geodesic` (closed form), `astar` (exact, consistent
  group-derived heuristic), `dijkstra`.
- `portal_quotient_test` — zero-cost identifications preserve all distances.
- `gated_search` (state-gated product space), `biased_search` (fold-complexity
  prior).

### three_body_lab.py
- Figure-eight initial conditions; `leapfrog_step`/`integrate` (symplectic),
  `energy`.
- `shape_symbol` (1..8: balanced/collinear/longest-side + chirality),
  `find_period`, `symbol_complexity` (periodic ⇒ compressible; chaos ⇒ 1.0).

## Presentation

### sonify.py
- 9-EDO tuning (`root_freq`); ternary chords = mod-3 residue classes (the 9-EDO
  analog of an augmented triad).
- `sonify_walk` maps machine state to articulation: jumps accented/longer,
  same-root shorter, CONTINUE = ascending arpeggio, DISCONTINUE = block chord.
- `render`, `write_wav`.

### test_sonify.py
- `sonify_test_results`: PASS = ternary chord; FAIL = dissonant clash (root +
  nearest 9-EDO neighbor + sub-octave), longer and accented.
- Writes `test_suite.wav` and a synthetic-failure demo.

### test_walk_engine.py / test_tree_preview.py / pyglet_visualizer.py
- `build_test_tree`: PASS→RIGHT, FAIL→UP; child[0] taken, child[1] an untaken
  "preview" stub; results kept in a side dict.
- `layout_test_tree` — deterministic spine layout with preview offshoots.
- `render_preview` — static matplotlib PNG (spine solid, previews dashed, portal
  gold, fail red).
- `pyglet_visualizer` — live reveal scheduled on the same cumulative timeline as
  the audio.

## Testing

### test_harness.py / run_all_tests.py
- `run_all_tests` imports each module in `MODULE_NAMES` and runs
  `_run_self_tests()`, returning `TestResult(module, passed, duration, error)`.
- `run_all_tests.py` groups modules (CORE / MATH LENSES / COMPUTATION /
  INSTRUMENTS), supports `--fast`, prints a ledger, exits non-zero on failure.