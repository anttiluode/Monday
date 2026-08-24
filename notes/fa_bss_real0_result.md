# FA-BSS-REAL0 result — 2026-08-24

## Recording

`Wav/two_ears_in0.wav` (SM58 / XLR) and `Wav/two_ears_in1.wav` (guitar pickup / instrument jack) are synchronous 44.1 kHz, 8 s recordings saved by TWO EARS. TWO EARS normalized the channels separately on save, so relative physical gain is not preserved, but timing and linear separability are.

The channels are much less alike than a conventional two-microphone cocktail-party mixture:

- best time-domain |corr| ~= 0.117 at -17 samples (-0.385 ms)
- median magnitude-squared coherence over 40 Hz–10 kHz ~= 0.029
- 95th percentile coherence ~= 0.174
- pickup dominates the low-frequency region strongly (e.g. ~81 Hz by +41 dB relative to mic)
- mic dominates several ~7 kHz regions by about +30 dB

Interpretation: this recording is already a heterogeneous-sensor problem. The SM58 and pickup mostly observe different physical worlds, with some shared leakage. Do not equate “two returned components” with recovered latent causes.

## Digital baselines

FastICA returns almost the sensor axes:

- component 0 signature ~= [0.020 mic, 0.980 pickup]
- component 1 signature ~= [0.923 mic, 0.077 pickup]

This is consistent with the low raw cross-channel dependence: an instantaneous ICA model can obtain apparent independence largely by keeping the two sensor modalities separate.

AuxIVA returns more mixed component signatures:

- component 0 ~= [0.749 mic, 0.251 pickup]
- component 1 ~= [0.142 mic, 0.858 pickup]

The separation between those signatures is substantial (L1 ~= 1.213), but without a causal intervention or answer key this is not proof that component 1 is “the phone” or component 0 is “voice.” Freeze-and-kill remains the decisive physical test.

## The real complex target

For the pickup-associated AuxIVA component, the strongest selected bin is 602.93 Hz. Its demixing row is approximately

`w = [0.086 - 0.806j, 1.004 + 0.004j]`

so

`w1/w0 ~= 0.126 + 1.232j`

with magnitude ~= 1.239 and phase ~= +84.1 degrees.

This matters: unlike synthetic FA-BSS0’s purely real target ratio, the real recording supplies a strongly complex phase relation. A useful morphology therefore must implement genuine phase-sensitive transfer, not merely “make one branch longer.”

## FunctionalArbor teacher compile

Four v0.5 bootstrap morphologies were asked to move their measured two-terminal transfer vector toward that real AuxIVA row using only legal detour/prune mutations.

Projective angle error (degrees):

- seed 0: 49.6 -> 40.9; AuxIVA-bin output corr 0.251 -> 0.681; 3 accepted moves
- seed 1: 48.0 -> 23.7; corr 0.978 -> 0.992; 4 accepted moves
- seed 2: 39.8 -> 16.1; corr 0.963 -> 0.996; 6 accepted moves
- seed 3: 28.7 -> 28.7; corr unchanged 0.953; 0 accepted moves

Mean projective error improvement is ~14.1 degrees (0.247 rad).

Provisional result: **existing FunctionalArbor morphology can move toward a complex demixing coefficient fitted from a real two-sensor recording.** This is a representational/compile result, not blind source separation.

Important caution: output correlation to the AuxIVA bin is not itself a strong compile metric here. Three initial morphologies already correlate >0.95 with the AuxIVA output despite being 29–48 degrees away in demixing-vector space. Many different linear combinations can produce nearly the same one-bin waveform when one sensor/source dominates. The projective coefficient error is the more discriminating measurement.

## Blind cumulant arm: fail as a separation objective

The exploratory one-bin fourth-cumulant objective does **not** survive this real recording.

- seed 0: blind score 18.71 -> 21.32 while AuxIVA corr collapses 0.251 -> 0.016
- seed 1: blind objective happens to reach the same useful morphology as teacher
- seed 2: no blind mutation accepted
- seed 3: blind score 2.84 -> 9.97 while AuxIVA corr falls 0.953 -> 0.561

Across the four seeds, the blind arm’s mean AuxIVA correlation decreases and its mean projective error does not improve meaningfully.

Diagnosis: maximizing non-Gaussianity at a **single frequency bin and single output** is underconstrained. It can simply select an impulsive/sparse sensor direction. This is not ICA/IVE in the useful sense because there is no whitening/orthogonality or broadband source-vector consistency pressure.

**Do not tune this one-bin cumulant objective further. Kill it.**

## What REAL0 actually establishes

1. The physical SM58 + pickup pair is interesting, but mostly modality-separated already; there is shared leakage rather than a classic equal-mixture cocktail party.
2. AuxIVA learns frequency-dependent complex combinations that are measurably different from the sensor axes.
3. A v0.5 FunctionalArbor can be structurally moved toward one such real complex combination.
4. The current blind one-bin cumulant rule is wrong.
5. The next discriminating experiment should be causal and broadband.

## Next gates

### REAL1A — frozen physical intervention

Fit AuxIVA on a recording containing both causes, freeze `W`, then record controlled changes with the same hardware gains and clock:

- both phone + speech
- phone only
- speech only
- neither

Apply the frozen `W` without refitting. A genuine source component should collapse selectively when its cause is removed. This names the components without storytelling.

### REAL1B — broadband anatomical compile

Do not compile one isolated STFT bin. Select a set of informative bins and compare one morphology’s transfer curve `H(omega_k)` against the corresponding AuxIVA demixing curve `w(f_k)` with one shared anatomy. The objective is a weighted sum of projective errors across bins.

This asks the important question: **can one developed geometry embody a frequency-dependent demixing filter, rather than one complex coefficient?**

### REAL2 — blind broadband extraction

Only after the intervention and broadband compile gates work, replace the teacher with a proper IVE/IVA-style objective: whitened observations, broadband source-vector norm shared across frequencies, variance constraint, and a residual/orthogonality term to prevent trivial sensor selection.

The lesson from REAL0 is exactly the identifiability lesson: do not demand that a pretty independent-looking output be a source. Require a frozen transfer, a controlled intervention, and a coefficient-space prediction.
