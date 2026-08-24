#!/usr/bin/env python3
"""
Monday / compression / Gate C3

Move the transient relation matrix earlier than C2. C0 made each gate choose
a 3x3 move independently and C2 tried to group those already-jittery decisions
afterward. C3 instead:

  1. freezes the current reconstruction;
  2. measures each persistent gate's local move proposal before any move occurs;
  3. accumulates a decaying motion/proximity relation matrix over those proposals;
  4. forms temporary shared-motion groups;
  5. lets the group prediction guide a much smaller sequential residual search;
  6. charges membership, group move, residual override, birth/death and amp bits.

The critical attacker is a PRUNED NULL that uses the same frozen top-2 proposal
pruning but disables the transient matrix. That separates any matrix benefit
from the simpler benefit of not searching all 9 translations again.

This is a toy rate/distortion/search experiment, not object recognition and not
a production codec. Exact C3 thresholds were not preregistered before the first
run, so the script reports both the broad route and the matrix-incremental null.
"""
from __future__ import annotations
import math
from dataclasses import dataclass
import numpy as np

SZ=64; NPX=SZ*SZ
K=100; B=5; DTH=.02; FRAMES=48
QLO,QHI,QL=np.log(.01),np.log(25),16

# --- same analytic dictionary / scene as C0 ---
def build_dictionary():
    scales=[(2,4),(4,8),(8,16),(16,32)]
    atoms=[]; meta=[]; g=np.arange(SZ,dtype=np.float32)
    for si,(sig,st) in enumerate(scales):
        lam=2.2*sig
        for y0 in range(st//2,SZ,st):
            for x0 in range(st//2,SZ,st):
                Xr=g[None,:]-x0; Yr=g[:,None]-y0
                env=np.exp(-(Xr**2+Yr**2)/(2*sig**2)).astype(np.float32)
                atoms.append(env.copy()); meta.append((si,sig,x0,y0,-1,-1))
                for o in range(4):
                    th=np.pi*o/4; u=Xr*np.cos(th)+Yr*np.sin(th)
                    for pi,ph in enumerate((0.,np.pi/2)):
                        atoms.append((env*np.cos(2*np.pi*u/lam+ph)).astype(np.float32))
                        meta.append((si,sig,x0,y0,o,pi))
    D=np.stack([a.ravel() for a in atoms],axis=1).astype(np.float32)
    D/=np.linalg.norm(D,axis=0,keepdims=True)+1e-12
    return D,meta
D,META=build_dictionary(); NA=D.shape[1]

def frame(t):
    x=np.arange(SZ); X,Y=np.meshgrid(x,x)
    cx=32+16*np.cos(.6*t); cy=32+12*np.sin(.9*t)
    v=.30+.25*Y/SZ
    m=(X-cx)**2+(Y-cy)**2<130
    v[m]=.5+.35*np.sin(.9*X[m]+2*t)
    v[(np.abs(X-46)<8)&(np.abs(Y-18)<8)]=.12
    return np.clip(v,0,1).astype(np.float32).ravel()

def quant(v):
    m=np.clip(abs(v),.01,25)
    q=int(round((np.log(m)-QLO)/(QHI-QLO)*(QL-1))); q=max(0,min(QL-1,q))
    return q,int(np.sign(v)),float(np.sign(v)*np.exp(QLO+q/(QL-1)*(QHI-QLO)))

def shift_atom(base,ox,oy):
    a=D[:,base].reshape(SZ,SZ); out=np.zeros_like(a)
    x0=max(0,ox); x1=min(SZ,SZ+ox); y0=max(0,oy); y1=min(SZ,SZ+oy)
    sx0=max(0,-ox); sx1=sx0+(x1-x0); sy0=max(0,-oy); sy1=sy0+(y1-y0)
    if x1>x0 and y1>y0: out[y0:y1,x0:x1]=a[sy0:sy1,sx0:sx1]
    z=out.ravel(); return z/(np.linalg.norm(z)+1e-12)

@dataclass
class Gate:
    base:int; amp:float; age:int=0; qc:int|None=None; qs:int|None=None
    ox:int=0; oy:int=0; uid:int=-1

def psnr(mse): return 10*np.log10(1/max(mse,1e-12))

class FixedCodec:
    def __init__(self): self.active={}
    def step(self,img):
        active=self.active; ids=list(active)
        for _ in range(6):
            rec=D[:,ids]@np.array([active[a].amp for a in ids],np.float32) if ids else np.zeros(NPX,np.float32)
            r=img-rec
            if ids:
                c=D[:,ids].T@r
                for a,ci in zip(ids,c): active[a].amp+=.45*float(ci)
        deaths=[a for a in ids if abs(active[a].amp)<DTH]
        for a in deaths: del active[a]
        ids=list(active); rec=D[:,ids]@np.array([active[a].amp for a in ids],np.float32) if ids else np.zeros(NPX,np.float32); r=img-rec
        births=0
        for _ in range(B):
            if len(active)>=K: break
            c=D.T@r
            if ids: c[np.asarray(ids,dtype=int)]=0
            j=int(np.argmax(np.abs(c))); bc=float(c[j])
            if abs(bc)<DTH*1.6: break
            active[j]=Gate(j,bc); ids.append(j); births+=1; r-=bc*D[:,j]
        updates=0
        for a,g in active.items():
            q,s,_=quant(g.amp)
            if g.age>0 and (q!=g.qc or s!=g.qs): updates+=1
            g.qc=q; g.qs=s; g.age+=1
        recq=np.zeros(NPX,np.float32)
        for a,g in active.items(): recq+=quant(g.amp)[2]*D[:,a]
        bits=births*17+len(deaths)*8+updates*13+16
        return bits,(births+len(deaths))/max(len(active),1),float(np.mean((img-recq)**2)),births,len(deaths),updates,0,0,0

class IndependentMoveCodec:
    def __init__(self): self.active=[]; self.next_uid=0
    def reconstruction(self,q=False):
        rec=np.zeros(NPX,np.float32)
        for g in self.active: rec+=(quant(g.amp)[2] if q else g.amp)*shift_atom(g.base,g.ox,g.oy)
        return rec
    def step(self,img):
        residual=img-self.reconstruction(False); moves=0; evals=0
        for g in self.active:
            oldv=shift_atom(g.base,g.ox,g.oy); own=residual+g.amp*oldv
            best=None
            for dy in (-1,0,1):
                for dx in (-1,0,1):
                    nox,noy=g.ox+dx,g.oy+dy
                    if abs(nox)>8 or abs(noy)>8: continue
                    v=shift_atom(g.base,nox,noy); c=float(np.dot(v,own)); evals+=1
                    cand=(abs(c),nox,noy,c,v)
                    if best is None or cand[0]>best[0]+1e-6: best=cand
            _,nox,noy,c,newv=best
            if nox!=g.ox or noy!=g.oy: moves+=1
            g.ox,g.oy,g.amp=nox,noy,c; residual=own-c*newv
        if self.active:
            V=np.stack([shift_atom(g.base,g.ox,g.oy) for g in self.active],axis=1); amps=np.array([g.amp for g in self.active],np.float32)
            for _ in range(3):
                amps+=.38*(V.T@(img-V@amps))
            for g,a in zip(self.active,amps): g.amp=float(a)
        deaths=[g for g in self.active if abs(g.amp)<DTH]; self.active=[g for g in self.active if abs(g.amp)>=DTH]
        r=img-self.reconstruction(False); used={g.base for g in self.active if g.ox==0 and g.oy==0}; births=0
        for _ in range(B):
            if len(self.active)>=K: break
            c=D.T@r
            if used: c[np.fromiter(used,int)]=0
            j=int(np.argmax(np.abs(c))); bc=float(c[j])
            if abs(bc)<DTH*1.6: break
            self.active.append(Gate(j,bc,uid=self.next_uid)); self.next_uid+=1; used.add(j); births+=1; r-=bc*D[:,j]
        updates=0
        for g in self.active:
            q,s,_=quant(g.amp)
            if g.age>0 and (q!=g.qc or s!=g.qs): updates+=1
            g.qc=q;g.qs=s;g.age+=1
        bits=births*17+len(deaths)*8+moves*12+updates*13+16
        return bits,(births+len(deaths))/max(len(self.active),1),float(np.mean((img-self.reconstruction(True))**2)),births,len(deaths),updates,moves,evals,0

# --- C3: pre-decision local transport evidence -> transient matrix -> guided search ---
PAIR_DECAY=.76; PAIR_THRESHOLD=.24; SPACE_SIGMA=17.0; FLOW_SIGMA=.55; MIN_GROUP=3
MEMBER_BITS=8; GROUP_MOVE_BITS=8; RESID_BITS=12; IND_MOVE_BITS=12
PROPOSAL_GAIN_SCALE=.08; RESIDUAL_GAIN_MARGIN=.028

class PredictiveMatrix:
    def __init__(self): self.pairs={}; self.previous=[]
    @staticmethod
    def pair(a,b): return (a,b) if a<b else (b,a)
    def update(self,evidence):
        # evidence uid -> (x,y,dx,dy,confidence)
        live=set(evidence); nxt={}
        for p,w in self.pairs.items():
            if p[0] in live and p[1] in live:
                w*=PAIR_DECAY
                if w>.02: nxt[p]=w
        self.pairs=nxt
        ids=list(evidence)
        for ii,a in enumerate(ids):
            xa,ya,dxa,dya,ca=evidence[a]
            if ca<=0 or (abs(dxa)+abs(dya))==0: continue
            for b in ids[ii+1:]:
                xb,yb,dxb,dyb,cb=evidence[b]
                if cb<=0 or (abs(dxb)+abs(dyb))==0: continue
                dv=(dxa-dxb)**2+(dya-dyb)**2; dp=(xa-xb)**2+(ya-yb)**2
                sim=math.exp(-dv/(2*FLOW_SIGMA**2))*math.exp(-dp/(2*SPACE_SIGMA**2))*math.sqrt(ca*cb)
                if sim<.06: continue
                p=self.pair(a,b); old=self.pairs.get(p,0.0)
                self.pairs[p]=PAIR_DECAY*old+(1-PAIR_DECAY)*sim
        adj={u:set() for u in ids}
        for (a,b),w in self.pairs.items():
            if w>=PAIR_THRESHOLD and a in adj and b in adj:
                adj[a].add(b); adj[b].add(a)
        seen=set(); groups=[]
        for u in ids:
            if u in seen: continue
            stack=[u];seen.add(u);comp=[]
            while stack:
                q=stack.pop();comp.append(q)
                for v in adj[q]:
                    if v not in seen: seen.add(v);stack.append(v)
            if len(comp)>=MIN_GROUP:
                mv=np.array([[evidence[v][2],evidence[v][3]] for v in comp],float)
                gp=np.rint(np.median(mv,axis=0)).astype(int)
                if np.any(gp!=0): groups.append((set(comp),(int(gp[0]),int(gp[1]))))
        return groups
    def membership_cost(self,groups):
        curr=[set(g) for g,_ in groups]; unmatched=list(self.previous); cost=0
        for g in curr:
            bi=None; bj=0.0
            for i,p in enumerate(unmatched):
                j=len(g&p)/max(len(g|p),1)
                if j>bj: bi,bj=i,j
            if bi is not None and bj>=.55:
                p=unmatched.pop(bi); cost+=len(g^p)*MEMBER_BITS
            else: cost+=len(g)*MEMBER_BITS
        self.previous=curr
        return cost

class GroupGuidedCodec:
    def __init__(self):
        self.active=[]; self.next_uid=0; self.matrix=PredictiveMatrix()
    def reconstruction(self,q=False):
        rec=np.zeros(NPX,np.float32)
        for g in self.active: rec+=(quant(g.amp)[2] if q else g.amp)*shift_atom(g.base,g.ox,g.oy)
        return rec
    def proposals(self,img):
        # IMPORTANT C3 change: all local transport evidence is measured against
        # one frozen pre-decision reconstruction. No gate has moved yet, so
        # sequential residual updates cannot decorrelate a common motion before
        # the relation matrix sees it.
        if not self.active:
            return {}, {}
        rec=self.reconstruction(False); residual=img-rec
        evidence={}; score_maps={}
        for g in self.active:
            _,sig,x0,y0,_,_=META[g.base]; cx=float(x0+g.ox); cy=float(y0+g.oy)
            oldv=shift_atom(g.base,g.ox,g.oy); own=residual+g.amp*oldv
            scores={}
            best=None
            for dy in (-1,0,1):
                for dx in (-1,0,1):
                    nox,noy=g.ox+dx,g.oy+dy
                    if abs(nox)>8 or abs(noy)>8: continue
                    v=shift_atom(g.base,nox,noy); c=float(np.dot(v,own)); a=abs(c)
                    scores[(dx,dy)]=(a,c)
                    if best is None or a>best[0]+1e-6: best=(a,dx,dy,c)
            stay=scores.get((0,0),(0.0,0.0))[0]
            gain=max(0.0,best[0]-stay)
            dx,dy=int(best[1]),int(best[2])
            conf=float(np.clip(gain/PROPOSAL_GAIN_SCALE,0.0,1.0))
            # Zero-gain moves are not motion evidence even if tie-breaking found one.
            if gain<1e-6: dx=dy=0
            evidence[g.uid]=(cx,cy,dx,dy,conf)
            score_maps[g.uid]=scores
        return evidence,score_maps

    def step(self,img):
        ev,score_maps=self.proposals(img)
        groups=self.matrix.update(ev) if ev else []
        membership_bits=self.matrix.membership_cost(groups) if ev else 0
        group_of={}; group_pred={}
        for gi,(members,pred) in enumerate(groups):
            group_pred[gi]=pred
            for u in members: group_of[u]=gi

        # The matrix now acts BEFORE motion is committed. It proposes a cheap
        # shared transport. The final local update is still evaluated against
        # the *current sequential residual* (as in C0), but searches only the
        # shared prediction, the frozen individual proposal, and STAY.
        residual=img-self.reconstruction(False)
        moves=0; evals=0; chosen_delta={}
        for g in self.active:
            gi=group_of.get(g.uid,None); pred=group_pred.get(gi,(0,0))
            scores=score_maps.get(g.uid,{(0,0):(abs(g.amp),g.amp)})
            ranked=sorted(scores,key=lambda d:scores[d][0],reverse=True)[:2]
            candidates=[(0,0)]+ranked
            if gi is not None: candidates.append(pred)
            # unique and legal one-pixel deltas
            cand=[]
            for d in candidates:
                dx=max(-1,min(1,int(d[0]))); dy=max(-1,min(1,int(d[1])))
                if (dx,dy) not in cand: cand.append((dx,dy))
            oldv=shift_atom(g.base,g.ox,g.oy); own=residual+g.amp*oldv
            best=None
            for dx,dy in cand:
                nox,noy=g.ox+dx,g.oy+dy
                if abs(nox)>8 or abs(noy)>8: continue
                v=shift_atom(g.base,nox,noy); c=float(np.dot(v,own)); evals+=1
                # The shared move is cheaper to code than a residual override.
                penalty=0.0 if gi is None or (dx,dy)==pred else RESIDUAL_GAIN_MARGIN
                val=abs(c)-penalty
                q=(val,abs(c),nox,noy,c,v,dx,dy)
                if best is None or q[0]>best[0]+1e-6: best=q
            _,_,nox,noy,c,newv,dx,dy=best
            chosen_delta[g.uid]=(dx,dy)
            if dx or dy: moves+=1
            g.ox,g.oy,g.amp=nox,noy,c
            residual=own-c*newv

        # Now refit amplitudes jointly after the shared transport decision.
        if self.active:
            V=np.stack([shift_atom(g.base,g.ox,g.oy) for g in self.active],axis=1); amps=np.array([g.amp for g in self.active],np.float32)
            for _ in range(3):
                amps+=.38*(V.T@(img-V@amps))
            for g,a in zip(self.active,amps): g.amp=float(a)

        deaths=[g for g in self.active if abs(g.amp)<DTH]; self.active=[g for g in self.active if abs(g.amp)>=DTH]
        alive={g.uid for g in self.active}
        r=img-self.reconstruction(False); used={g.base for g in self.active if g.ox==0 and g.oy==0}; births=0
        for _ in range(B):
            if len(self.active)>=K: break
            c=D.T@r
            if used: c[np.fromiter(used,int)]=0
            j=int(np.argmax(np.abs(c))); bc=float(c[j])
            if abs(bc)<DTH*1.6: break
            self.active.append(Gate(j,bc,uid=self.next_uid));self.next_uid+=1;used.add(j);births+=1;r-=bc*D[:,j]
        updates=0
        for g in self.active:
            q,s,_=quant(g.amp)
            if g.age>0 and (q!=g.qc or s!=g.qs): updates+=1
            g.qc=q;g.qs=s;g.age+=1

        # motion bitstream: membership deltas + one shared move/group + residual overrides + independent movers
        motion_bits=membership_bits; grouped=set(); useful_groups=0; residuals=0
        for gi,(members,pred) in enumerate(groups):
            members=members & alive
            if len(members)<MIN_GROUP: continue
            grouped |= members; motion_bits+=GROUP_MOVE_BITS; useful_groups+=1
            for u in members:
                d=chosen_delta.get(u,(0,0))
                if d!=pred:
                    motion_bits+=RESID_BITS; residuals+=1
        for u,d in chosen_delta.items():
            if u in alive and u not in grouped and (d[0] or d[1]): motion_bits+=IND_MOVE_BITS
        bits=births*17+len(deaths)*8+updates*13+16+motion_bits
        mse=float(np.mean((img-self.reconstruction(True))**2)); churn=(births+len(deaths))/max(len(self.active),1)
        return bits,churn,mse,births,len(deaths),updates,moves,evals,useful_groups,motion_bits,residuals,membership_bits

def run(codec):
    rows=[]
    for f in range(FRAMES): rows.append(codec.step(frame(f/12.0)))
    return np.asarray(rows,float)[10:]

def main():
    print(f"dictionary atoms: {NA} | K={K} | frames={FRAMES}")
    fixed=run(FixedCodec())
    indep=run(IndependentMoveCodec())

    # Boring attacker: keep C3's frozen pre-decision top-2 proposal pruning,
    # but remove the transient matrix entirely. If grouped C3 cannot beat this,
    # the matrix has not earned credit for the saving.
    pruned_codec=GroupGuidedCodec()
    pruned_codec.matrix.update=lambda ev: []
    pruned_codec.matrix.membership_cost=lambda groups: 0
    pruned=run(pruned_codec)

    guided=run(GroupGuidedCodec())

    def summ(a):
        return dict(bits=a[:,0].mean(),churn=a[:,1].mean(),
                    psnr=np.mean([psnr(x) for x in a[:,2]]),
                    birth=a[:,3].mean(),death=a[:,4].mean(),upd=a[:,5].mean(),
                    moves=a[:,6].mean(),evals=a[:,7].mean())
    F,I,P,G=map(summ,(fixed,indep,pruned,guided))

    print("Gate C3 — pre-decision transient matrix + group-guided transport")
    for n,r in (("fixed",F),("indep",I),("pruned",P),("guided",G)):
        print(f"{n:7s} bits/frame {r['bits']:7.1f} | churn {100*r['churn']:5.2f}% | "
              f"PSNR {r['psnr']:5.2f} | moves {r['moves']:5.2f} | search {r['evals']:6.1f}")
    print(f"guided groups/frame           {guided[:,8].mean():6.2f}")
    print(f"guided motion bits/frame      {guided[:,9].mean():6.1f}")
    print(f"guided residuals/frame        {guided[:,10].mean():6.2f}")
    print(f"membership bits/frame         {guided[:,11].mean():6.1f}")
    print(f"guided / independent bits     {G['bits']/I['bits']:.3f}")
    print(f"guided / pruned-null bits     {G['bits']/P['bits']:.3f}")
    print(f"guided / fixed bits           {G['bits']/F['bits']:.3f}")
    print(f"guided / independent search   {G['evals']/I['evals']:.3f}")
    print(f"PSNR vs independent           {G['psnr']-I['psnr']:+.2f} dB")
    print(f"PSNR vs pruned null           {G['psnr']-P['psnr']:+.2f} dB")

    # These are interpretation lines, not preregistered thresholds: C3 was
    # proposed in the README before exact numerical stop lines were specified.
    route=(G['bits']<=.90*I['bits'] and G['evals']<=.35*I['evals']
           and G['psnr']>=I['psnr']-.5)
    matrix_incremental=(G['bits']<=.95*P['bits'] and G['psnr']>=P['psnr']-.25)
    strong=(G['bits']<=1.10*F['bits'] and G['psnr']>=F['psnr']-1.0)
    print("OVERALL GUIDED ROUTE:","PASS" if route else "FAIL")
    print("MATRIX INCREMENTAL OVER PRUNING NULL:","PASS" if matrix_incremental else "FAIL")
    print("STRONG FIXED-CODE COMPETITOR:","PASS" if strong else "FAIL")
    return 0 if route else 1

if __name__=='__main__': raise SystemExit(main())
