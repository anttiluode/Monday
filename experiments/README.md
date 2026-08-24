# Experiments

## FA-BSS0 — supervised structural source extraction

Question: can a mass-conserving, finite-speed FunctionalArbor reshape its geometry so a single soma output preferentially recovers one latent source from two observed mixtures?

Gate:

1. Generate two independent, non-Gaussian, same-band latent sources `s1`, `s2`.
2. Hide them behind a fixed invertible 2x2 mixing matrix to obtain `x1`, `x2`.
3. Inject only `x1`, `x2` at the two arbor terminals.
4. Let real wave transport produce local eligibility, then use the existing v0.5 local detour/prune mutation mechanism unchanged.
5. During this first capability gate only, accept a mutation when target-source purity improves.
6. Freeze anatomy and score fresh source realizations.
7. Independently solve the frozen morphology's small-signal carrier response to measure complex terminal-to-soma gains `H1,H2`; verify that `H @ A` explains the source isolation.
8. Compare against FastICA and exact matrix inversion as calibration baselines, plus matched reward-shuffle/anti-reward morphology controls.

Run:

```bash
python experiments/fa_bss0_run.py --fa-root ../FunctionalArbors --seeds 8 --mutations 28
```

Success is not a pretty arbor. Success is frozen-anatomy source recovery plus a measured physical transfer function that explains it.

## FA-BSS0 reachability

The first implementation exposed a sharper prior question: **can legal v0.5 morphologies even realize the complex demixing ratio needed by a given mixture?**

`fa_bss0_reachability.py` performs unrewarded random walks through the same detour/prune mutation space while measuring `H2/H1` after every legal move.

```bash
python experiments/fa_bss0_reachability.py --fa-root ../FunctionalArbors --seeds 4 --steps 50
```

This is a sampled reachable set, not a proof of the complete set. If excellent demixing ratios appear in the random walk but supervised greedy learning fails to find them, the bottleneck is search/credit assignment rather than raw morphological expressivity.

Do not move to blind ICA/IVE-style objectives until this supervised gate and its reachability diagnosis are understood.
