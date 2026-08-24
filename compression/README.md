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

This is the most important failure that led to C3.

The clean C1 mechanism **does not simply appear when attached after the fact to C0's local Gabor moves**. The per-gate pose search emits too many small, inconsistent, intermittent `{-1,0,+1}` decisions. A post-hoc relation matrix barely saves anything.

---

## Gate C3 — move the matrix before the decisions

Run:

```bash
python compression/gate3_predictive_group_codec.py
```

C3 changes the causal order rather than tuning C2.

```text
frozen pre-decision reconstruction
        |
        v
all gates propose local 3x3 moves
before any gate is moved
        |
        v
decaying motion/proximity matrix
        |
        v
temporary shared-motion hypothesis
        |
        v
sequential residual refit searches only:
  STAY + top two frozen proposals + group proposal
        |
        v
MOVE GROUP + sparse residual overrides
```

The reason for freezing the proposal stage is specific: in C0 the first gate's accepted move changes the residual seen by the next gate. If several gates share a physical motion, that sequential fitting can decorrelate their move decisions before a later grouping stage ever sees them.

C3 therefore lets the matrix see the local proposals **before** those decisions modify one another.

### The boring pruning null

There is an important attacker inside C3:

```text
PRUNED NULL = same frozen proposal stage
            + same top-2 reduced sequential search
            + NO transient matrix
```

Without this null it would be easy to credit the matrix for a gain actually caused by the much simpler act of not re-searching all nine translations per gate.

First deterministic run, 2026-08-24:

```text
fixed   bits/frame   391.7 | churn 5.49% | PSNR 24.27 | search   0.0
indep   bits/frame   750.8 | churn 2.02% | PSNR 23.59 | search 809.2
pruned  bits/frame   661.9 | churn 2.60% | PSNR 23.54 | search 201.6
guided  bits/frame   641.3 | churn 2.34% | PSNR 23.35 | search 200.3

guided groups/frame             0.53
guided motion bits/frame       342.5
guided residuals/frame           0.34
membership bits/frame           13.1

guided / independent bits       0.854
guided / pruned-null bits       0.969
guided / fixed bits             1.637
guided / independent search     0.248
PSNR vs independent            -0.23 dB
PSNR vs pruned null            -0.19 dB
```

Exact C3 numerical stop lines were **not preregistered** before the first run, so do not treat the following labels like the earlier registered gates. The script prints three interpretations:

```text
OVERALL GUIDED ROUTE: PASS
MATRIX INCREMENTAL OVER PRUNING NULL: FAIL
STRONG FIXED-CODE COMPETITOR: FAIL
```

The important decomposition is:

1. Moving the prediction stage earlier and pruning the local search is useful. Relative to C0's independent MOVE codec, C3 uses about **14.6% fewer bits**, about **75% fewer candidate evaluations**, and loses only **0.23 dB**.
2. Most of that win is **not yet the transient matrix**. The no-matrix pruning null is already at 661.9 bits/frame. The matrix only moves that to 641.3 bits/frame, about a **3.1% incremental saving**, while losing another 0.19 dB. That misses the deliberately stronger 5% incremental line in the script.
3. Neither moving codec is close to the boring fixed-address event coder. C3 remains about **1.64x** its bit cost.

So C3 partially repairs C2's causal-order mistake, but it does **not** earn the object-like story.

The current evidence supports a much narrower statement:

> **Pre-decision transport proposals are a useful predictive scaffold. A transient relation matrix adds a small extra saving on this toy stream, but the dominant gain comes from proposal pruning, and the original fixed-address codec still wins badly on bits.**

That is a better stopping point than tuning the matrix until it passes.

### What C3 says the next gate should attack

The matrix is trying to bind already-discrete `{-1,0,+1}` translations. That may still be too late / too lossy a description of motion.

The next serious candidates are earlier and more continuous:

- quadrature Gabor **phase change** before a discrete move is selected;
- coarse-scale gates proposing a motion field that fine gates inherit;
- local affine / Sim(2)-like group motion rather than one identical translation for every member;
- continuous trajectories followed by PCA only to ask whether the motion is actually low-rank;
- then ICA / IVA only if several independent cause families are genuinely mixed.

And before any semantic language returns, the same hard rule remains:

> if the representation does not reduce bits, search, or distortion against the boring null, it has not bought the codec anything.

---

## Where PCA / ICA / IVA fit

Not first.

C3 now gives a better place to insert them than C0 did, but the matrix result itself is still small.

If a next gate produces more continuous persistent trajectories, then:

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

C3  pre-decision proposals + matrix-guided reduced search
    -> 14.6% below independent MOVE bits
    -> ~75% less local search
    -> only 3.1% incremental gain over no-matrix pruning null
    -> fixed-address codec still wins badly
    -> broad route interesting; matrix-specific claim NOT YET EARNED
```

The interesting object is still not "object recognition."

It is:

> **a transient relation scaffold that should exist only while several persistent primitives actually benefit from sharing a prediction.**

C3 says that idea has a measurable but currently small footprint in the real Gabor toy stream. If a later version begins to resemble an object, the compression advantage still has to arrive before the name does.
