# Mathematics

## Digital-root topology
Multiplication by a unit `k` mod `radix`, written in digital-root form, partitions
roots into cycles. For (9,2): the *doubling* cycle `(1,2,4,8,7,5)` and the
*3-6-9* cycle `(3,6,9)`. `advance`/`retreat` move along a cycle and are exact
inverses; `classify_root_pair` is the canonical label for any root transition.

## Coordinates
A number `n` decodes to `(level, root)` with `n = level*9 + root`. The backward
map is `R' = T^-L(R)` (retreat the root by the level); forward is its inverse.
`NestedMapper` lifts this to N dimensions as a reversible chain.

## Letters and portals
The drawing's letters cover roots {3,5,6,7,8,9}; roots {1,2,4} are unnamed.
`G` is a portal: it draws as 6 but is `{6,9}`, and in a D-aligned context it
resolves to 9. This single ambiguity is what the portal quotient and the natural
isomorphism formalize.

## Quotients
- `portal_quotient`: identify 6~9 ⇒ 8 classes; F, G, D collapse to one.
- `fold_quotient`: the cross-links identify B~E and C~F.
- `fold_strip`: folding at a pivot identifies mirror-indexed cells; the tip of
  `GFEABCD` at pivot 3 is exactly the portal `{6,9}`.
- `fold_lattice`: the 2D analogue, `(x,y)~(y,x)`; the crease (fixed points) is
  precisely the portal nodes.

## Category lens
- `topology_groupoid`: morphisms `(r, k, s)` = "advance k steps"; two connected
  components = the two cycles.
- Adding the fold graph's edges makes the thin category connected.
- `portal_eta`: the natural isomorphism between the literal-root functor and the
  portal-flipped-root functor; components are the identity except 6↔9 on F, G, D.
  Naturality and invertibility are machine-checked.

## Galois / quintic lens
- `galois_view(9,2)`: radix 9 is composite ⇒ a *ring*, not a field: units orbit
  of length 6 plus zero-divisors {3,6}. Prime radix (e.g. 7 with multiplier 3)
  gives a genuine field with a primitive root.
- Quintics: factorization mod p gives Frobenius cycle types (Dedekind). A 5-cycle
  plus a transposition certify Galois = S5 ⇒ not solvable by radicals. Numeric
  roots come from Durand–Kerner. The lab reports *certified* vs *not certified*
  honestly.

## Prime lens
- Filter: a prime >3 must have digital root on the doubling cycle (a mod-3 sieve
  in disguise); necessary, not sufficient (25 passes).
- Certify: a Lucas witness `a` with `ord_n(a) = n-1` is a machine-checkable proof.
- Execute: a Minsky mod-3 machine on the universal VM reproduces the filter.