# Preliminary scratch result (not yet the committed gate run)

Before wiring the full experiment into Monday, I reproduced the FunctionalArbors v0.5 transport/remodeling logic in a local scratch test and replaced the old delay contrast with an analytic small-signal transfer-function score at the carrier.

One fixed example used `A = [[1.0, 0.65], [0.4, 1.0]]`.  Across four bootstrap seeds with 20 structural proposals per arm, the supervised reward arm moved target-source purity as follows:

- seed 0: 0.727 -> 0.838; matched shuffle ended 0.590
- seed 1: 0.135 -> 0.277; matched shuffle ended 0.204
- seed 2: 0.823 -> 0.965; matched shuffle ended 0.486
- seed 3: 0.557 -> 0.823; matched shuffle ended 0.767

This is **only a smoke signal**, not a result.  The run was small, used one hand-picked mixing matrix, and the scoring transfer function used a linearized steady-state solve.  It is enough to justify implementing the real gate rather than stopping on an immediate expressivity failure.

A useful technical finding from the scratch work: the linearized discrete-time wave equations admit a direct sparse frequency-domain solve for terminal-to-soma gain.  This is much faster and cleaner than waiting hundreds of simulation frames for a driven tone to settle.  Long direct tone simulations matched the important gain ratio after transients decayed.
