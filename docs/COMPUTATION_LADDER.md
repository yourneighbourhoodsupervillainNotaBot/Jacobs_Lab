# The computational ladder

The folding VM (`folding_computations.run_program`) operates on strips of `Cell`s
with six instructions: `FOLD`, `GLUE`, `READ`, `BRANCH`, `SLIDE`, `WHILE`.
Combining rules form a digital-root semiring plus a portal merge.

## Rung 1 — pure folds
`probe_pure_folds` shows fold-only programs compute exactly the digital-root
semiring (sum, product) and projections. `max` and level-extraction are *not*
realizable. This is a precise characterization, not a limitation of search.

## Rung 2 — add BRANCH (+ constants)
`lookup_program` builds a branch tree over `value_eq` predicates that computes
*any* finite function on a domain, given an explicit constants list. So
branching + constants is lookup-universal; it lifts the class beyond the
semiring (e.g. `max`, level+1).

## Rung 3 — add SLIDE + WHILE
`SLIDE` changes a cell's level by `k*radix` (unbounded counter arithmetic);
`WHILE` loops on a predicate. `turing_universality.compile_minsky` simulates any
two-counter Minsky machine step-exactly (INC = SLIDE+1, DEC = BRANCH zero-test,
dispatch = BRANCH on pc, loop = WHILE). Two-counter machines are universal
(Minsky 1961) ⇒ **the folding computer is Turing-universal.**

## Closure and consistency
- `run_state_schedule` re-derives the entire 7-state triangle loop from fold ops
  alone, closing the loop exactly.
- The flexagon conservation laws (letter multiset, period-2 flex, two flips per
  lap) tie the physical fold to the state machine.

## Resource bounds
`complexity_lab.realizable_count(budget)` counts distinct functions realizable
within a step budget: with no budget nothing computes; more budget never reduces
what is realized. Time is a genuine computational constraint — the empirical face
of descriptional complexity.