# The continuous objective is simple; the structural neighborhood is the hard part

At one carrier, one-soma morphology is projectively summarized by

`r = H2/H1`.

For real 2x2 mixing matrix

`A = [[a,b],[c,d]]`,

the two hidden-source gains at the soma, up to irrelevant common scale, are

`g1(r) = a + r*c`

`g2(r) = b + r*d`.

The supervised source-1 purity landscape is therefore

`Q(r) = |g1|^2 / (|g1|^2 + |g2|^2)`.

For a nonsingular matrix its exact maximum is obvious: `g2=0`, hence

`r* = -b/d` (when `d != 0`).

So the difficult part of FA-BSS0 is not a mysterious global objective.  In the continuous complex-r plane the destination is explicit.  The difficulty is that FunctionalArbors does not move freely in that plane.  A legal structural action is a discrete detour/prune operation whose effect on `r` depends on the current whole tree.

This explains the preliminary observation that an unrewarded structural random walk can encounter near-perfect ratios while greedy reward learning gets stuck earlier.  The local maxima are maxima on the **mutation graph of morphologies**, not necessarily maxima of the underlying continuous demixing objective.

For equal-kurtosis independent sources the blind fourth-cumulant objective has the analogous form

`J(r) proportional to (|g1|^4 + |g2|^4) / (|g1|^2 + |g2|^2)^2`,

with maxima when either source dominates.  Again, ICA supplies a clean statistical landscape; the unresolved FunctionalArbors problem is how local structural plasticity navigates its constrained projection of that landscape.
