# PIPE-OJA-BRANCH0 result — 2026-08-24

## Predeclared question

Does branching itself earn computational value when a single path and a branching organism receive the same inputs, same total mass, same blind learning signal and same raw update?

## Important construction

Both organisms start from exactly the same state: one direct pipe from each of two whitened sensors, mass 0.5 on each. Total mass is constrained to 1.0 throughout.

The only difference is the projection after the blind update:

- cable: at most one delay-pipe per sensor;
- branch: mass may occupy several delay-pipes;
- branch-shuffle: branch geometry, but the soma-derived score is shuffled across time before it is paired with local pipe current.

The data are two independent super-Gaussian source vectors mixed by a frequency-dependent 2x2 convolutive mixer. The learning rule sees only the observed mixtures. Source identities are hidden from learning.

## Default eight-seed receipt

```text
seed   branch    cable    shuffle   cable-capacity   branch-capacity
0      0.9190    0.6621   0.5483       0.8337           0.9933
1      0.9521    0.6586   0.5586       0.8326           0.9937
2      0.9496    0.6722   0.5718       0.8293           0.9943
3      0.9676    0.6631   0.5702       0.8307           0.9945
4      0.9285    0.6844   0.5872       0.8357           0.9932
5      0.9481    0.6486   0.5364       0.8377           0.9929
6      0.9574    0.6828   0.5843       0.8285           0.9937
7      0.9362    0.6446   0.5667       0.8315           0.9929
```

Means:

```text
branch                  0.9448
cable                   0.6645
branch-shuffle          0.5654
cable capacity          0.8325
branch capacity         0.9936
```

Paired exact sign-flip tests:

```text
branch - cable      +0.2803    p=0.00781
branch - shuffle    +0.3794    p=0.00781
```

All eight learned branching runs exceeded the independently searched supervised capacity ceiling of the single-path family.

The branch arm also drove the blind radial objective lower than the cable/shuffle arms, while source purity was only a post-hoc diagnostic.

## Interpretation

This is the first gate in this line where **branching itself has been forced to earn its existence** rather than merely decorating a delay line.

A single path supplies one delay/attenuation relation from each sensor. A branching body can superpose several path delays, so one conserved mass distribution generates a richer broadband transfer function. The blind nonlinear-Hebbian update plus fixed-resource normalization found that extra representational capacity.

The result is stronger than "branching optimized better" because the learned branch beats the best supervised cable available in the declared cable family.

## What it is not

This is not yet FunctionalArbors and not a biological claim. The candidate delay-pipes are supplied in advance rather than grown on a 2-D lattice, whitening is a fixed digital front end, and the resource projection is global rather than physically transported local material.

The next experiment must therefore move this exact adversarial comparison into actual FunctionalArbors. If free branching no longer beats the single-route restriction under the same mass and blind pressure, the present result stays a clean signal-processing toy.
