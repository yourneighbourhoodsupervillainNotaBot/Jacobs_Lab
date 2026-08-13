# Glossary

- **root** — a digital root 1..9; the residue class of a number mod 9 (with 9
  representing 0).
- **level** — the quotient `(n-1)//9`; the "octave" of a coordinate.
- **address** — `(level, root, pattern)`; a decoded number plus its cycle.
- **cycle / pattern** — an orbit of the multiplication rule; (9,2) has the
  doubling cycle and the 3-6-9 cycle.
- **portal** — the letter/cell carrying both 6 and 9; the site of an
  identification.
- **crease** — the fixed line of a mirror fold; in `fold_lattice`, the diagonal
  `x==y` portals.
- **fold** — identifying mirror-indexed cells around a pivot (a quotient).
- **glue** — identifying two adjacent cells (a quotient).
- **quotient set** — the partition produced by a set of identifications.
- **digital root** — `(n-1) % 9 + 1`.
- **9-EDO** — nine equal divisions of the octave; the lab's tuning.
- **ternary chord** — a root's mod-3 residue class, an exact 3-way octave
  division in 9-EDO.
- **admissible** — passing the topology mod-3 prime filter (necessary, not
  sufficient).
- **Lucas witness** — `a` with `ord_n(a)=n-1`; a machine-checkable primality proof.
- **cycle type** — degrees of irreducible factors mod p = Frobenius cycle type.
- **S5 evidence** — a prime giving a 5-cycle and a prime giving a transposition.
- **shape symbol** — 1..8 code of a three-body configuration (base shape +
  chirality).
- **FC (fold complexity)** — `codec_bits / raw_bits ∈ (0,1]`; 1 = incompressible.
- **predictable bits** — codec bits explained by fold-computable predictors.
- **preview stub** — the untaken branch kept beside the walked path.