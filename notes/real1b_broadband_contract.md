# FA-BSS-REAL1B contract — one body, many frequencies

## Question

REAL0 showed that legal FunctionalArbor morphology can be moved toward one complex AuxIVA demixing direction.

REAL1B asks the stronger question:

> Can one fixed-mass morphology move toward a *frequency-dependent* AuxIVA demixing curve across several frequencies at once?

This is still a supervised compile test. It does not test blind source separation.

## Why this discriminates

One isolated coefficient can be dismissed as an eccentric scalar weight.

A single morphology produces a whole transfer curve `H(omega)`. The effective coefficients at different frequencies are coupled because they are consequences of the same topology, path lengths, junctions, material distribution, damping, and wave dynamics.

If one anatomy can improve a broadband target, morphology is functioning as a constrained parameterization of an operator rather than only as storage for one coefficient.

## Frequency mapping rule — fixed before the run

FunctionalArbors uses dimensionless time. No direct audio-Hz calibration exists.

Selected audio frequencies `f_k` are therefore mapped to arbor angular frequencies with one global scale through zero:

```text
omega_k = scale * f_k
```

The scale is chosen so the geometric mean of the selected audio frequencies maps to the existing `FreeConfig.carrier_omega`.

No per-frequency tuning, offset, warping, or fitted frequency map is allowed.

## Target selection — fixed before the run

- Fit AuxIVA to the same simultaneous two-sensor recording used by REAL0.
- Use the pickup-associated AuxIVA component selected by the existing REAL0 code.
- Restrict to 400–2400 Hz by default.
- Divide that band into logarithmic intervals.
- In each interval choose the highest-energy usable target-component bin.
- Score selected bins uniformly so one loud bin cannot dominate the gate.

## Main arm — shared body

For each bootstrap seed:

1. Freeze the starting mature morphology.
2. Measure `H(omega_k)` at every selected frequency.
3. Propose only existing legal v0.5 mass-conserving detour/prune mutations.
4. Accept a mutation only if mean projective angle to the correct AuxIVA curve decreases across the training bins.
5. Score the final morphology across all bins.

No new edge weights, route-specific conductances, or per-frequency parameters are introduced.

## Controls

### C0 — best constant demixing direction

Compute the best frequency-independent complex 2-vector for the selected AuxIVA target directions.

If the target curve is already well represented by one constant direction, a broadband morphology result is uninteresting.

### C1 — independent-body per-frequency oracle

Starting from the same bootstrap morphology, allow each frequency to have its own separately remodeled copy.

This is deliberately unfair in the oracle's favor. It measures the representational price of forcing one coherent body to satisfy all frequencies.

### C2 — held-out interleaved frequencies

Optimize only bins 0,2,4,... and score bins 1,3,5,... that never enter the acceptance objective.

Improvement on held-out bins would be evidence that structural coupling produces useful interpolation rather than independent memorization.

### C3 — shuffled curve

Permute the same AuxIVA target vectors across frequencies, optimize that wrong curve, then score against the correct curve.

This checks whether generic morphology drift produces apparent broadband improvement regardless of the target-frequency relation.

## Predeclared interpretation flags

### Representation pass

Call `representation_pass = true` only if all are true:

1. Median fractional reduction in correct all-bin projective error is at least 15%.
2. At least 75% of usable seeds improve.
3. Median final shared-body error beats the best constant-direction baseline.

This would support the narrow claim that one morphology captures useful frequency-dependent structure.

### Coupling hint

Call `coupling_hint = true` only if:

1. Held-out error improves in at least 75% of usable seeds.
2. Median held-out improvement is greater than median improvement of the shuffled-curve control when both are scored against the correct target.

This is deliberately called a *hint*, not a pass, because the target curve comes from one short real recording and the frequency calibration is normalized rather than physical.

## Kill conditions

The larger interpretation shrinks if:

- shared-body optimization cannot materially improve broadband projective error;
- a constant complex direction explains the target as well as the developed morphology;
- held-out frequencies systematically worsen;
- shuffled targets improve the correct curve just as much;
- the per-frequency oracle is good while the shared body remains poor, showing that the one-body constraint is the bottleneck rather than raw morphological reachability.

## What a positive result would NOT mean

It would not show:

- blind anatomical source separation;
- biological dendrites learning IVA;
- that morphology outperforms FIR/IIR filters or neural networks;
- a physical mapping from audio Hz to the simulator's omega;
- that dendrites exist for source separation.

The defensible positive statement would be:

> One constrained morphology can be supervisedly remodeled so that its coupled physical transfer curve approximates a nonconstant broadband demixing operator better than its initial geometry and a frequency-independent direction.
