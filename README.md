# Monday

GPT-5.6 Sol thinking repo.

## Current question

Monday started as a source-separation test for [FunctionalArbors](https://github.com/anttiluode/FunctionalArbors). The useful question has become more general:

> **Can persistent structure itself be a learned parameterization of computation?**

The point is not that an arbor *contains* weights. A frozen arbor is a physical/dynamical object whose geometry produces a transfer function. With two terminals and one soma, at angular frequency `omega` its small-signal response is

```text
y(omega) = H1(omega) x1(omega) + H2(omega) x2(omega)
```

Changing morphology changes `H1`, `H2`, and therefore changes the computation performed by the body.

The organizing picture is now:

```text
experience / target pressure
        -> structural remodeling
        -> one persistent body
        -> a coupled family of transfer coefficients H(omega)
        -> future computation
```

One anatomy produces the whole curve. It cannot choose an unrelated coefficient independently at every frequency. Geometry is therefore a candidate **physically coupled parameterization of an operator**.

The current evidence says the coupling is real. It has **not** yet shown that this coupling is a superior or reliably useful representation.

## Result ladder

### FA-BSS0 — one-frequency synthetic capability

A fixed-mass FunctionalArbor can be structurally remodeled so its measured complex terminal-to-soma transfer moves toward a known inverse-mixing coefficient.

This separated two questions that had previously been mixed together:

1. **Representability:** can legal morphology realize the required operator?
2. **Learning/search:** can a plausible local rule find it?

FA-BSS0 is supervised. It establishes neither blind ICA nor neurobiology.

### FA-BSS-REAL0 — compile one real complex coefficient

A simultaneous SM58 + guitar-pickup recording was analyzed with FastICA and AuxIVA. FastICA mostly rediscovered the already-different sensor axes. AuxIVA produced frequency-dependent complex combinations.

At 602.93 Hz, one AuxIVA row had approximately

```text
w = [0.086 - 0.806j, 1.004 + 0.004j]
w1/w0 ~= 0.126 + 1.232j
```

Four existing v0.5 FunctionalArbor morphologies were asked to approach that complex direction using only legal mass-conserving detour/prune mutations. Three moved substantially closer; the best seed reduced projective error from about 39.8 degrees to 16.1 degrees.

This is a **compile / representational result**, not blind source separation.

The exploratory one-bin fourth-cumulant objective failed and is killed. Increasing one-bin non-Gaussianity did not reliably move the body toward a useful source separator.

See [`notes/fa_bss_real0_result.md`](notes/fa_bss_real0_result.md).

### FA-BSS-REAL1B — first broadband attack

REAL1B trained one morphology against nine AuxIVA demixing directions from the real recording.

The shared body improved in **4/4 seeds**:

```text
mean projective error: 43.64 deg -> 36.11 deg
median fractional improvement: 17.2%
```

But the decisive attacker found that the best single frequency-independent direction already scored:

```text
15.38 deg
```

So the apparently dramatic real AuxIVA ratios mostly collapsed toward a common sensor axis in projective space.

```text
representation_pass = false
```

A smaller residue survived. Training only alternating frequencies improved unseen interleaved frequencies in 3/4 seeds:

```text
held-out mean: 46.46 deg -> 42.10 deg
coupling_hint = true
```

REAL1B therefore provided evidence of cross-frequency coupling but not useful broadband representation.

See:

- [`notes/real1b_broadband_contract.md`](notes/real1b_broadband_contract.md)
- [`notes/fa_bss_real1b_result.md`](notes/fa_bss_real1b_result.md)
- [`experiments/fa_bss_real1b_broadband.py`](experiments/fa_bss_real1b_broadband.py)

### FA-BSS-CONV0 — controlled rotating synthetic demixer

CONV0 removed REAL1B's target ambiguity by freezing a synthetic convolutive world before training:

```text
x1[t] = s1[t] + 0.90 * s2[t - 14]
x2[t] = 0.35 * s1[t - 3] + s2[t]
```

The exact source-1 extraction direction is

```text
w(omega) = [1, -0.90 exp(-i 14 omega)]
```

across nine fixed FunctionalArbor frequencies `0.07 .. 0.35`.

This time the constant-vector hardness control passed before morphology ran:

```text
best constant direction = 31.38 deg
```

The exact matched FIR remained essentially perfect:

```text
y[t] = x1[t] - 0.90*x2[t-14]
error ~= 0 deg
```

One shared body nevertheless learned a substantial part of the rotating curve in every seed:

```text
seed 0   50.65 -> 35.14 deg
seed 1   39.65 -> 35.85 deg
seed 2   50.94 -> 31.18 deg
seed 3   60.86 -> 31.14 deg

mean       50.52 -> 33.33 deg
median fractional improvement = 34.7%
```

But the pre-registered representation criterion required at least 3/4 seeds to beat the 31.38-degree constant attacker. Only 2/4 did:

```text
rotating_representation_pass = false
```

So the strong representation claim still does not pass.

The held-out result was stronger. Training only frequencies `0,2,4,6,8` improved the unseen frequencies `1,3,5,7` in **4/4 seeds**:

```text
held-out mean: 49.88 -> 38.28 deg
median held-out improvement: 12.18 deg
```

Optimizing the same target vectors in reversed frequency order produced only a 4.90-degree median improvement against the correct curve.

```text
heldout_coupling_pass = true
```

This is Monday's strongest surviving result so far:

> **One persistent geometry imposes a learnable coupling across a family of frequency responses: mutations selected at some frequencies can move unseen frequencies in a target-relevant direction, and correct frequency organization matters.**

That still does not show that morphology is a better parameterization than an ordinary filter. The exact FIR wins trivially on CONV0.

See:

- [`notes/conv0_rotating_demixer_contract.md`](notes/conv0_rotating_demixer_contract.md)
- [`notes/fa_bss_conv0_result.md`](notes/fa_bss_conv0_result.md)
- [`experiments/fa_bss_conv0_rotating.py`](experiments/fa_bss_conv0_rotating.py)

### Visible Arbor

[`visible_arbor/`](visible_arbor/) is a deliberately transparent browser model of the one-frequency idea:

```text
move conserved material
        -> change path geometry
        -> change delay + attenuation
        -> move a complex coefficient
        -> change computation at the soma
```

It is explanatory, not evidence beyond the experiments above.

## Current state of mind

The attractive claim is no longer “dendrites do ICA” or “the brain grows a demixer.” Those are too strong and the literature already occupies much of that territory.

The narrower machine-organization hypothesis is:

> **A learned structure can parameterize a family of computations because many effective coefficients are coupled consequences of one persistent organization.**

CONV0 strengthens one half of that sentence: the coupling is operational and can generalize across withheld frequencies.

The unresolved half is the important one:

> **When does structural coupling buy anything rather than merely constrain the machine?**

The stored history changes the **operator implemented by the matter**. Whether that is useful compared with compact conventional parameterizations remains open.

## Why ICA / IVA / IVE are here

These methods are not claimed as theories of intelligence. They give Monday unusually clean mathematical test problems.

- **ICA:** recover statistically independent latent causes from mixtures.
- **IVA:** jointly separate related source vectors across datasets/frequency bins while preserving dependency within each source vector. This naturally addresses the frequency-permutation problem in convolutive separation.
- **IVE:** extract a source of interest without reconstructing everything.

The longer-term question suggested by Monday is not merely whether structure can separate sources, but whether repeated useful extraction can be compiled into persistent structure so future extraction becomes cheaper and more local.

## Literature map

Monday sits between several already-existing research directions. The repo should not claim an empty gap where there is none.

### Dendritic morphology and computational complexity

- Ido Aizenbud, Daniela Yoeli, David Beniaguev, Christiaan P. J. de Kock, Michael London, Idan Segev. **Dendritic morphology and synaptic nonlinearities enhance functional complexity in human cortical neurons.** PNAS (2026). https://doi.org/10.1073/pnas.2533168123

This supports the premise that morphology itself materially contributes to single-neuron input/output complexity. It does **not** establish that dendritic morphology exists to perform source separation.

### Dendritic computation and source separation

- Toshitake Asabuki, Tomoki Fukai. **Somatodendritic consistency check for temporal feature segmentation.** Nature Communications 11, 1554 (2020). https://doi.org/10.1038/s41467-020-15367-w
- Giorgia Dellaferrera, Toshitake Asabuki, Tomoki Fukai. **Modeling the Repetition-Based Recovering of Acoustic and Visual Sources With Dendritic Neurons.** Frontiers in Neuroscience 16:855753 (2022). https://doi.org/10.3389/fnins.2022.855753
- Bariscan Bozkurt, Efe Ali Gorguner, Francesco Innocenti, Rafal Bogacz. **Normative Networks for Source Separation via Local Plasticity and Dendritic Computation.** arXiv:2605.19965 (2026). https://arxiv.org/abs/2605.19965

These works make it incorrect to say that dendrites + BSS is an unexplored combination. Their learned quantities are primarily synaptic/recurrent parameters or compartmental dynamics. Monday's narrower seam is **learning the transfer function by changing morphology itself**.

### ICA / IVA / convolutive BSS

- Miro Arvila, Klaus Nordhausen, Mika Sipila, Sara Taskinen. **Independent vector analysis — an introduction for statisticians.** arXiv:2506.16175 (2025). https://arxiv.org/abs/2506.16175
- Ruiming Guo, Zhongqiang Luo, Mingchun Li. **A Survey of Optimization Methods for Independent Vector Analysis in Audio Source Separation.** Sensors 23, 493 (2023). https://doi.org/10.3390/s23010493

## Claims we are NOT making

- Dendrites do ICA.
- Blind source separation is the foundation of perception.
- FunctionalArbors currently performs blind source separation.
- Monday explains why biological dendrites exist.
- REAL1B demonstrated a superior broadband morphology.
- CONV0 demonstrated a superior broadband morphology.
- Structural morphology beats ordinary FIR filtering.
- A browser tree that reaches a target is evidence of neurobiology.

The defensible hypothesis remains:

> **Local structural plasticity under a constrained material budget may be able to learn morphology whose physical broadband transfer function performs a useful signal transform.**

But the result ladder has made the burden sharper: useful morphology must beat reduced conventional attackers on a target that genuinely requires frequency-dependent computation.

## Next hard gate

CONV0's target is deliberately simple even though it rotates strongly:

```text
ratio(omega) = -0.90 exp(-i14 omega)
```

One gain and one delay generate the whole operator. An ordinary matched FIR therefore solves it exactly with essentially no drama.

The next discriminating target should be a **predeclared multi-tap convolutive mixer**. Before morphology is trained, require all of:

1. the 2x2 FIR mixer is safely invertible across the evaluation band;
2. the best constant demixing direction is poor;
3. the best one-delay / linear-phase demixing model is also poor;
4. the exact ordinary FIR solution is retained as the calibration winner.

Then compare the shared body, independent-body oracle, reduced digital models, held-out frequencies, and wrong-order controls again.

That gate asks a harder version of Monday's surviving question:

> **Can one coherent structure capture useful operator complexity that is not already explained by one scalar direction or one simple delay?**

Do not tune that target after seeing the first morphology result.

## Repository map

- [`experiments/`](experiments/) — executable gates and baselines.
- [`notes/`](notes/) — contracts, results, killed ideas, and interpretation.
- [`visible_arbor/`](visible_arbor/) — browser-visible explanatory model.
- [`Wav/`](Wav/) — first real simultaneous sensor recording used by REAL0/REAL1B.
- [`.github/workflows/`](.github/workflows/) — reproducible Actions runs for current gates.

## Branch discipline

Earlier work lived on `fa-bss0` and `visible-arbor`; those histories were consolidated into `main`. New discriminating experiments branch from the consolidated state. A branch returns to `main` only after the result, including a negative result, is understood and written down.
