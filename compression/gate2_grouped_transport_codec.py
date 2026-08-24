#!/usr/bin/env python3
"""
Monday / compression / Gate C2
Take the FAILED C0 moving-gate codec and ask whether a transient relation matrix
can amortize its expensive per-gate MOVE events.

The image codec itself is unchanged from C0. This file only changes how the
already-chosen gate translations are described. A decaying pairwise matrix
binds persistent gates that repeatedly make similar local moves while nearby.
A temporary group can then receive one shared MOVE plus sparse residuals.

This is not semantic object recognition. A group means only:
    a temporary set of persistent primitives for which shared transport is a
    cheaper local model than independent transport.
"""
from __future__ import annotations
import math
import numpy as np
import gate0_transport_codec as c0

PAIR_DECAY=.82
PAIR_THRESHOLD=.36
SPACE_SIGMA=18.0
VEL_SIGMA=.60
MIN_GROUP=3
IND_MOVE_BITS=12
GROUP_MOVE_BITS=10
RESID_MOVE_BITS=12
MEMBER_BITS=8

class TransientGroups:
    def __init__(self):
        self.pairs={}
        self.previous=[]
        self.last_groups=[]

    @staticmethod
    def _pair(a,b): return (a,b) if a<b else (b,a)

    def update(self,tracks):
        ids=[int(t[0]) for t in tracks]
        data={int(t[0]):np.asarray(t[1:],float) for t in tracks}
        live=set(ids)
        nxt={}
        for pair,w in self.pairs.items():
            if pair[0] in live and pair[1] in live:
                w*=PAIR_DECAY
                if w>.025: nxt[pair]=w
        self.pairs=nxt

        for i,a in enumerate(ids):
            xa,ya,dxa,dya=data[a]
            va=np.array([dxa,dya])
            for b in ids[i+1:]:
                xb,yb,dxb,dyb=data[b]
                vb=np.array([dxb,dyb])
                if np.allclose(va,0) and np.allclose(vb,0):
                    continue
                dv=va-vb
                dp=np.array([xa-xb,ya-yb])
                sim=math.exp(-float(dv@dv)/(2*VEL_SIGMA**2))
                sim*=math.exp(-float(dp@dp)/(2*SPACE_SIGMA**2))
                if sim<.08: continue
                p=self._pair(a,b)
                old=self.pairs.get(p,0.0)
                self.pairs[p]=PAIR_DECAY*old+(1-PAIR_DECAY)*sim

        adj={u:set() for u in ids}
        for (a,b),w in self.pairs.items():
            if w>=PAIR_THRESHOLD and a in adj and b in adj:
                adj[a].add(b);adj[b].add(a)
        seen=set();groups=[]
        for u in ids:
            if u in seen: continue
            stack=[u];seen.add(u);comp=[]
            while stack:
                q=stack.pop();comp.append(q)
                for v in adj[q]:
                    if v not in seen: seen.add(v);stack.append(v)
            if len(comp)>=MIN_GROUP: groups.append(set(comp))
        self.last_groups=groups
        return groups,data

    def membership_cost(self,groups):
        unmatched=list(self.previous)
        cost=0
        for g in groups:
            best_i=None;best_j=0.0
            for i,p in enumerate(unmatched):
                j=len(g&p)/max(len(g|p),1)
                if j>best_j: best_i,best_j=i,j
            if best_i is not None and best_j>=.55:
                p=unmatched.pop(best_i)
                cost += len(g^p)*MEMBER_BITS
            else:
                cost += len(g)*MEMBER_BITS
        self.previous=[set(g) for g in groups]
        return cost

    def encode_moves(self,groups,data):
        grouped=set()
        bits=self.membership_cost(groups)
        for g in groups:
            grouped |= g
            vel=np.array([data[u][2:4] for u in g])
            gv=np.rint(np.median(vel,axis=0)).astype(int)
            movers=np.any(np.abs(vel)>.1,axis=1)
            if np.any(gv!=0):
                bits += GROUP_MOVE_BITS
                residual=np.any(np.abs(vel-gv[None,:])>.1,axis=1)
                bits += int(residual.sum())*RESID_MOVE_BITS
            else:
                bits += int(movers.sum())*IND_MOVE_BITS

        for u,v in data.items():
            if u not in grouped and np.any(np.abs(v[2:4])>.1):
                bits += IND_MOVE_BITS
        return bits

def main():
    fixed=c0.FixedCodec()
    moving=c0.MoveCodec()
    groups=TransientGroups()
    rows=[]
    for f in range(c0.FRAMES):
        img=c0.frame(f/12.0)
        fb=fixed.step(img)
        mb=moving.step(img)
        gs,data=groups.update(moving.last_tracks)
        grouped_move_bits=groups.encode_moves(gs,data)
        independent_move_bits=mb[6]*IND_MOVE_BITS
        grouped_total=mb[0]-independent_move_bits+grouped_move_bits
        rows.append((fb[0],mb[0],grouped_total,fb[1],mb[1],fb[2],mb[2],
                     mb[6],len(gs),grouped_move_bits))
    a=np.asarray(rows,float)[10:]
    fixed_bits=a[:,0].mean()
    move_bits=a[:,1].mean()
    grouped_bits=a[:,2].mean()
    print("Gate C2 — transient matrix over real C0 gate moves")
    print(f"fixed-address bits/frame      {fixed_bits:7.1f}")
    print(f"individual-MOVE bits/frame    {move_bits:7.1f}")
    print(f"grouped-MOVE bits/frame       {grouped_bits:7.1f}")
    print(f"grouped / individual          {grouped_bits/move_bits:.3f}")
    print(f"grouped / fixed               {grouped_bits/fixed_bits:.3f}")
    print(f"fixed churn                   {100*a[:,3].mean():5.2f}%")
    print(f"moving churn                  {100*a[:,4].mean():5.2f}%")
    print(f"fixed PSNR                    {np.mean([c0.psnr(x) for x in a[:,5]]):5.2f} dB")
    print(f"moving PSNR                   {np.mean([c0.psnr(x) for x in a[:,6]]):5.2f} dB")
    print(f"moves/frame                   {a[:,7].mean():5.2f}")
    print(f"transient groups/frame        {a[:,8].mean():5.2f}")
    print(f"group-motion sidebits/frame   {a[:,9].mean():7.1f}")
    pass0=(grouped_bits <= .78*move_bits)
    strong=(grouped_bits < fixed_bits*1.05)
    print("RESULT:", "PASS" if pass0 else "FAIL",
          "| strong fixed-code competitor:", "PASS" if strong else "FAIL")
    return 0 if pass0 else 1

if __name__=="__main__":
    raise SystemExit(main())
