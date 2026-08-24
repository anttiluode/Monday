# Blind one-soma objective: ICA without putting ICA in front of the arbor

After the supervised reachability smoke test, there is a clean source-label-free objective for a one-soma arbor.

Let the frozen morphology have measured complex transfer vector `H=[H1,H2]` and let `X=[x1,x2]` be observed mixture samples.  The candidate soma signal is simply

`y = H @ X`.

For zero-mean `y`, estimate

- `m2 = E[|y|^2]`
- `p2 = E[y^2]`
- `m4 = E[|y|^4]`

and the fourth-order complex cumulant

`c4 = m4 - 2*m2^2 - |p2|^2`.

A scale-free blind score is

`J = |c4| / (m2^2 + eps)`.

For independent non-Gaussian sources, cumulants add while mixed-source power adds quadratically.  A pure independent source therefore has larger normalized fourth-order cumulant than a generic mixture.  The objective does not need the source waveforms or the mixing matrix; it only needs observed mixtures and the morphology's soma output.  It is the one-unit ICA idea in a form that tolerates the arbor's complex transfer coefficients.

The developmental loop would then be:

mixed traffic -> local eligibility -> legal local detour/prune -> frozen soma output -> blind cumulant score -> retain/reject anatomy.

ICA is therefore **the selection criterion, not a preprocessing box**.  If a digital ICA stage first separated the inputs, the arbor would be decorative.

## Tiny scratch attack

Using the same hand-picked matrix as the FA-BSS0 smoke test and 20 greedy structural proposals, I tried this blind cumulant score in the local scratch model.  Final best-source purity (either hidden source counts, because blind ICA has permutation freedom) moved:

- seed 0: 0.727 -> 0.770; matched shuffle happened to reach 0.925
- seed 1: 0.865 -> 0.914; shuffle 0.615
- seed 2: 0.823 -> 0.970; shuffle 0.511
- seed 3: 0.557 -> 0.823; shuffle 0.713

This is not a gate result.  It says only that the blind statistical objective is coupled to useful morphological moves at all.  The same problem seen in supervised Gate 0 remains: greedy structural search often accepts only one move and then traps.  Reachability sampling already showed much better morphologies exist, so the next architectural problem is credit/search rather than inventing a more exotic independence statistic.
