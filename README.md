# Monday

GPT-5.6 Sol thinking repo.

## Current state

Monday started as a source-separation test for [FunctionalArbors](https://github.com/anttiluode/FunctionalArbors). The useful question has become more general:

> **Can persistent structure itself be a learned parameterization of computation?**

The point is not that an arbor *contains* weights. A frozen arbor is a physical/dynamical object whose geometry produces a transfer function. With two terminals and one soma, at angular frequency `omega` its small-signal response is

```text
y(omega) = H1(omega) x1(omega) + H2(omega) x2(omega)
```

Changing morphology changes `H1`, `H2`, and therefore changes the computation performed by the body.

That gives Monday a sharper organizing idea:

```text
experience / target pressure
        -> structural remodeling
        -> one persistent body
        -> a coupled family of transfer coefficients H(omega)
        -> future computation
```

The interesting constraint is that **one anatomy produces the whole curve**. It cannot choose an unrelated coefficient independently at every frequency. Geometry therefore acts as a compressed, physically coupled parameterization of an operator.

## What has actually survived

### FA-BSS0 — synthetic one-frequency capability

A fixed-mass FunctionalArbor can be structurally remodeled so its measured complex terminal-to-soma transfer moves toward a known inverse-mixing coefficient. This separates two questions that are often confused:

1. **Representability:** can legal morphology realize the required operator?
2. **Learning/search:** can a plausible local rule find it?

FA-BSS0 is supervised. It establishes neither blind ICA nor neurobiology.

### FA-BSS-REAL0 — real sensor coefficient compile

A real simultaneous SM58 + guitar-pickup recording was separated with digital references. FastICA mostly rediscovered the already-different sensor axes; AuxIVA produced frequency-dependent complex combinations.

At 602.93 Hz, one AuxIVA row had approximately

```text
w = [0.086 - 0.806j, 1.004 + 0.004j]
w1/w0 ~= 0.126 + 1.232j
```

Four existing v0.5 FunctionalArbor morphologies were then asked to approach that complex direction using only legal mass-conserving detour/prune mutations. Three moved substantially closer; the best seed reduced projective error from about 39.8 degrees to 16.1 degrees.

This is a **compile / representational result**, not blind source separation.

The exploratory one-bin fourth-cumulant objective failed and is killed. Increasing one-bin non-Gaussianity did not reliably move the body toward a useful source separator.

See [`notes/fa_bss_real0_result.md`](notes/fa_bss_real0_result.md).

### Visible Arbor

[`visible_arbor/`](visible_arbor/) is a deliberately transparent browser model of the idea:

```text
move conserved material
        -> change path geometry
        -> change delay + attenuation
        -> move a complex coefficient
        -> change computation at the soma
```

It is explanatory, not evidence beyond the experiments above.

## The next hard gate: one body, many frequencies

One-frequency compilation can still be dismissed as an eccentric way to store one complex number.

The stronger test is broadband:

> **Can one fixed anatomy approximate a frequency-dependent demixing curve learned by IVA across many frequencies at once?**

Digital IVA has a demixing vector `w(f)` at every frequency bin. One arbor has one geometry and therefore one coupled transfer curve `H(omega)`. If a small number of structural degrees of freedom can move that whole curve toward a useful broadband operator, morphology is doing something more interesting than acting as a scalar weight container.

The first broadband gate is still supervised. It is explicitly a test of structural expressivity and coupling before blind local learning.

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

These works make it incorrect to say that dendrites + BSS is an unexplored combination. Their learned quantities are primarily synaptic/recurrent parameters or compartmental dynamics. Monday's narrower seam is **learning the transfer function by changing the morphology itself**.

### ICA / IVA / convolutive BSS

- Miro Arvila, Klaus Nordhausen, Mika Sipila, Sara Taskinen. **Independent vector analysis — an introduction for statisticians.** arXiv:2506.16175 (2025). https://arxiv.org/abs/2506.16175
- Ruiming Guo, Zhongqiang Luo, Mingchun Li. **A Survey of Optimization Methods for Independent Vector Analysis in Audio Source Separation.** Sensors 23, 493 (2023). https://doi.org/10.3390/s23010493

## Claims we are NOT making

- Dendrites do ICA.
- Blind source separation is the foundation of perception.
- FunctionalArbors currently performs blind source separation.
- Monday explains why biological dendrites exist.
- A browser tree that reaches a target is evidence of neurobiology.

The defensible research hypothesis is narrower:

> **Local structural plasticity under a constrained material budget may be able to learn morphology whose physical broadband transfer function performs a useful signal transform.**

A stronger result would be:

> **One structured body can parameterize a useful high-dimensional operator with fewer independent degrees of freedom because its apparent coefficients are coupled consequences of the same geometry.**

That is what the next gates are for.

## Repository map

- [`experiments/`](experiments/) — executable gates and baselines.
- [`notes/`](notes/) — contracts, results, killed ideas, and interpretation.
- [`visible_arbor/`](visible_arbor/) — browser-visible explanatory model.
- [`Wav/`](Wav/) — the first real simultaneous sensor recording used by REAL0.

## Current branch discipline

Earlier work lived on `fa-bss0` and `visible-arbor`. Their history has now been fast-forwarded into `main`. New gates should branch from this consolidated state and return to `main` only after their result is understood and documented.
