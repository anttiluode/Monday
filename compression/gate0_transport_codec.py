#!/usr/bin/env python3
"""
Monday / compression / Gate C0
Does an identity-preserving MOVE event reduce structural churn in the toy
Gabor codec compared with fixed-address death+birth?

This is an offline synthetic attack derived from GaborVideoCompression's
64x64 analytic dictionary and moving test scene. The moving codec is allowed
ONE extra primitive: an active Gabor atom may translate by at most one pixel
per frame before it is considered for death. Everything remains decoder-side
reconstructible from BIRTH / DEATH / AMP / MOVE events.

Not a production codec. The question is narrower:
    is some measured "churn" actually transport mis-described as destruction?
"""
from __future__ import annotations
import argparse, math
from dataclasses import dataclass
import numpy as np

SZ=64; NPX=SZ*SZ
K=100; B=5; DTH=.02
FRAMES=48
QLO,QHI,QL=np.log(.01),np.log(25),16

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
    q=int(round((np.log(m)-QLO)/(QHI-QLO)*(QL-1)))
    q=max(0,min(QL-1,q))
    return q, int(np.sign(v)), float(np.sign(v)*np.exp(QLO+q/(QL-1)*(QHI-QLO)))

def shift_atom(base,ox,oy):
    a=D[:,base].reshape(SZ,SZ)
    out=np.zeros_like(a)
    x0=max(0,ox); x1=min(SZ,SZ+ox)
    y0=max(0,oy); y1=min(SZ,SZ+oy)
    sx0=max(0,-ox); sx1=sx0+(x1-x0)
    sy0=max(0,-oy); sy1=sy0+(y1-y0)
    if x1>x0 and y1>y0:
        out[y0:y1,x0:x1]=a[sy0:sy1,sx0:sx1]
    z=out.ravel()
    n=float(np.linalg.norm(z))
    return z/(n+1e-12)

@dataclass
class Gate:
    base:int
    amp:float
    age:int=0
    qc:int|None=None
    qs:int|None=None
    ox:int=0
    oy:int=0
    uid:int=-1

class FixedCodec:
    def __init__(self):
        self.active={}
    def step(self,img):
        active=self.active
        ids=list(active)
        for _ in range(6):
            rec=D[:,ids]@np.array([active[a].amp for a in ids],np.float32) if ids else np.zeros(NPX,np.float32)
            r=img-rec
            if ids:
                c=D[:,ids].T@r
                for a,ci in zip(ids,c): active[a].amp+=.45*float(ci)
        deaths=[a for a in ids if abs(active[a].amp)<DTH]
        for a in deaths: del active[a]
        ids=list(active)
        rec=D[:,ids]@np.array([active[a].amp for a in ids],np.float32) if ids else np.zeros(NPX,np.float32)
        r=img-rec
        births=0
        for _ in range(B):
            if len(active)>=K: break
            c=D.T@r
            if ids: c[np.asarray(ids,dtype=int)]=0
            j=int(np.argmax(np.abs(c))); bc=float(c[j])
            if abs(bc)<DTH*1.6: break
            active[j]=Gate(j,bc); ids.append(j); births+=1
            r-=bc*D[:,j]
        updates=0
        for a,g in active.items():
            q,s,_=quant(g.amp)
            if g.age>0 and (q!=g.qc or s!=g.qs): updates+=1
            g.qc=q;g.qs=s;g.age+=1
        recq=np.zeros(NPX,np.float32)
        for a,g in active.items():
            _,_,qv=quant(g.amp); recq+=qv*D[:,a]
        bits=births*(12+5)+len(deaths)*8+updates*(8+5)+16
        churn=(births+len(deaths))/max(len(active),1)
        mse=float(np.mean((img-recq)**2))
        return bits,churn,mse,births,len(deaths),updates,0

class MoveCodec:
    def __init__(self):
        self.active=[]
        self.next_uid=0
        self.last_tracks=[]

    def reconstruction(self,quantized=False):
        rec=np.zeros(NPX,np.float32)
        for g in self.active:
            v=shift_atom(g.base,g.ox,g.oy)
            a=quant(g.amp)[2] if quantized else g.amp
            rec+=a*v
        return rec

    def step(self,img):
        rec=self.reconstruction(False)
        residual=img-rec
        moves=0
        motion_by_uid={}
        for g in self.active:
            old_ox,old_oy=g.ox,g.oy
            oldv=shift_atom(g.base,g.ox,g.oy)
            own_residual=residual+g.amp*oldv
            best=(abs(float(np.dot(oldv,own_residual))),g.ox,g.oy,float(np.dot(oldv,own_residual)),oldv)
            for dy in (-1,0,1):
                for dx in (-1,0,1):
                    if dx==0 and dy==0: continue
                    nox,noy=g.ox+dx,g.oy+dy
                    if abs(nox)>8 or abs(noy)>8: continue
                    v=shift_atom(g.base,nox,noy)
                    c=float(np.dot(v,own_residual))
                    cand=(abs(c),nox,noy,c,v)
                    if cand[0]>best[0]+1e-6: best=cand
            _,nox,noy,c,newv=best
            if nox!=g.ox or noy!=g.oy: moves+=1
            motion_by_uid[g.uid]=(nox-old_ox,noy-old_oy)
            g.ox,g.oy,g.amp=nox,noy,c
            residual=own_residual-c*newv

        if self.active:
            V=np.stack([shift_atom(g.base,g.ox,g.oy) for g in self.active],axis=1)
            amps=np.array([g.amp for g in self.active],np.float32)
            for _ in range(3):
                r=img-V@amps
                amps+=.38*(V.T@r)
            for g,a in zip(self.active,amps): g.amp=float(a)

        deaths=[g for g in self.active if abs(g.amp)<DTH]
        self.active=[g for g in self.active if abs(g.amp)>=DTH]

        rec=self.reconstruction(False); r=img-rec
        used={g.base for g in self.active if g.ox==0 and g.oy==0}
        births=0
        for _ in range(B):
            if len(self.active)>=K: break
            c=D.T@r
            if used: c[np.fromiter(used,int)]=0
            j=int(np.argmax(np.abs(c))); bc=float(c[j])
            if abs(bc)<DTH*1.6: break
            self.active.append(Gate(j,bc,uid=self.next_uid)); self.next_uid+=1; used.add(j);births+=1
            r-=bc*D[:,j]

        updates=0
        for g in self.active:
            q,s,_=quant(g.amp)
            if g.age>0 and (q!=g.qc or s!=g.qs): updates+=1
            g.qc=q;g.qs=s;g.age+=1

        recq=self.reconstruction(True)
        self.last_tracks=[]
        for g in self.active:
            if g.uid in motion_by_uid:
                dx,dy=motion_by_uid[g.uid]
                _,_,x0,y0,_,_=META[g.base]
                self.last_tracks.append((g.uid,float(x0+g.ox),float(y0+g.oy),float(dx),float(dy)))
        bits=births*(12+5)+len(deaths)*8+moves*(8+4)+updates*(8+5)+16
        churn=(births+len(deaths))/max(len(self.active),1)
        mse=float(np.mean((img-recq)**2))
        return bits,churn,mse,births,len(deaths),updates,moves

def psnr(mse): return 10*np.log10(1/max(mse,1e-12))

def run(codec):
    rows=[]
    for f in range(FRAMES):
        rows.append(codec.step(frame(f/12.0)))
    a=np.asarray(rows,float)
    steady=a[10:]
    return {
        "bits":float(steady[:,0].mean()),
        "churn":float(steady[:,1].mean()),
        "psnr":float(np.mean([psnr(x) for x in steady[:,2]])),
        "births":float(steady[:,3].mean()),
        "deaths":float(steady[:,4].mean()),
        "updates":float(steady[:,5].mean()),
        "moves":float(steady[:,6].mean()),
    }

def main():
    print(f"dictionary atoms: {NA} | K={K} | frames={FRAMES}")
    fixed=run(FixedCodec())
    moving=run(MoveCodec())
    print("Gate C0 — identity-preserving gate transport")
    for name,r in (("fixed",fixed),("moving",moving)):
        print(f"{name:6s} bits/frame {r['bits']:7.1f} | churn {100*r['churn']:5.2f}% | "
              f"PSNR {r['psnr']:5.2f} dB | b/d/u/m {r['births']:.2f}/{r['deaths']:.2f}/{r['updates']:.2f}/{r['moves']:.2f}")
    print(f"bit ratio moving/fixed   {moving['bits']/fixed['bits']:.3f}")
    print(f"churn ratio moving/fixed {moving['churn']/max(fixed['churn'],1e-9):.3f}")
    print(f"PSNR delta               {moving['psnr']-fixed['psnr']:+.2f} dB")
    passed=(moving["churn"]<0.90*fixed["churn"] and
            moving["psnr"]>=fixed["psnr"]-1.0 and
            moving["bits"]<=1.15*fixed["bits"])
    print("RESULT:", "PASS" if passed else "FAIL")
    return 0 if passed else 1

if __name__=="__main__":
    raise SystemExit(main())
