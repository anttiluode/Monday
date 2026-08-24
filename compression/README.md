# Monday / compression

A late Monday detour from the Gabor/Splat lineage into a very concrete question:

> **If the same visual primitives survive from frame to frame, should motion be encoded as destruction + rebirth, or as transport of persistent primitives? And if many primitives move together, can a transient relation matrix factor that shared motion cheaply?**

This folder is deliberately attached to **Monday** rather than promoted into a new grand repo. Monday's useful language was mixtures -> causes and persistent structure -> constrained families of computations. Compression supplies a hard attacker: **bits at a given reconstruction quality**.

The immediate provenance is:

- `anttiluode/GaborVideoCompression`: a sparse analytic Gabor code persists across video frames and transmits gate births, deaths and amplitude changes.
- `anttiluode/Splatworld2`: repeated visual destruction became much easier to reason about once transport was separated from repainting and the detail anchor was kept immutable.
- Monday: ICA / IVA / IVE as disciplined tools for hidden causes, plus the surviving idea that one structured state can generate many coupled coefficients.

No claim here that Gabor gates are objects, that ICA discovers semantic objects, or that this is a competitive codec.

## The hypothesis

The fixed-address Gabor codec has no first-class operation for:

```text
this same gate moved
```

so smooth transport can appear as:

```text
old gate dies
new nearby gate is born
```

The first extension is therefore a persistent gate with a local pose:

```text
gate = identity + base atom + x/y offset + amplitude
```

and an event:

```text
MOVE gate dx dy
```

The second extension is the thing that motivated this folder:

```text
many persistent gates
        |
        v
temporary pairwise relation matrix
        |
        +-- repeated similar motion?
        +-- spatially near enough to be useful?
        |
        v
transient motion group
        |
        v
one shared move + sparse residuals
```

The word **group** is intentional. The word **object** is not yet earned.

A transient group is merely a temporary compression hypothesis: *these primitives are cheaper to predict / move together than separately.*

---

## Gate C0 — does MOVE expose real transport?

Run:

```bash
python compression/gate0_transport_codec.py
```

`gate0_transport_codec.py` rebuilds the analytic 64x64 Gabor dictionary used by the compression demo (3060 atoms), uses a shorter 48-frame synthetic run and `K=100` for runtime, and compares:

- a fixed-address sparse coder;
- the same kind of coder where an existing gate may search a `3x3` one-pixel translation neighborhood before death.

A translated gate remains decoder-reconstructible from its original atom plus accumulated integer offset.

Registered run (`seedless deterministic test pattern`, 2026-08-24):

```text
dictionary atoms: 3060 | K=100 | frames=48

fixed:
  bits/frame        391.7
  churn               5.49 %
  PSNR               24.27 dB
  births/deaths       3.08 / 1.76 per frame

moving:
  bits/frame        750.8
  churn               2.02 %
  PSNR               23.59 dB
  births/deaths       1.45 / 0.13 per frame
  MOVE events        37.03 per frame

bit ratio moving/fixed     1.917
churn ratio moving/fixed   0.369
PSNR delta                -0.68 dB

RESULT: FAIL
```

This is a useful failure.

**Transport killed about 63% of the structural churn, but paying for 37 independent MOVE events per frame almost doubled the stream.**

So the first intuition was partly right and still not useful enough:

> much of death/birth really can be replaced by identity-preserving transport;

but:

> describing every primitive's transport independently is too expensive.

That failure is the reason Gate C1 exists.

---

## Gate C1 — can a transient matrix discover useful motion groups at all?

Run:

```bash
python compression/gate1_transient_motion_matrix.py
```

This gate removes image coding entirely. It assumes primitives have already been tracked and gives the grouping idea a clean synthetic world with known ground truth:

```text
3 independently moving groups x 16 primitives
12 independent distractor primitives
```

The algorithm sees only positions and recent motion vectors.

It maintains a decaying pairwise matrix:

```text
affinity(i,j) ~= repeated velocity agreement x spatial usefulness
```

and uses density clustering on that transient matrix. Group membership is not permanent and membership changes are charged bits.

Registered run:

```text
main mean ARI               1.000
main median ARI             1.000
guided / unguided evals     0.347
group / independent bits    0.241
bits: group 19194  independent 79800
shuffled-motion mean ARI    0.000
global-motion mean ARI      0.000

RESULT: PASS
```

Interpretation:

- in a clean world where coherent local motion really exists, a disposable relation matrix can recover the known groups;
- using the group's predicted displacement reduces the hypothetical local search to about 35% of unguided candidate evaluations;
- one group move plus residuals can be far cheaper than independent moves;
- shuffling motion destroys the result;
- when all objects share only global camera motion, the matrix collapses the distinction instead of hallucinating semantic object identity.

That last control matters. **Motion coherence is not object identity.** For a codec, a global motion group can still be useful; it simply must not be called an object.

C1 is a mechanism sanity check, not evidence about the Gabor stream.

---

## Gate C2 — does the transient matrix rescue the actual C0 move stream?

Run:

```bash
python compression/gate2_grouped_transport_codec.py
```

C2 leaves C0's image reconstruction untouched. It only watches the persistent gate identities and their chosen local translations, accumulates a decaying motion/proximity relation matrix, and tries to describe those already-selected movements using transient groups.

Registered run:

```text
fixed-address bits/frame       391.7
individual-MOVE bits/frame     750.8
grouped-MOVE bits/frame        743.9

grouped / individual           0.991
grouped / fixed                1.899

fixed churn                    5.49 %
moving churn                   2.02 %
moves/frame                   37.03
transient groups/frame         0.55

RESULT: FAIL
strong fixed-code competitor: FAIL
```

This is the most important result in the folder so far.

The clean C1 mechanism **does not simply appear when attached after the fact to C0's local Gabor moves**.

The current per-gate pose search emits too many small, inconsistent, intermittent `{-1,0,+1}` decisions. A post-hoc relation matrix barely saves anything.

So the attractive story:

```text
persistent Gabor gates -> transient matrix -> objects -> cheap guidance
```

has **not** been demonstrated.

What survived is narrower:

1. C0 says transport is hiding inside some of the fixed-code churn.
2. C1 says transient grouping can be useful when coherent motions are actually observable.
3. C2 says the current Gabor move estimator destroys / fails to expose enough coherence for the grouping to matter.

---

## The next gate

The next experiment should **not** tune C2's clustering thresholds until it passes.

The matrix needs to move earlier in the causal chain.

### C3 — group-guided transport, not post-hoc grouping

Current C0:

```text
each gate independently searches 3x3
        |
        v
37 jittery MOVE decisions/frame
        |
        v
try to group them afterward
```

Proposed C3:

```text
continuous/local transport evidence
        |
        v
transient relation matrix
        |
        v
temporary shared motion hypotheses
        |
        v
group predicts where its gates should search
        |
        +-- cheap residual 3x3 / subpixel correction
        |
        v
MOVE GROUP + sparse residuals
```

The difference is important.

The transient matrix would become a **predictive routing scaffold**, not merely a compressor placed after 100 independent decisions have already thrown away their common structure.

Good sources of pre-decision motion evidence include:

- quadrature Gabor phase change;
- local optical-flow-style transport;
- correlation of amplitude/phase trajectories across nearby scales;
- a coarse-to-fine motion proposal where coarse gates guide fine gates.

Registered attackers for C3 should include:

- fixed-address Gabor event codec;
- independent MOVE codec from C0;
- global-motion-only scene;
- two objects crossing / occluding;
- shuffled gate trajectories;
- matched PSNR, not just lower bits;
- full membership-definition and residual costs.

A useful win is not "the groups look object-like." It is:

> **group-guided transport lowers total coded bits or search work at matched quality, and the advantage disappears when the motion relation is destroyed.**

---

## Where PCA / ICA / IVA fit

Not first.

The current C0 move stream is already telling us that throwing a decomposition at noisy per-gate trajectories would be premature.

If C3 produces persistent continuous trajectories, then:

```text
gate trajectories
       |
       +-- PCA: is the local motion actually low rank?
       |
       +-- ICA: are several independent motion causes mixed in that trajectory space?
       |
       +-- IVA/JISA: do corresponding motion/source families stay tied across
                     Gabor scales, phases or local views?
       |
       +-- IVE: can the codec maintain only one requested source family?
```

These are attackers / factorization tools, not decorations.

The compression meter gives them a simple test:

> if a factorization does not reduce bits, search, or distortion, it has not bought the codec anything.

---

## SplatWorld2 and the visible "fire"

SplatWorld2's immutable-anchor repair is still worth a separate gate, but it should remain separate from the transport claim.

The Gabor reconstruction is already decoded fresh from the active sparse code; it is not recursively re-encoding the previous reconstructed pixels. So any similar-looking "fire" is not automatically the same bug.

A legitimate future visual gate would be:

```text
sparse decoded frame = changing guide
immutable decoder-known anchor = detail reservoir
guide estimates transport
warp anchor detail only where confidence remains high
refresh anchor when confidence/churn says the old anchor is invalid
```

For a real codec, the receiver must be able to perform the same operation from transmitted state. No hidden access to the original webcam frame is allowed.

---

## Current status

```text
C0  MOVE instead of death+birth
    -> churn reduction is real
    -> bit cost FAILS

C1  transient relation matrix in clean tracked world
    -> grouping / guidance / bit accounting PASS

C2  post-hoc matrix on actual C0 gate moves
    -> almost no savings
    -> FAIL

C3  predictive group-guided transport
    -> not implemented yet
```

That is enough for Monday night.

The interesting object is no longer "object recognition."

It is:

> **a transient matrix that exists only while several persistent primitives benefit from sharing a prediction.**

If that eventually resembles an object, the compression advantage should arrive before the name does.
