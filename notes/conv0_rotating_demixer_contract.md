# FA-BSS-CONV0 contract — synthetic rotating demixer

Date: 2026-08-24

## Why this gate exists

REAL1B used a real SM58 + guitar-pickup recording. The AuxIVA coefficients looked strongly frequency dependent in raw ratio form, but the best **frequency-independent projective direction** scored only 15.38 degrees mean error. That exposed a false-positive route: large coefficient magnitudes can still point toward almost the same sensor axis.

CONV0 removes that ambiguity before morphology is trained.

The question is:

> **Can one fixed-mass FunctionalArbor learn a genuinely nonconstant, rotating demixing direction across frequency, when the exact convolutive mixing process is known in advance?**

This remains a supervised structural capability test. It is not blind source separation and not a biological claim.

## Frozen synthetic world

Two hidden sources `s1`, `s2` are mixed into two observed channels by a 2x2 FIR system:

```text
x1[t] = s1[t] + 0.90 * s2[t - 14]
x2[t] = 0.35 * s1[t - 3] + s2[t]
```

In the frequency domain,

```text
A(omega) = [[1,                 0.90 exp(-i 14 omega)],
            [0.35 exp(-i 3 omega),                 1]]
```

The determinant is

```text
1 - 0.315 exp(-i 17 omega)
```

so its magnitude is bounded below by `1 - 0.315 = 0.685`; the mixture is safely invertible at every frequency.

A row that exactly cancels `s2` is, up to arbitrary nonzero complex scale,

```text
w(omega) = [1, -0.90 exp(-i 14 omega)]
```

Therefore the required projective demixing direction rotates with frequency even though its coefficient magnitude is constant.

The matched digital FIR extractor is simply

```text
y[t] = x1[t] - 0.90 * x2[t - 14]
```

which cancels `s2` exactly. That is an intentionally brutal boring baseline.

## Frozen frequency grid

Use nine equally spaced dimensionless FunctionalArbor angular frequencies:

```text
omega = linspace(0.07, 0.35, 9)
```

No Hz mapping is involved in this synthetic gate.

Before any arbor optimization, compute the best single frequency-independent complex direction across these nine exact target rows.

**Hardness prerequisite:** its mean projective error must be at least **30 degrees**. If not, abort the morphology experiment. We do not tune the FIRs after seeing arbor performance.

With the frozen numbers above, the target phase sweep is produced by the 14-step delay. The code must print the actual constant-vector difficulty before training.

## Arms / attackers

### C0 — best constant direction

Find the single two-complex-number direction that minimizes average projective error across all nine target rows.

This is the main attacker that killed REAL1B.

### C1 — exact matched FIR

The known two-tap/delay extractor above has zero target projective error by construction. It is reported explicitly so a structural success is never described as beating ordinary signal processing.

### C2 — independent-body oracle

Each frequency receives its own separately remodeled FunctionalArbor. This removes the shared-body constraint and estimates how much error comes from morphology reachability/search rather than cross-frequency coupling.

### C3 — held-out frequencies

Train one shared body using only indices `0,2,4,6,8`. Acceptance never sees indices `1,3,5,7`. Score the withheld frequencies before and after.

This is the important coupling/generalization test.

### C4 — shuffled frequency assignment

Permute the same target directions across frequencies, optimize that wrong curve, then score against the correct curve. This estimates generic drift / target-insensitive improvement.

## Structural learning rule

Use the existing `FunctionalArbors/v05_free_arbor` bootstrap and legal mass-conserving `propose_detour()` mutation unchanged.

The teacher objective is mean projective angle between the body's measured transfer vector

```text
H(omega) = [H1(omega), H2(omega)]
```

and the exact target row `w(omega)`.

No new edge weights, route-specific conductances, or frequency-specific body parameters may be introduced.

## Frozen execution constants

These are fixed before the first morphology run:

```text
seeds                 = 0,1,2,3
bootstrap_mass        = 90
shared proposals      = 120 per arm
independent proposals = 80 per frequency
frequencies           = 9
omega range           = 0.07 .. 0.35 inclusive
```

The existing v0.5 model configuration is otherwise unchanged.

## Predeclared interpretation

### `rotating_representation_pass`

Require all of:

1. hardness prerequisite passes (`constant_error >= 30 deg`);
2. at least 3 of 4 usable seeds finish with shared-body error **below the best constant-direction error**;
3. median fractional improvement from each seed's starting morphology is at least 20%.

This would establish that one physical morphology can express useful nonconstant frequency dependence on this controlled target. It would **not** establish superiority to FIR filters; the matched FIR is exact and dramatically simpler for this constructed world.

### `heldout_coupling_pass`

Require all of:

1. withheld-frequency error improves in at least 3 of 4 usable seeds;
2. median withheld-frequency improvement is positive;
3. median correct-curve improvement in the held-out arm exceeds the median improvement obtained by optimizing the shuffled curve.

This would strengthen REAL1B's weaker `coupling_hint` by using a target known in advance to rotate substantially.

## What success would mean

A pass would support only this statement:

> **One persistent geometry can learn a coherent, frequency-dependent operator rather than merely one constant complex coefficient, and structural changes selected at some frequencies can move unseen frequencies in a useful direction.**

It would not mean morphology is a better representation than an FIR filter. In fact this target is deliberately generated by a very low-dimensional digital mechanism: one gain and one delay. If CONV0 passes, the next fair attack is a richer multi-tap convolutive target whose inverse cannot be described by one delay ramp.

## What failure would mean

If the constant-vector attacker still wins, or if held-out frequencies do not improve, the current v0.5 FunctionalArbor has not demonstrated useful broadband structural coupling even on a target deliberately aligned with delay/phase physics.

That would be a substantial hit to the current structural-operator interpretation and should be recorded as such rather than tuned away.
