# State of mind — 2026-08-24

## The shift

Monday began as "can FunctionalArbors do source separation?"

That was too narrow and, in one sense, too easy to misunderstand. At one frequency, a frozen two-terminal arbor is just a little linear complex combiner:

```text
y = H1*x1 + H2*x2
```

If morphology can move `H2/H1` toward a desired value, we have shown that geometry can implement a learned coefficient. Interesting, but still vulnerable to the criticism: **this is an eccentric weight.**

IVA sharpened the question.

A convolutive separator has a frequency-dependent demixing vector `w(f)`. A digital algorithm may hold a different complex coefficient at every frequency. A physical arbor does not get a new anatomy for each Fourier bin. It has one body, and that one body generates an entire transfer curve `H(omega)`.

So the new object of interest is not a coefficient.

It is the map

```text
structural state theta
        -> H(omega; theta)
        -> a whole family of coupled computations
```

The body's apparent "weights" across frequency are not independently free. They are consequences of the same geometry.

## The hypothesis worth defending

> A learned structure can be a compressed parameterization of a high-dimensional operator because many effective coefficients are coupled consequences of one physical organization.

For FunctionalArbors this becomes:

> Can a constrained, mass-conserving morphology be remodeled so that its *whole transfer function* approximates a useful broadband demixing operator?

This is not yet a biological claim. It is a machine-organization question.

## Why this matters beyond an arbor

Conventional learning usually treats the adjustable object as a collection of numerical parameters. Monday asks about a different organization:

```text
experience
   -> changes a persistent generative structure
   -> that structure determines many future coefficients at once
   -> future computation inherits those constraints automatically
```

This is stronger than "memory in matter." The stored history changes the **operator implemented by the matter**.

The attractive possibility is that a comparatively small developmental/structural state can specify a much larger family of effective computations. Physics, topology, recurrence, or another structured generator supplies the coupling that would otherwise have to be learned coefficient-by-coefficient.

## What is already evidence, and what is not

### Evidence we have

1. FunctionalArbors v0.5 has genuine finite-speed wave transport and persistent mass-conserving morphology.
2. Frozen morphology has a measurable complex terminal-to-soma transfer vector.
3. Legal structural mutations can move that transfer vector toward a known synthetic inverse-mixing coefficient.
4. In REAL0, legal morphology moved toward a strongly complex coefficient learned independently by AuxIVA from a real two-sensor recording.
5. The one-bin blind fourth-cumulant objective failed. We therefore do not currently have blind anatomical BSS.

### We do not have

1. Broadband compilation by one shared anatomy.
2. Evidence that morphology beats or regularizes against a matched numerical filter.
3. A local blind learning rule that discovers the broadband separator.
4. A causal physical intervention that names the recovered real-audio components.
5. Evidence that biological dendrites use structural plasticity for BSS.

## The literature seam

The surrounding boxes already exist.

- Morphology contributes to neuronal functional complexity: Aizenbud et al. 2026.
- Dendritic/compartmental neuron models can learn temporal features and source separation: Asabuki & Fukai 2020; Dellaferrera et al. 2022.
- Source-separation objectives can yield biologically local synaptic and lateral plasticity with dendritic error computation: Bozkurt et al. 2026.
- IVA provides the broadband/multi-view source-separation framework and IVE provides extraction of a source of interest.

So the defensible seam is **not** "dendrites + source separation."

It is:

```text
source-separation pressure
        +
structural plasticity under a material constraint
        ->
learned morphology
        ->
learned physical transfer function
```

The learned parameter is the morphology itself.

## The next gate must discriminate

The next gate should make the one-body constraint unavoidable.

Take an AuxIVA demixing curve from several informative frequency bins. Map those bins onto a fixed normalized internal frequency grid. Then ask one FunctionalArbor morphology to reduce projective error across the whole curve using the same legal detour/prune operations.

Important controls:

1. **Best constant complex vector.** If one coefficient is already enough, broadband morphology adds nothing.
2. **Independent-body per-frequency oracle.** Let every frequency have its own morphology. This estimates how much error comes specifically from forcing one body to satisfy all bins.
3. **Held-out frequencies.** Train morphology on alternating frequency points and score the points it never saw. If held-out points improve, that is evidence that structural coupling supplies useful interpolation rather than independent memorization.
4. **Random/reward-shuffled remodeling.** Morphology must beat accidental movement through reachable space.

The broadband test is still supervised. Its purpose is to answer the representational question first:

> Does one coherent structure actually buy a coherent family of useful computations?

Only if that survives should we return to blind local objectives.

## Red line for interpretation

If the shared body cannot approach the broadband target, or if independent numerical coefficients dominate at the same effective parameter budget, then the large interpretation shrinks.

If it can, the interesting sentence is not "we found why dendrites exist."

It is:

> **Instead of repeatedly calculating a recurring family of transformations, a system may learn a persistent structure whose dynamics instantiate that family directly.**
