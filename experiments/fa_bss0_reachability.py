"""FA-BSS0 reachability probe.

Before blaming ICA-like objectives or credit assignment, ask whether legal v0.5
morphologies can realize a useful complex terminal-to-soma ratio at all.

This is *not* an exhaustive reachable-set proof.  It performs unrewarded random
walks through the same legal detour/prune mutation space while mixed traffic
supplies eligibility, measuring H2/H1 after every retained proposal.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from fa_bss0_run import (
    carrier_transfer,
    ideal_ratio,
    load_functional_arbor,
    purity,
    traffic_episode,
)


def walk(base, A: np.ndarray, steps: int, seed: int):
    m = base.copy()
    m.mature = True
    m.protect = base.protect.copy()
    rng = np.random.default_rng(seed + 4567)

    rows = []

    def measure(step: int):
        H = carrier_transfer(m)
        q, G = purity(H, A)
        r = H[1] / H[0]
        rows.append({
            "step": int(step),
            "purity": float(q),
            "ratio": [float(r.real), float(r.imag)],
            "H": [[float(z.real), float(z.imag)] for z in H],
            "G": [[float(z.real), float(z.imag)] for z in G],
        })

    measure(0)
    accepted = 0
    for step in range(1, int(steps) + 1):
        traffic_episode(m, A, rng, steps=80)
        prop = m.propose_detour(int(rng.integers(2)))
        if prop is None:
            continue
        accepted += 1
        measure(step)
    return rows, accepted


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--fa-root", default="../FunctionalArbors")
    p.add_argument("--seeds", type=int, default=4)
    p.add_argument("--steps", type=int, default=50)
    p.add_argument("--bootstrap-mass", type=int, default=90)
    p.add_argument("--mix", default="1,.65,.4,1")
    p.add_argument("--out", default="fa_bss0_reachability.json")
    args = p.parse_args()

    vals = [float(x) for x in args.mix.split(",")]
    if len(vals) != 4:
        raise SystemExit("--mix needs four comma-separated numbers")
    A = np.asarray(vals, float).reshape(2, 2)
    if abs(np.linalg.det(A)) < 0.08:
        raise SystemExit("mixing matrix is too close to singular")

    FreeBinaryArbor, FreeConfig = load_functional_arbor(args.fa_root)
    rstar = ideal_ratio(A)
    payload = {
        "experiment": "FA-BSS0-reachability",
        "mixing_matrix": A.tolist(),
        "ideal_ratio": [float(rstar.real), float(rstar.imag)],
        "args": vars(args),
        "seeds": [],
    }

    print("FA-BSS0 reachability sample")
    print("ideal H2/H1 =", rstar)
    for seed in range(args.seeds):
        base = FreeBinaryArbor(FreeConfig(seed=seed, bootstrap_mass=args.bootstrap_mass))
        boot = base.bootstrap()
        if not boot.get("ok", False):
            print(f" seed {seed}: bootstrap failed")
            continue
        base.mature = True
        rows, accepted = walk(base, A, args.steps, seed)
        best = max(rows, key=lambda z: z["purity"])
        rr = complex(*best["ratio"])
        item = {
            "seed": seed,
            "bootstrap": boot,
            "accepted_random_walk_moves": accepted,
            "best_purity": best["purity"],
            "best_ratio": best["ratio"],
            "best_ratio_distance": float(abs(rr - rstar)),
            "rows": rows,
        }
        payload["seeds"].append(item)
        print(
            f" seed {seed:2d}: sampled={len(rows):3d} "
            f"best_purity={best['purity']:.4f} "
            f"ratio={rr.real:+.3f}{rr.imag:+.3f}j "
            f"|r-r*|={abs(rr-rstar):.3f}"
        )

    Path(args.out).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("wrote", args.out)


if __name__ == "__main__":
    main()
