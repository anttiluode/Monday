# VISIBLE ARBOR

A browser-visible version of the question Monday reached through ICA/IVA:

> Can persistent branching geometry itself become part of a learned signal transform?

Open `index.html` directly in a browser. No server or dependencies are required.

## Why this branch exists

Aizenbud et al. (PNAS, 2026) quantify how dendritic morphology and synaptic nonlinearities contribute to single-neuron input/output complexity. Their analysis finds that morphology alone contributes substantially to functional complexity, with total dendritic area and features of bifurcation branches among the strongest morphological predictors.

FunctionalArbors asks a different question: not only whether morphology changes computation, but whether local structural remodeling can *learn* useful computation.

Monday's FA-BSS work supplied a particularly clean target. At one frequency a frozen two-terminal arbor can be summarized by a complex transfer vector

`H = [H1, H2]`

so the soma performs

`y = H1*x1 + H2*x2`.

For a known 2x2 source mixture, a particular ratio `H2/H1` cancels one hidden source. That turns "dendritic shape matters" into a measurable structural-learning problem.

## What the HTML demo does

The page intentionally uses a tiny transparent model rather than pretending to be the full FunctionalArbors simulator.

- Two mixed inputs enter two terminals of a branching grid tree.
- The body has a fixed number of cells.
- Each edge contributes attenuation and phase delay at one carrier frequency.
- A proposed mutation replaces one straight degree-2 path cell with a three-cell U-detour.
- The +2-cell cost is paid by pruning two leaves that are not on either terminal-to-soma route.
- The soma accepts a mutation only when source-1 purity improves.
- The current complex ratio `H2/H1` is plotted beside the morphology.

The synthetic mixture is

```text
x1 = 1.0*s1 + 0.65*s2
x2 = 0.4*s1 + 1.0*s2
```

so isolating `s1` requires

```text
H2/H1 = -0.65
```

The toy propagation constants are chosen so six accepted two-edge detours on the second route land exactly on that target. The point is not the number; the point is that the viewer makes the chain visible:

```text
move conserved material
        -> change path geometry
        -> change delay + attenuation
        -> move a complex coefficient
        -> change computation at the soma
```

## What this does NOT establish

This page is a visual executable hypothesis, not a biological model and not a new BSS result.

It does not implement NMDA nonlinearities, realistic cable equations, synaptic plasticity, or the full FunctionalArbors v0.5 wave dynamics. It also uses supervised source purity, so it is not blind ICA/IVA.

The useful next version is to instrument the actual FunctionalArbors FA-BSS experiment to export accepted morphology snapshots and have this viewer replay *real training traces*. After that, the stronger broadband gate is one fixed anatomy attempting to approximate an IVA demixing curve `w(f)` across many frequencies rather than one coefficient at one frequency.

## Reference

Ido Aizenbud, Daniela Yoeli, David Beniaguev, Christiaan P. J. de Kock, Michael London, Idan Segev. **Dendritic morphology and synaptic nonlinearities enhance functional complexity in human cortical neurons.** PNAS 123(28), e2533168123 (2026). DOI: 10.1073/pnas.2533168123.
