# Test plan for committed FA-BSS0

Run from a directory where `Monday` and `FunctionalArbors` are sibling checkouts:

```bash
cd Monday
python experiments/fa_bss0_run.py --fa-root ../FunctionalArbors --seeds 8 --mutations 28
```

Then inspect `fa_bss0_out.json` before changing the gate.  If reward beats shuffle, repeat over a predeclared bank of mixing matrices rather than tuning one matrix.  If reward fails, run the reachable-ratio sweep first.
