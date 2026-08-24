# FA-BSS-REAL1B result — 2026-08-24

## Gate

Question:

> Can one fixed-mass FunctionalArbor morphology move toward a frequency-dependent AuxIVA demixing curve across several frequencies at once?

This was pre-registered in [`real1b_broadband_contract.md`](real1b_broadband_contract.md).

The gate remained supervised. AuxIVA supplied the target demixing directions. The FunctionalArbor was only allowed the existing v0.5 mass-conserving detour/prune mutation.

The run executed in GitHub Actions on Python 3.12 against the current `FunctionalArbors/main` checkout. Workflow run: `32703779329`.

## Target construction

The existing REAL0 two-sensor recording was reused.

AuxIVA again selected component 1 as the pickup-associated component. Nine energetic bins were selected across logarithmic sub-bands in the requested 400–2400 Hz range. The actual chosen frequencies were:

```text
409.13
581.40
602.93
775.20
904.39
1098.19
1399.66
1614.99
2002.59 Hz
```

Because FunctionalArbors uses dimensionless time, there was no fake Hz calibration. One global scale through zero mapped the geometric-mean audio frequency, 925.84 Hz, to the existing arbor carrier `omega=0.16`. The resulting arbor frequencies spanned approximately `0.0707 .. 0.3461`.

The AuxIVA target ratios `w1/w0` were:

```text
409.1 Hz    0.844 + 1.173j
581.4 Hz    0.204 + 1.388j
602.9 Hz    0.126 + 1.232j
775.2 Hz    5.513 - 0.086j
904.4 Hz   -0.820 + 5.030j
1098.2 Hz   4.920 + 3.612j
1399.7 Hz   6.208 - 2.664j
1615.0 Hz   9.682 + 2.326j
2002.6 Hz  22.087 - 12.890j
```

These ratios look strongly frequency dependent numerically. The decisive control showed why that visual impression is misleading.

## C0 — best constant direction exposes the problem

The best single frequency-independent complex demixing direction scored only:

```text
15.38 degrees mean projective error
```

That is dramatically better than any of the tested FunctionalArbor morphologies.

Why? At the upper frequencies, `|w1/w0|` becomes very large. In projective demixing space those rows increasingly point toward the same second-sensor axis. Huge changes in ratio magnitude therefore do **not** imply equally huge changes in demixing direction.

This means the real recording did not supply the hard broadband target we thought it might.

## Shared-body arm

Four bootstrap seeds were optimized across all nine bins.

```text
seed 0   55.76 -> 49.10 deg   4 accepted mutations
seed 1   33.63 -> 26.08 deg   3 accepted mutations
seed 2   39.95 -> 38.37 deg   3 accepted mutations
seed 3   45.22 -> 30.88 deg   3 accepted mutations
```

Aggregate:

```text
start mean                 43.64 deg
final shared-body mean     36.11 deg
median fractional gain     17.2%
seeds improved             4 / 4
```

So one body **did** move coherently toward the multi-frequency target. This is a real positive capability result.

But it does not pass the pre-registered representation gate, because the best constant direction was far better at 15.38 degrees.

`representation_pass = false`

The correct conclusion is therefore:

> The shared morphology can improve a broadband objective, but this recording does not demonstrate that morphology captures useful frequency dependence better than one fixed demixing direction.

## C1 — independent-body oracle

If every frequency is allowed its own separately remodeled morphology, mean error was:

```text
26.47 deg
```

This is better than the shared body's 36.11 degrees, as expected, but still worse than the 15.38-degree constant-vector control.

That is revealing. The main limitation here is not merely the one-body coupling constraint. The current v0.5 morphology space/search also has difficulty reaching even the relatively simple projective directions demanded by this target.

## C2 — held-out frequencies

Training used alternating bins and never scored the interleaved bins during acceptance.

```text
seed 0   held-out 59.96 -> 52.73 deg
seed 1            45.59 -> 45.59 deg
seed 2            39.35 -> 40.11 deg
seed 3            40.92 -> 29.96 deg
```

Aggregate:

```text
held-out start mean   46.46 deg
held-out final mean   42.10 deg
seeds improved        3 / 4
```

This satisfies the pre-registered weak coupling criterion.

`coupling_hint = true`

That is the interesting residue. Structural changes selected using only alternating frequencies often moved unseen frequencies in the useful direction as well. This is exactly the kind of coupled behavior expected when many effective coefficients are consequences of one shared geometry.

But it must remain a **hint** because the main representation gate failed and the target itself is close to a constant projective direction.

## C3 — shuffled-curve control

A wrong permutation of the same target vectors was optimized and then scored against the correct curve.

```text
correct-target mean before shuffled optimization   43.64 deg
correct-target mean after shuffled optimization    42.64 deg
```

Only about one degree of incidental improvement occurred, versus about 4.36 degrees on held-out bins in the correctly ordered alternating-frequency arm.

That supports the interpretation that the held-out movement is not purely generic morphology drift.

## Verdict

The strong broadband claim does **not** survive this gate.

### Killed / weakened

Do not say:

> REAL1B showed that one arbor compactly represents a genuinely frequency-dependent AuxIVA demixer better than a simple fixed coefficient.

It did not. The constant-vector attacker wins decisively.

### Surviving residue

Two narrower facts survive:

1. One shared morphology improved a nine-frequency target in all four seeds.
2. Target-aware remodeling on alternating frequencies improved unseen frequencies in three of four seeds and did more useful work than optimizing a shuffled target ordering.

The second fact is the first direct evidence in Monday that **structural coupling across frequencies is operational rather than merely verbal**.

It is not enough yet to establish that this coupling is useful compared with ordinary parameterizations.

## What the gate taught us about the experiment, not just the arbor

REAL0 had already warned that the SM58 + guitar pickup pair is mostly a heterogeneous-sensor problem rather than a difficult cocktail-party mixture.

REAL1B makes that warning decisive. Above roughly 800 Hz, the AuxIVA row increasingly becomes dominated by one physical sensor. A broadband target can therefore look spectacular in raw complex ratios while collapsing to a nearly constant direction in the projective space that actually matters for two-channel demixing.

So the next broadband test should not simply search this recording for bins with visually dramatic ratios. That would be post-hoc target shopping.

A cleaner next gate is a **known convolutive synthetic mixture** whose FIR paths are chosen before the run to force a genuinely rotating demixing direction across frequency. Then:

- the exact inverse filter is known;
- source identity is known;
- the target cannot collapse to a sensor axis without us noticing;
- constant-vector difficulty can be precomputed before morphology is trained;
- one shared body, independent per-frequency bodies, and ordinary FIR baselines can be compared fairly.

Only after that should the real physical recording return, ideally with the frozen intervention recordings from REAL1A.

## Bottom line

REAL1B did not give Monday the big broadband result.

It did something more useful: it caught a subtle false-positive route before we could mistake large changes in complex coefficient magnitude for a genuinely high-dimensional demixing operator.

The remaining interesting observation is that **one structural change can move several unseen transfer coefficients together in a target-relevant way**.

That is now the thing to attack next.
