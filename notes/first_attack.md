# First attack: does anatomy become an unmixing filter?

The tempting claim is too broad: "FunctionalArbors can do ICA."  The first attack narrows it.

A 2x2 instantaneous mixture has a trivial digital inverse.  Therefore FA-BSS0 is not a benchmark where the arbor should beat ICA.  It is an expressivity test: can local, mass-conserving changes to a finite-speed wave medium physically realize enough of that inverse to isolate one source at a soma?

Important controls:

- sources overlap spectrally so a simple frequency split cannot solve the task;
- train/test episodes use fresh source realizations under the same mixing matrix;
- score the frozen anatomy on held-out episodes;
- compare to a two-weight linear least-squares demixer and FastICA;
- run reward-shuffle and anti-reward structural controls as in FunctionalArbors v0.5;
- measure terminal-to-soma impulse responses after training rather than inferring mechanism from geometry;
- repeat across mixing matrices and seeds.

The most likely failure mode is representational: the current binary tree plus positive fixed material may only supply restricted complex coefficients through path delay/interference.  If so, the correct next change is not more mutations; it is to characterize the reachable transfer-function family first.

That characterization may become the real result: map geometry -> complex two-input transfer vector H(f), then ask which ICA/IVE demixing vectors lie inside the reachable set.
