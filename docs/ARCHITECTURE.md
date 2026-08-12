# Jacobs Lab Architecture

Source of truth: `src/jacobs_lab/`

Legacy flat modules: `legacy/flat_modules/`

Canonical imports use subpackage paths, for example:

```python
from jacobs_lab.core.general_recursive_mapper import RecursiveMapper
from jacobs_lab.structure.level_tree import TreeNode
from jacobs_lab.computation.folding_computations import run_program
```
