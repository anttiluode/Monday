# Why start with one soma

One soma makes the first gate an extraction problem rather than a full decomposition problem.  That matches IVE conceptually: recover one source of interest without requiring a complete set of separated outputs.

It also preserves the existing FunctionalArbors v0.5 architecture.  If one soma cannot learn a useful demixing direction, adding a second soma would only multiply ambiguity.

Only after one-source extraction passes should Monday add two output sites and an independence objective for full blind separation.
