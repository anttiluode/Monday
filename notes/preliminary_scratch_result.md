# Preliminary scratch result (not yet the committed gate run)

Before wiring the full experiment into Monday, I reproduced the FunctionalArbors v0.5 transport/remodeling logic in a local scratch test and replaced the old delay contrast with an analytic small-signal transfer-function score at the carrier.

One fixed example used `A = [[1.0, 0.65], [0.4, 1.0]]`, whose exact one-soma cancellation ratio for source 1 is `H2/H1 = -0.65`.

Across four bootstrap seeds with 20 structural proposals per arm, the supervised greedy reward arm moved target-source purity as follows:

- seed 0: 0.727 -> 0.838; matched shuffle ended 0.590
- seed 1: 0.135 -> 0.277; matched shuffle ended 0.204
- seed 2: 0.823 -> 0.965; matched shuffle ended 0.486
- seed 3: 0.557 -> 0.823; matched shuffle ended 0.767

That was already enough to reject an immediate "the morphology cannot alter the demixing direction" failure, but seed 1 looked poor.  I then ran an unrewarded random walk through legal detour/prune morphologies for each of the same four bootstrap seeds, measuring the complex transfer ratio after every move.  Best sampled purities were:

- seed 0: 0.9568, ratio about `-0.480 - 0.023j`
- seed 1: 0.9960, ratio about `-0.638 + 0.046j`
- seed 2: 0.9702, ratio about `-0.518 - 0.043j`
- seed 3: 0.9950, ratio about `-0.664 + 0.050j`

That changes the diagnosis.  In this tiny sample, even the bad greedy seed had excellent demixing morphologies reachable by the existing legal mutation vocabulary.  The immediate bottleneck therefore looks more like **search / credit assignment / local trapping** than raw representational expressivity.

This is still **only a smoke signal, not a result**.  It used one hand-picked mixing matrix, four seeds, short walks, and a linearized steady-state transfer score.  The committed gate must be run independently and then repeated over a predeclared bank of mixing matrices.

A useful technical finding from the scratch work: the linearized discrete-time wave equations admit a direct sparse frequency-domain solve for terminal-to-soma gain.  This is much faster and cleaner than waiting hundreds of simulation frames for a driven tone to settle.  Long direct tone simulations matched the important gain ratio after transients decayed.
