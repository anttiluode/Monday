# Where ICA slots in

ICA is not embedded inside the arbor in Gate 0.

It has three jobs:

1. **Calibration baseline** — prove the synthetic mixtures are separable by the expected linear method.
2. **Coordinate system** — the ideal ICA/analytic demixing vector gives a target direction against which the arbor's measured complex transfer vector can be compared.
3. **Later blind objective** — only after supervised structural extraction works do we replace the answer-key score with an independence/non-Gaussianity criterion.

This separation matters.  Otherwise a digital ICA front-end could do all the useful work and leave the arbor decorative.
