# Monday

GPT-5.6 Sol thinking repo.

**Status: paused and consolidated, 2026-08-24.**

Monday began when a source-separation detour collided with [FunctionalArbors](https://github.com/anttiluode/FunctionalArbors). It ended up doing two related things:

1. using ICA / IVA / IVE as a much cleaner language for an old recurring question — *what hidden causes are inside a mixture, which ones correspond across views, and which one matters now?*;
2. asking one deliberately strange follow-up — *can a persistent physical structure itself embody part of the learned unmixing operator?*

The second question produced the experiments in this repo. The first is probably the larger reason Monday was worth doing.

## The larger turn: mixtures -> causes

A lot of earlier work had tried to make hidden structure visible with phase, resonators, Fourier banks, fields, latent directions, geometry, or custom adaptive media. BSS gives a more disciplined middle problem:

```text
many latent causes
        ↓
observed mixtures
        ↓
ICA      separate independent-ish causes
IVA      keep corresponding causes tied across views / frequency bins
JISA     allow a cause to be a dependent subspace
IVE      extract only the source of interest
Dynamic  keep doing it while the mixing changes
```

This is not a theory of intelligence. It is useful mathematics for a very basic perceptual problem:

> **Many causes are superposed in my measurements. Which cause is which, which combinations belong together, and which one matters now?**

That framing connects cleanly to several older repo themes without requiring their mythology:

- latent-space trajectories can be attacked with ICA instead of only PCA;
- IVA can ask whether controls or sources correspond across different identities, sensors, subjects, or models despite different local coordinate systems;
- IVE makes “only extract what matters now” a concrete algorithmic operation rather than a metaphor;
- dynamic IVA/IVE gives a mature reference for moving sources and changing mixtures.

A particularly promising non-Monday direction is automatic latent rigging: learn motion trajectories in several generated identities, use ICA/JISA to find candidate control factors inside each, and IVA to ask whether yaw, mouth, expression, etc. correspond across identities even when each model has a different local basis. Monday does not implement that. It simply left the door visibly open.

## Why FunctionalArbors entered the story

A frozen FunctionalArbor is a little wave-carrying body. With two terminals and one soma, its small-signal response at frequency `omega` is approximately

```text
y(omega) = H1(omega) x1(omega) + H2(omega) x2(omega)
```

The complex gains `H1`, `H2` are consequences of path geometry, attenuation, and delay. Remodeling the body therefore changes the arithmetic performed at the soma.

That suggested a deliberately concrete question:

> **Can legal structural remodeling make one persistent anatomy approximate a demixing operator?**

The point was not “dendrites do ICA.” The point was to distinguish:

- **representability** — can the body realize a useful operator at all?;
- **learning/search** — can an unsupervised or local rule actually find it?;
- **structural coupling** — does one body impose useful relationships across many apparent coefficients?

## What the experiments actually established

### FA-BSS0 — one synthetic coefficient

A fixed-mass arbor could be remodeled so its measured complex terminal-to-soma transfer moved toward a known inverse-mixing coefficient.

This was a supervised capability result. It showed that morphology could embody a coefficient; it did **not** show blind ICA or biological source separation.

### FA-BSS-REAL0 — one coefficient learned elsewhere, compiled into anatomy

A simultaneous SM58 + guitar-pickup recording was analyzed with digital separators. AuxIVA produced genuinely complex frequency-dependent demixing directions. At 602.93 Hz one row was approximately

```text
w = [0.086 - 0.806j, 1.004 + 0.004j]
```

Legal FunctionalArbor remodeling moved 3/4 starting morphologies substantially closer to that direction; the best seed improved from about 39.8 degrees projective error to 16.1 degrees.

Again: this was **compile / representability**, not blind source separation.

The first attempted blind learner — one-bin fourth-order non-Gaussianity — failed. It could happily increase kurtosis while walking away from the AuxIVA source. That route is killed.

See [`notes/fa_bss_real0_result.md`](notes/fa_bss_real0_result.md).

### FA-BSS-REAL1B — one body, several real frequency bins

One shared morphology was trained against nine AuxIVA directions from the real recording.

```text
shared-body mean error: 43.64 -> 36.11 deg
best constant direction: 15.38 deg
representation_pass = false
```

The body moved the whole response curve, but the target was much easier than it first looked: a single frequency-independent direction beat the arbor badly.

A smaller effect survived. Training only alternating frequencies improved unseen interleaved frequencies in 3/4 seeds:

```text
held-out mean: 46.46 -> 42.10 deg
coupling_hint = true
```

So one structural mutation really does move multiple frequency coefficients together. REAL1B did not show that this coupling was useful enough to justify the representation.

See [`notes/fa_bss_real1b_result.md`](notes/fa_bss_real1b_result.md).

### FA-BSS-CONV0 — controlled rotating demixer

CONV0 removed the REAL1B loophole with a synthetic convolutive world whose exact source-1 demixing direction genuinely rotates across frequency:

```text
x1[t] = s1[t] + 0.90*s2[t-14]
x2[t] = 0.35*s1[t-3] + s2[t]

w(omega) = [1, -0.90 exp(-i14omega)]
```

The best constant direction scored 31.38 degrees, so the target was genuinely frequency-dependent.

The shared body improved in all four seeds:

```text
mean: 50.52 -> 33.33 deg
median fractional improvement: 34.7%
```

But the predeclared representation criterion required at least 3/4 seeds to beat the constant attacker. Only 2/4 did:

```text
rotating_representation_pass = false
```

The held-out-frequency result was stronger. Training only frequencies `0,2,4,6,8` improved unseen `1,3,5,7` in 4/4 seeds:

```text
held-out mean: 49.88 -> 38.28 deg
median held-out improvement: 12.18 deg
heldout_coupling_pass = true
```

Reversing the frequency ordering of the same target vectors produced much less useful movement against the correct curve.

This is the strongest surviving FunctionalArbor result in Monday:

> **One persistent geometry imposes learnable cross-frequency coupling: mutations selected at some frequencies can move unseen frequencies in a target-relevant direction, and the ordering of the target across frequency matters.**

But the boring exact FIR remains essentially perfect on CONV0. Monday did not discover a better filter.

See [`notes/fa_bss_conv0_result.md`](notes/fa_bss_conv0_result.md).

## What survived, in plain language

The strongest claim did **not** survive.

Monday did not show that morphology beats conventional filtering, performs blind BSS, or explains dendrites.

What survived is smaller and more reusable:

```text
one persistent structure
        ↓
generates many effective coefficients together
        ↓
a local structural change moves the whole operator coherently
        ↓
some of that movement generalizes to frequencies not used for selection
```

So the useful idea is not “a tree is an ICA matrix.” It is:

> **A structure can be a low-dimensional generator of a larger family of mutually constrained computations.**

Whether those constraints are an advantage or merely a handicap remains open.

## What Monday was trying to connect

Looking backward, the repo sits at the intersection of two recurring ideas.

The first is source separation:

```text
world of mixtures
      -> recover latent causes
      -> align them across views
      -> extract the one that matters
```

The second is persistent organization:

```text
experience
      -> changes a durable operator
      -> future signals are processed differently
```

FunctionalArbors was one unusually literal test of the second idea: instead of updating an abstract scalar weight, rearrange conserved structure and let the resulting physics generate the effective coefficients.

That is why ICA/IVA/IVE mattered here even though the repo became arbor-heavy. They supplied a rigorous target family and good attackers. The arbor was a contestant, not the theory.

## Claims explicitly not made

- dendrites do ICA;
- Monday explains why dendrites exist;
- FunctionalArbors currently performs blind source separation;
- REAL1B or CONV0 demonstrated a superior broadband representation;
- structural morphology beats an ordinary matched FIR;
- source separation is a complete theory of perception or intelligence;
- the Visible Arbor browser demo is biological evidence.

The attached neuroscience literature already places source separation, local plasticity, and dendritic computation close together. Monday's narrower experimental seam was structural remodeling of the transfer function itself.

## Visible Arbor

[`visible_arbor/`](visible_arbor/) is the browser-visible explanation of the simplest mechanism:

```text
move conserved material
        -> change path geometry
        -> change delay + attenuation
        -> move a complex coefficient
        -> change soma computation
```

It is a visualization of the hypothesis, not additional evidence.

## Where this repo stops

There is an obvious next structural gate: use a predeclared multi-tap convolutive target that defeats a constant direction and a one-delay model, then compare the shared body with matched compact digital parameterizations.

Monday is deliberately **not** doing that now.

The current result is enough to close the loop:

- a body can embody a learned complex coefficient;
- one body can move a broadband family of coefficients together;
- cross-frequency structural coupling survives held-out tests;
- the current morphology does not reliably beat simpler digital representations;
- the first blind local objective failed;
- ICA / IVA / IVE remain more valuable as general tools than as decoration around the arbor.

If this repo is reopened, the first question should therefore be **what concrete task benefits from the coupling**, not how to make a more elaborate tree.

## Repository map

- [`experiments/`](experiments/) — executable FA-BSS gates and controls.
- [`notes/`](notes/) — contracts, results, warnings, killed routes, and interpretation.
- [`visible_arbor/`](visible_arbor/) — self-contained browser explanation.
- [`Wav/`](Wav/) — simultaneous sensor recording used by REAL0 / REAL1B.
- [`.github/workflows/`](.github/workflows/) — reproducible Actions runs.

## Literature map

- Ido Aizenbud et al. **Dendritic morphology and synaptic nonlinearities enhance functional complexity in human cortical neurons.** PNAS (2026). https://doi.org/10.1073/pnas.2533168123
- Toshitake Asabuki, Tomoki Fukai. **Somatodendritic consistency check for temporal feature segmentation.** Nature Communications (2020). https://doi.org/10.1038/s41467-020-15367-w
- Giorgia Dellaferrera, Toshitake Asabuki, Tomoki Fukai. **Modeling the Repetition-Based Recovering of Acoustic and Visual Sources With Dendritic Neurons.** Frontiers in Neuroscience (2022). https://doi.org/10.3389/fnins.2022.855753
- Bariscan Bozkurt et al. **Normative Networks for Source Separation via Local Plasticity and Dendritic Computation.** arXiv:2605.19965 (2026). https://arxiv.org/abs/2605.19965
- Miro Arvila et al. **Independent vector analysis — an introduction for statisticians.** arXiv:2506.16175 (2025). https://arxiv.org/abs/2506.16175
- Ruiming Guo, Zhongqiang Luo, Mingchun Li. **A Survey of Optimization Methods for Independent Vector Analysis in Audio Source Separation.** Sensors 23, 493 (2023). https://doi.org/10.3390/s23010493

---

Monday is left as a record of a useful collision: **source separation gave the old “hidden causes in mixtures” obsession a mature mathematical language, while FunctionalArbors supplied one concrete test of whether experience can be compiled into persistent structure.** The structural result is modest. The broader toolbox is probably the part worth carrying forward.
