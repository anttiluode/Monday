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

## PIPE-OJA-BRANCH0

Work is on branch `oja-pipe-branching` under [`pipe_oja/`](pipe_oja/).

This gate reconnects Monday to the earlier **self-normalizing pipe** idea. Structural resource is a non-negative mass budget. Local pipe signal is paired with a nonlinear broadband soma score; after every update, the same fixed amount of mass is redistributed rather than created.

The adversarial comparison is deliberately simple:

- same two mixed inputs;
- same whitening front end;
- same initial two direct pipes;
- same total mass `sum(m)=1`;
- same blind broadband gradient;
- `cable`: exactly one delay route per sensor;
- `branch`: mass may split over several delay routes;
- `branch_shuffle`: same branching freedom, but local pipe current is paired with a time-shuffled soma score.

The default eight-seed run gives mean hidden-source purity `0.9448` for branching, `0.6645` for the cable, and `0.5654` for shuffled branching. The independently searched supervised capacity ceiling of the entire single-path family is only `0.8325`; every learned branch exceeds its matched cable ceiling. Paired exact sign-flip tests give `p=0.00781` for both branch-vs-cable and branch-vs-shuffle.

That is a result for the declared toy, not yet for FunctionalArbors. The point is narrower: **branching finally earns a computational role that cannot be reduced to stretching one delay line.**

Run:

```bash
python pipe_oja/run.py
```

Open [`pipe_oja/index.html`](pipe_oja/index.html) directly to scrub through seed 0 and watch fixed structural mass split into several delay routes.

The next gate ports this exact single-path-vs-free-branch comparison into the real FunctionalArbors wave body.
