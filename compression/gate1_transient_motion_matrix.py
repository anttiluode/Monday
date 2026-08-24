#!/usr/bin/env python3
"""
Monday / compression / Gate C1
Transient motion matrix: can temporary pairwise motion coherence recover
object-like groups well enough to guide persistent primitives more cheaply?

This is deliberately NOT an object detector and NOT a video codec yet.
Inputs are already-tracked primitive positions. Synthetic ground truth lets us
attack the grouping claim before wiring it into the Gabor codec.

PASS criteria (registered in README):
  - grouped-object ARI >= 0.80 after warmup
  - guided candidate evaluations <= 45% of unguided
  - group-coded move bits <= 60% of independent move bits
  - shuffled-motion control ARI <= 0.35
Global camera-motion control is diagnostic: it SHOULD collapse objects together.
"""
from __future__ import annotations
import argparse
import math
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.metrics import adjusted_rand_score

SEED = 20260824
N_GROUPS = 3
PER_GROUP = 16
N_NOISE = 12
N = N_GROUPS * PER_GROUP + N_NOISE
T = 120
WARMUP = 25
DECAY = 0.88
SIGMA_V = 0.34
SIGMA_P = 22.0
DBSCAN_EPS = 0.30
DBSCAN_MIN = 5
UNGUIDED_RADIUS = 3
GUIDED_RADIUS = 1
GATE_INDEX_BITS = 8
MOVE_BITS = 6
GROUP_ID_BITS = 4
RESID_BITS = 4
MEMBERSHIP_BITS = 8
RESID_THRESHOLD = 0.24

def group_velocity(g: int, t: int, global_motion=False) -> np.ndarray:
    tt = t / 11.0
    if global_motion:
        return np.array([0.72 + 0.14*math.sin(.31*tt),
                         0.18 + 0.10*math.cos(.27*tt)], np.float32)
    if g == 0:
        return np.array([0.75 + 0.20*math.sin(.39*tt),
                         0.12 + 0.18*math.cos(.31*tt)], np.float32)
    if g == 1:
        return np.array([-0.55 + 0.14*math.cos(.28*tt),
                          0.52 + 0.16*math.sin(.43*tt)], np.float32)
    return np.array([0.15 + 0.20*math.sin(.37*tt + 1.0),
                    -0.70 + 0.12*math.cos(.33*tt)], np.float32)

def simulate(seed=SEED, global_motion=False):
    rng = np.random.default_rng(seed)
    centers = np.array([[18., 20.], [48., 19.], [34., 48.]], np.float32)
    pos = []
    labels = []
    for g in range(N_GROUPS):
        pos.append(centers[g] + rng.normal(0, 4.0, size=(PER_GROUP,2)))
        labels.extend([g]*PER_GROUP)
    pos.append(rng.uniform(6, 58, size=(N_NOISE,2)))
    labels.extend([-1]*N_NOISE)
    pos = np.vstack(pos).astype(np.float32)
    labels = np.asarray(labels, np.int32)

    noise_vel = rng.normal(0, .25, size=(N_NOISE,2)).astype(np.float32)
    P=[pos.copy()]
    V=[]
    for t in range(T):
        v=np.zeros((N,2),np.float32)
        for g in range(N_GROUPS):
            ix=np.flatnonzero(labels==g)
            v[ix]=group_velocity(g,t,global_motion) + rng.normal(0,.055,size=(len(ix),2))
        noise_vel[:] = 0.82*noise_vel + rng.normal(0,.18,size=noise_vel.shape)
        v[labels<0]=noise_vel
        pos = pos + v
        P.append(pos.copy()); V.append(v.copy())
    return np.asarray(P), np.asarray(V), labels

def similarity(pos, vel):
    dv=vel[:,None,:]-vel[None,:,:]
    dp=pos[:,None,:]-pos[None,:,:]
    sv=np.exp(-np.sum(dv*dv,axis=2)/(2*SIGMA_V**2))
    sp=np.exp(-np.sum(dp*dp,axis=2)/(2*SIGMA_P**2))
    S=(sv*(0.30+0.70*sp)).astype(np.float32)
    np.fill_diagonal(S,1.0)
    return S

def clusters_from_affinity(A):
    D=1.0-np.clip(A,0,1)
    np.fill_diagonal(D,0)
    return DBSCAN(eps=DBSCAN_EPS,min_samples=DBSCAN_MIN,metric="precomputed").fit_predict(D)

def ari_on_object_members(pred, truth):
    m=truth>=0
    return adjusted_rand_score(truth[m],pred[m])

def canonical_memberships(pred):
    out=set()
    for k in sorted(set(pred)):
        if k < 0: continue
        members=tuple(np.flatnonzero(pred==k).tolist())
        if len(members)>=DBSCAN_MIN:
            out.add(members)
    return out

def run_relation(P,V,truth,shuffle=False,seed=SEED):
    rng=np.random.default_rng(seed+999)
    A=np.eye(N,dtype=np.float32)
    aris=[]
    eval_unguided=0
    eval_guided=0
    independent_bits=0
    grouped_bits=0
    prev_groups=set()

    for t in range(T):
        vel=V[t].copy()
        if shuffle:
            vel=vel[rng.permutation(N)]
        S=similarity(P[t],vel)
        A=DECAY*A+(1-DECAY)*S
        np.fill_diagonal(A,1.0)
        pred=clusters_from_affinity(A)

        if t>=WARMUP:
            aris.append(ari_on_object_members(pred,truth))
            grouped = pred>=0
            eval_unguided += N*(2*UNGUIDED_RADIUS+1)**2
            eval_guided += int(grouped.sum())*(2*GUIDED_RADIUS+1)**2
            eval_guided += int((~grouped).sum())*(2*UNGUIDED_RADIUS+1)**2
            independent_bits += N*(GATE_INDEX_BITS+MOVE_BITS)

            for k in sorted(set(pred)):
                if k<0: continue
                ix=np.flatnonzero(pred==k)
                if len(ix)<DBSCAN_MIN: continue
                gv=np.median(V[t,ix],axis=0)
                grouped_bits += GROUP_ID_BITS+MOVE_BITS
                resid=np.linalg.norm(V[t,ix]-gv[None,:],axis=1)
                grouped_bits += int(np.sum(resid>RESID_THRESHOLD))*(GATE_INDEX_BITS+RESID_BITS)

            grouped_bits += int((pred<0).sum())*(GATE_INDEX_BITS+MOVE_BITS)
            groups=canonical_memberships(pred)
            added=groups-prev_groups
            grouped_bits += sum(len(g)*MEMBERSHIP_BITS for g in added)
            prev_groups=groups

    return {
        "mean_ari": float(np.mean(aris)),
        "median_ari": float(np.median(aris)),
        "eval_ratio": eval_guided/max(eval_unguided,1),
        "bit_ratio": grouped_bits/max(independent_bits,1),
        "independent_bits": independent_bits,
        "grouped_bits": grouped_bits,
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--seed",type=int,default=SEED)
    args=ap.parse_args()

    P,V,truth=simulate(args.seed,global_motion=False)
    main=run_relation(P,V,truth,False,args.seed)
    shuf=run_relation(P,V,truth,True,args.seed)
    Pg,Vg,tg=simulate(args.seed,global_motion=True)
    glob=run_relation(Pg,Vg,tg,False,args.seed)

    print("Gate C1 — transient motion matrix")
    print(f"objects: {N_GROUPS} x {PER_GROUP} primitives + {N_NOISE} independent distractors")
    print(f"main mean ARI               {main['mean_ari']:.3f}")
    print(f"main median ARI             {main['median_ari']:.3f}")
    print(f"guided / unguided evals     {main['eval_ratio']:.3f}")
    print(f"group / independent bits    {main['bit_ratio']:.3f}")
    print(f"bits: group {main['grouped_bits']}  independent {main['independent_bits']}")
    print(f"shuffled-motion mean ARI    {shuf['mean_ari']:.3f}")
    print(f"global-motion mean ARI      {glob['mean_ari']:.3f}  (diagnostic; collapse is expected)")

    passed=(
        main["mean_ari"]>=0.80
        and main["eval_ratio"]<=0.45
        and main["bit_ratio"]<=0.60
        and shuf["mean_ari"]<=0.35
    )
    print("RESULT:", "PASS" if passed else "FAIL")
    if glob["mean_ari"]>0.55:
        print("WARNING: global-motion control still looks object-specific; inspect the relation rule.")
    else:
        print("GLOBAL-MOTION CONTROL: correctly shows the limitation — common camera motion is not object identity.")
    return 0 if passed else 1

if __name__=="__main__":
    raise SystemExit(main())
