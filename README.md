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

One anatomy produces the whole curve. It cannot choose an unrelated coefficient independently at every frequency. Geometry is therefore a candidate **compressed, physically coupled parameterization of an operator**.

That is the idea Monday is now trying to kill or preserve.

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

### FA-BSS-REAL1B — one body, many frequencies

REAL1B was the first direct attack on the larger structural-operator interpretation.

One morphology was trained against nine AuxIVA demixing directions spanning approximately 409–2003 Hz, mapped by one fixed global scale into the dimensionless FunctionalArbor frequency axis. The same anatomy had to improve all frequencies together.

The shared body improved in **4/4 seeds**:

```text
mean projective error: 43.64 deg -> 36.11 deg
median fractional improvement: 17.2%
```

But the strongest control killed the big version of the claim:

```text
best single frequency-independent direction: 15.38 deg
```

So the real recording's apparently dramatic complex ratios were misleading. At higher frequencies the AuxIVA rows increasingly point toward roughly the same sensor axis in projective space. One constant direction already explains the target much better than the developed arbor.

Therefore:

```text
representation_pass = false
```

This is an important negative result. **REAL1B did not show that one morphology compactly represents a genuinely difficult broadband demixer better than a simple fixed coefficient.**

A smaller residue survived. When morphology was optimized only on alternating frequencies, unseen interleaved frequencies improved in 3/4 seeds:

```text
held-out mean: 46.46 deg -> 42.10 deg
```

Optimizing a shuffled frequency-to-target assignment produced only weak improvement against the correct curve. Under the pre-registered rule:

```text
coupling_hint = true
```

So one structural change really can move several transfer coefficients together in a target-relevant way. We have operational evidence for **coupling across frequencies**, but not yet evidence that the coupling is a useful compact parameterization compared with ordinary alternatives.

See:

- [`notes/real1b_broadband_contract.md`](notes/real1b_broadband_contract.md)
- [`notes/fa_bss_real1b_result.md`](notes/fa_bss_real1b_result.md)
- [`experiments/fa_bss_real1b_broadband.py`](experiments/fa_bss_real1b_broadband.py)

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

That is stronger than “memory in matter.” The stored history changes the **operator implemented by the matter**.

The question now is whether that coupling ever buys something rather than merely constraining the machine.

The current state is written out in [`notes/state_of_mind_2026-08-24.md`](notes/state_of_mind_2026-08-24.md).

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
- A browser tree that reaches a target is evidence of neurobiology.

The defensible research hypothesis remains:

> **Local structural plasticity under a constrained material budget may be able to learn morphology whose physical broadband transfer function performs a useful signal transform.**

But REAL1B adds an important condition: the target must actually require a nontrivial frequency-dependent direction, and morphology must beat a constant/filter baseline before the larger interpretation earns anything.

## Next hard gate

Do not mine the current real recording for prettier bins. That would be post-hoc target shopping.

Build a **predeclared synthetic convolutive mixture with known FIR source-to-sensor paths** chosen before training so that the exact inverse demixing direction genuinely rotates across frequency.

Then compare:

1. one shared FunctionalArbor body;
2. independent morphology per frequency;
3. best constant complex direction;
4. an ordinary matched FIR/filter parameterization;
5. held-out frequencies;
6. shuffled/reward controls.

Because the hidden sources and FIR paths are known, the exact answer is available for scoring but need not be supplied to a later blind learner.

That gate asks the question REAL1B could not:

> **Does one coherent structure buy a useful coherent family of computations?**

## Repository map

- [`experiments/`](experiments/) — executable gates and baselines.
- [`notes/`](notes/) — contracts, results, killed ideas, and interpretation.
- [`visible_arbor/`](visible_arbor/) — browser-visible explanatory model.
- [`Wav/`](Wav/) — first real simultaneous sensor recording used by REAL0/REAL1B.
- [`.github/workflows/`](.github/workflows/) — reproducible Actions runs for current gates.

## Branch discipline

Earlier work lived on `fa-bss0` and `visible-arbor`; those histories were consolidated into `main`. New discriminating experiments branch from the consolidated state. A branch returns to `main` only after the result, including a negative result, is understood and written down.
