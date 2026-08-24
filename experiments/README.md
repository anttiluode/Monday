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
python experiments/fa_bss0_run_fast.py --fa-root ../FunctionalArbors --seeds 8 --mutations 28
```

Success is not a pretty arbor. Success is frozen-anatomy source recovery plus a measured physical transfer function that explains it.

## FA-BSS0 reachability

The first implementation exposed a sharper prior question: **can legal v0.5 morphologies even realize the complex demixing ratio needed by a given mixture?**

`fa_bss0_reachability.py` performs unrewarded random walks through the same detour/prune mutation space while measuring `H2/H1` after every legal move.

```bash
python experiments/fa_bss0_reachability.py --fa-root ../FunctionalArbors --seeds 4 --steps 50
```

This is a sampled reachable set, not a proof of the complete set. If excellent demixing ratios appear in the random walk but supervised greedy learning fails to find them, the bottleneck is search/credit assignment rather than raw morphological expressivity.

## FA-BSS-REAL0 — Two Ears recording -> real demixing coefficient -> anatomy

The branch now contains the first physical recording pair in `Wav/`:

- `two_ears_in0.wav` — microphone / XLR
- `two_ears_in1.wav` — guitar pickup / instrument input

`fa_bss_real0.py` does three things, in that order:

1. **Diagnose the recording itself.** It measures cross-channel lag/correlation, frequency-dependent coherence, and spectral asymmetries so we can tell whether this is a real shared-mixture problem or merely two already-disjoint sensors.
2. **Fit digital reference separators.** FastICA is the instantaneous attacker; AuxIVA is the frequency-dependent/convolutive reference. With no ground-truth sources in a live recording, channel signatures and frozen/intervention recordings are diagnostics, not proof by themselves.
3. **Compile one real AuxIVA demixing row into FunctionalArbor morphology.** The strongest pickup-associated AuxIVA STFT bin supplies a two-complex-number target `w=[w0,w1]`. Existing legal v0.5 morphology is then asked whether its measured physical transfer vector `H=[H0,H1]` can approach that direction. This is a supervised real-data capability test, not yet blind learning. A blind fourth-cumulant arm is printed only as an exploratory comparison.

Run from Monday with FunctionalArbors checked out beside it:

```bash
python experiments/fa_bss_real0.py --fa-root ../FunctionalArbors
```

It writes `fa_bss_real0.json` and prints the useful summary. The decisive fields are:

- `median_coherence_40_10k` / `p95_coherence_40_10k`: whether the sensors share structured content;
- AuxIVA `channel_signature`: whether recovered components actually have different sensor footprints;
- `audio_bin` target ratio: the real-data digital demixing coefficient selected for compilation;
- FunctionalArbor `start -> teacher` projective error and `auxiva_bin_corr`: whether anatomy moved toward and reproduced the real digital demixer;
- blind-arm kurtosis and AuxIVA-bin correlation: whether a source-label-free statistical pressure happens to move in the same direction.

Important limitation: TWO EARS currently saves each mono input with its own peak normalization. That loses the original physical inter-channel gain calibration, although invertible per-sensor scaling does not destroy the BSS problem itself. Future recordings should also save one untouched stereo/raw pair.

Do not move to broad claims about live blind anatomical source separation until the supervised synthetic gate, the real-data coefficient compile, and a frozen causal intervention recording all agree.
