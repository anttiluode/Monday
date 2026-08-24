# PIPE-OJA-BRANCH0

A tiny gate connecting the earlier **self-normalizing pipe** idea to Monday's ICA/IVA direction.

Question:

> If the same fixed amount of structural resource learns under the same blind broadband pressure, does a freely branching pipe system solve a source-separation problem that a single-path pipe cannot?

This is deliberately **not yet the full FunctionalArbors simulator**. It isolates the representational point before we bury it under grid growth, credit transport and wave dynamics.

## The pipe rule

Each candidate pipe is indexed by sensor `i` and path delay `d`. A unit-mass pipe contributes

```text
q[i,d,k,t] = rho^d * exp(-j*omega[k]*d) * x[i,k,t]
```

at frequency bin `k`. Structural mass `m[i,d] >= 0` scales that contribution, so the soma sees

```text
y[k,t] = sum(i,d) m[i,d] q[i,d,k,t]
```

and total material is always conserved:

```text
sum(i,d) m[i,d] = 1.
```

That is the old pipe intuition in an explicit form: repeated useful signal becomes slow structural mass, but strengthening one route must cost mass elsewhere.

The blind source-vector norm is

```text
r[t] = sqrt(mean_k |y[k,t]|^2)
```

and the scale-free super-Gaussian contrast is

```text
J = E[r] / sqrt(E[r^2])
```

(lower is better). Its exact derivative for one pipe contains a nonlinear Hebbian term and a normalization term. After the step, mass is projected back onto the fixed-mass simplex. This is **Oja-like resource competition**, not a claim that the rule is literally Oja's PCA rule.

No source label enters learning.

## The arms

Both arms begin identically: two direct pipes, one from each whitened sensor, each holding mass 0.5.

- `cable`: exactly one delay-pipe per sensor may carry mass. The same raw gradient is projected onto this single-path morphology.
- `branch`: mass may split over any of the available delays. Parallel paths therefore create a frequency-dependent transfer function.
- `branch_shuffle`: same branching freedom, but the soma score is time-shuffled before the local pipe update. This breaks the current/soma relationship while preserving marginal statistics.

The synthetic mixture is convolutive: each cross-channel mixing term contains multiple delayed paths. That is intentional. A single scalar stretch must not be enough.

Ground-truth sources are used **only after freezing** to score source purity and in the capacity attackers.

## Run

```bash
python pipe_oja/run.py
```

This writes `pipe_oja_branch0.json`.

The committed `index.html` is a standalone visualization of the default eight-seed run and works directly from `file://`.

## Default run on 2026-08-24

Eight seeds, 18 frequency bins, 11 candidate delays per sensor, 180 learning steps, total mass exactly 1.

```text
branch mean purity          0.9448
cable mean purity           0.6645
branch-shuffle mean purity  0.5654

best possible cable         0.8325
best possible branch        0.9936

branch - cable              +0.2803   exact sign-flip p=0.00781
branch - shuffle            +0.3794   exact sign-flip p=0.00781
```

Every learned branching organism in this run exceeded the **supervised capacity ceiling** of the single-path organism. Total mass remained 1.0 in every arm.

That is a real result for this toy gate: the improvement cannot be explained by better optimization of the cable, because the learned branch went beyond what any cable in the declared cable family can represent.

## What this establishes

Only this:

> Under one fixed-resource broadband toy, branching gives the pipe system a useful family of physical transfer functions that a single path cannot realize, and a source-label-free nonlinear Hebbian/Oja-like mass rule can discover them. Breaking the local pipe-current/soma-score alignment destroys the effect.

It does **not** establish biological dendritic learning, ICA in real neurons, or that the present rule will work inside FunctionalArbors.

## Why this sits next to Aizenbud et al.

Aizenbud et al. (PNAS 2026) show that dendritic morphology contributes strongly to modeled single-neuron functional complexity, with dendritic area and bifurcation-branch structure carrying substantial explanatory power. Their result is about how morphology affects computational complexity.

This gate asks the complementary learning question: can a finite structural resource redistribute itself so that **branching structure becomes the learned operator**?

## Next gate

Port the same comparison into actual FunctionalArbors:

1. same bootstrapped mass;
2. same mixed wave traffic;
3. same blind broadband soma pressure;
4. one arm restricted to a single route per terminal;
5. one arm allowed genuine reconnect/branch structure;
6. frozen transfer `H(omega)` measured afterward;
7. shuffled-credit and supervised-capacity controls retained.

If the free arbor loses there, this branch remains a useful filter-bank toy and nothing more.
