# What a detour means in BSS language

FunctionalArbors v0.5 replaces one straight degree-2 cell by a three-cell U detour and pays the +2 cell cost by pruning weak leaves elsewhere.  At fixed material parameters this does not create an arbitrary learned weight.  It changes path length, delay, attenuation and phase response.

At a chosen carrier frequency, each input terminal therefore contributes a complex coefficient at the soma.  A legal detour is a local move in that complex coefficient space.

This gives a concrete interpretation of structural learning:

- morphology defines the current complex demixing vector;
- wave traffic defines local eligibility (where a legal move may be attempted);
- source-purity or independence defines whether the move is useful;
- retained anatomy is persistent memory of the inverse mixing problem.

The first thing to test is whether the legal local moves span enough coefficient space.  If not, adding a cleverer ICA objective will not rescue the architecture.
