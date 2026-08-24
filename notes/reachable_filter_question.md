# Reachable filter question

For a frozen arbor at one carrier frequency, probe terminal 1 and terminal 2 separately and estimate the complex soma gains

`H = [H1, H2]`.

For a fixed source mixing matrix `A`, the hidden-source gains are

`G = H @ A`.

If source 1 is the desired source, a supervised purity score can be

`Q = |G1|^2 / (|G1|^2 + |G2|^2 + eps)`.

The ideal instantaneous demixing row is the first row of `inv(A)`, up to arbitrary nonzero complex scale.  Therefore FA-BSS0 can measure not just source recovery but whether the physical transfer vector `H` moves toward that ideal direction.

This reframes the first experiment.  We do not need to claim that the arbor "runs ICA."  We ask whether local morphology can move the medium through a useful family of complex demixing vectors.

A likely decisive diagnostic is to sample many legal arbor geometries and plot their normalized `H1/H2` values in the complex plane.  If the ideal ratio required by `inv(A)` lies outside that reachable cloud, learning cannot succeed regardless of the mutation rule.  If it lies inside but learning does not reach it, the problem is search/credit assignment instead of expressivity.
