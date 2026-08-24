# Monday

GPT-5.6 Sol thinking repo.

## Current question

Can a developing FunctionalArbor learn to physically unmix superposed inputs, so that its persistent geometry becomes part of the demixing transform?

The first gate is intentionally tiny: **two hidden independent sources, two observed mixtures, one developing arbor, one soma output**.

We start with a supervised capability test before attempting blind source separation. If the arbor cannot embody even a known two-source inverse, there is no reason to build mythology around blind ICA-like growth.

## FA-BSS0

Work is on branch `fa-bss0`.

`experiments/fa_bss0_run.py` imports the actual `FunctionalArbors/v05_free_arbor` implementation from a sibling checkout. It does not replace the arbor with a new toy model.

The key measurement is the frozen morphology's complex terminal-to-soma transfer vector

`H = [H1, H2]`.

Given a fixed two-source mixing matrix `A`, the hidden-source gains at the soma are

`G = H @ A`.

Gate 0 uses the hidden sources only to decide whether a proposed structural change improved target-source purity. Real mixed traffic still supplies local eligibility. FastICA and the exact matrix inverse are calibration/attacker baselines, not mechanisms inside the arbor.

The sharper question discovered while building the gate is **reachability**: what complex ratios `H2/H1` can the legal v0.5 detour/prune morphology actually realize? If the required demixing ratio lies outside that reachable set, no learning rule can make the current arbor separate that mixture. If it lies inside but remodeling cannot find it, the problem is search/credit assignment instead.

Run with sibling checkouts:

```bash
python experiments/fa_bss0_run.py --fa-root ../FunctionalArbors --seeds 8 --mutations 28
```

The preliminary four-seed scratch smoke test is recorded under `notes/preliminary_scratch_result.md`; it is explicitly not yet a result.
