# Next code step

Implement `fa_bss0.py` against the actual `FunctionalArbors/v05_free_arbor` transport rather than a new toy medium.

Minimum adapter needed:

- arbitrary two-terminal carrier drive instead of `pulse_source(which, ...)`;
- phasor probe for each terminal to estimate `H1`, `H2`;
- source-purity task using `H @ A`;
- trainer reusing `propose_detour`, snapshot/restore, fixed mass and tree/connectivity checks;
- optional FastICA baseline on generated mixtures.

Keep the original FunctionalArbors mutation vocabulary untouched for Gate 0.  If it fails, first diagnose reachable transfer functions before expanding the morphology language.
