# CONV0 pre-run freeze

The synthetic mixing system, frequency grid, pass criteria, seed count, proposal budgets, and reversed-frequency control are committed before the first morphology run.

The gate must not be retuned after seeing the first result. If code fails mechanically, repair the implementation without changing the frozen scientific target or thresholds and record the repair here.

Frozen implementation commit lineage begins with:

- `notes/conv0_rotating_demixer_contract.md`
- `experiments/fa_bss_conv0_rotating.py`
- `.github/workflows/conv0.yml`

The deliberately simple exact digital attacker is retained: `y[t] = x1[t] - 0.90*x2[t-14]`.
