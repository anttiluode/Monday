# Experiments

## FA-BSS0

Question: can a mass-conserving, finite-speed FunctionalArbor reshape its geometry so a single soma output preferentially recovers one latent source from two observed mixtures?

Planned gate:

1. Generate two independent, non-Gaussian, same-band latent sources `s1`, `s2`.
2. Hide them behind a fixed invertible 2x2 mixing matrix to obtain `x1`, `x2`.
3. Inject only `x1`, `x2` at the two arbor terminals.
4. Let real transport produce local eligibility, then use the existing local detour/prune mutation mechanism.
5. During this first capability gate only, accept a mutation when held-out source-purity improves.
6. Freeze anatomy and compare against a direct two-weight linear unmixing optimum and FastICA.
7. Probe each terminal with an impulse to measure the learned physical transfer functions.

Success is not a pretty arbor. Success is held-out source recovery plus an independently measured transfer function that explains it.

Failure is useful: if a direct linear unmixing solution exists but the arbor cannot approach it, the current geometry/mutation vocabulary is not expressive enough for demixing.
