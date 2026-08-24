"""FA-BSS0 -- supervised one-source extraction by FunctionalArbor geometry.

This deliberately imports the *actual* v0.5 FunctionalArbors implementation from
an adjacent checkout instead of reimplementing the medium in Monday.

Example (repos checked out side by side):
    python experiments/fa_bss0_run.py --fa-root ../FunctionalArbors --seeds 8

Gate 0 is supervised: hidden source labels are used only for the structural
accept/reject score.  The arbor's wave dynamics see only the two mixtures.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
import sys
from pathlib import Path

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla


def load_functional_arbor(root: str):
    root = str(Path(root).resolve())
    if root not in sys.path:
        sys.path.insert(0, root)
    from v05_free_arbor.free_arbor import FreeBinaryArbor, FreeConfig  # type: ignore
    return FreeBinaryArbor, FreeConfig


def laplacian_sparse(model) -> sp.csr_matrix:
    """Exact sparse matrix matching FreeBinaryArbor._lap for mature material."""
    kr, kl, kd, ku = model.bond_fields(True)
    n = model.cfg.size
    rows: list[int] = []
    cols: list[int] = []
    data: list[float] = []

    # shift(u,0,-1)[y,x] = u[y,x+1], etc. Out-of-grid shift values are 0,
    # so boundary bonds still contribute their -k*u diagonal term.
    directions = ((0, 1, kr), (0, -1, kl), (1, 0, kd), (-1, 0, ku))
    for y in range(n):
        for x in range(n):
            i = y * n + x
            diag = 0.0
            for dy, dx, field in directions:
                k = float(field[y, x])
                diag -= k
                yy, xx = y + dy, x + dx
                if 0 <= yy < n and 0 <= xx < n:
                    rows.append(i)
                    cols.append(yy * n + xx)
                    data.append(k)
            rows.append(i)
            cols.append(i)
            data.append(diag)
    N = n * n
    return sp.csr_matrix((data, (rows, cols)), shape=(N, N))


def carrier_transfer(model, omega: float | None = None) -> np.ndarray:
    """Small-signal steady-state complex gains [H1,H2] from terminals to soma.

    The v0.5 update before its weak saturation is
      v[t+1] = v[t] + dt*(K L psi[t] - d v[t] - r psi[t] + u[t])
      psi[t+1] = psi[t] + dt*v[t+1]

    For harmonic u[t] = U z^t, z=exp(i omega), solve the linearization around
    zero directly for the phasor P.  This measures what the frozen morphology
    itself implements without waiting for a long driven tone to settle.
    """
    c = model.cfg
    omega = float(c.carrier_omega if omega is None else omega)
    z = np.exp(1j * omega)
    L = laplacian_sparse(model).astype(np.complex128)
    N = L.shape[0]
    alpha = (z - 1.0) * (1.0 - (1.0 - c.dt * c.damping) / z)
    alpha += (c.dt**2) * c.restoring
    M = alpha * sp.eye(N, format="csr") - (c.dt**2 * c.stiffness) * L

    soma_i = model.soma[0] * c.size + model.soma[1]
    out = []
    for which in (0, 1):
        p = model.source_terminal(which)
        if p is None:
            out.append(np.nan + 1j * np.nan)
            continue
        U = np.zeros(N, dtype=np.complex128)
        U[p[0] * c.size + p[1]] = 1.0
        P = spla.spsolve(M, (c.dt**2) * U)
        out.append(P[soma_i])
    return np.asarray(out, dtype=np.complex128)


def source_gains(H: np.ndarray, A: np.ndarray) -> np.ndarray:
    return np.asarray(H) @ np.asarray(A)


def purity(H: np.ndarray, A: np.ndarray, target: int = 0) -> tuple[float, np.ndarray]:
    G = source_gains(H, A)
    power = np.abs(G) ** 2
    q = float(power[target] / (float(power.sum()) + 1e-15))
    return q, G


def ideal_ratio(A: np.ndarray, target: int = 0) -> complex:
    """Ideal H2/H1 for exact cancellation of the non-target source."""
    other = 1 - int(target)
    return complex(-A[0, other] / A[1, other])


def projective_error(H: np.ndarray, A: np.ndarray, target: int = 0) -> float:
    """Angle-like distance between physical H and ideal inverse row, scale free."""
    W = np.linalg.inv(A)
    w = np.asarray(W[target], dtype=np.complex128)
    h = np.asarray(H, dtype=np.complex128)
    hn = h / (np.linalg.norm(h) + 1e-15)
    wn = w / (np.linalg.norm(w) + 1e-15)
    overlap = float(np.clip(abs(np.vdot(wn, hn)), 0.0, 1.0))
    return float(math.acos(overlap))


def make_sources(rng: np.random.Generator, steps: int, block: int = 7) -> np.ndarray:
    """Two independent non-Gaussian envelopes with deliberately identical bandwidth."""
    nb = (steps + block - 1) // block
    s = rng.laplace(size=(2, nb))
    s = np.repeat(s, block, axis=1)[:, :steps]
    s -= s.mean(axis=1, keepdims=True)
    s /= s.std(axis=1, keepdims=True) + 1e-12
    return s


def traffic_episode(model, A: np.ndarray, rng: np.random.Generator, steps: int = 110, amp: float = 0.05):
    """Drive only mixtures through the two terminals and accumulate local eligibility."""
    s = make_sources(rng, steps)
    x = A @ s
    x /= max(1.0, float(np.max(np.abs(x))))
    p0, p1 = model.source_terminal(0), model.source_terminal(1)
    if p0 is None or p1 is None:
        raise RuntimeError("arbor lost a source terminal")

    model.reset_fast(clear_E=True)
    omega = float(model.cfg.carrier_omega)
    for t in range(steps):
        src = np.zeros_like(model.psi)
        phase = np.exp(1j * omega * t)
        src[p0] = amp * x[0, t] * phase
        src[p1] = amp * x[1, t] * phase
        model.advance(src, accumulate=True, mature=True)
    return s, x


def heldout_waveform_score(H: np.ndarray, A: np.ndarray, rng: np.random.Generator, n: int = 4096):
    """Frozen small-signal readout on fresh source realizations."""
    s = rng.laplace(size=(2, n))
    x = A @ s
    y = H @ x

    def coh(a, b):
        a = np.asarray(a) - np.mean(a)
        b = np.asarray(b) - np.mean(b)
        return float(abs(np.vdot(b, a)) / ((np.linalg.norm(a) * np.linalg.norm(b)) + 1e-15))

    return {"target_corr": coh(y, s[0]), "other_corr": coh(y, s[1])}


def train_one(base, A: np.ndarray, mode: str, mutations: int, seed: int):
    m = base.copy()
    m.mature = True
    # v0.5 copy() currently does not preserve the post-bootstrap protection mask.
    # Preserve it here so matched arms cannot move an endpoint simply because of copy().
    m.protect = base.protect.copy()
    rng = np.random.default_rng(seed + 120_001)

    H = carrier_transfer(m)
    score, G = purity(H, A)
    pre = {
        "purity": score,
        "H": [[float(z.real), float(z.imag)] for z in H],
        "G": [[float(z.real), float(z.imag)] for z in G],
        "ratio": [float((H[1] / H[0]).real), float((H[1] / H[0]).imag)],
        "projective_error": projective_error(H, A),
    }
    hist = []
    accepted = 0

    for step in range(int(mutations)):
        traffic_episode(m, A, rng)
        snap = m.snapshot()
        prop = m.propose_detour(int(rng.integers(2)))
        if prop is None:
            hist.append({"step": step, "proposal": None, "keep": False, "score": score})
            continue

        Hnew = carrier_transfer(m)
        new, Gnew = purity(Hnew, A)
        delta = new - score
        if mode == "reward":
            keep = delta > 1e-9
        elif mode == "anti":
            keep = delta < -1e-9
        elif mode == "shuffle":
            keep = delta * (1.0 if rng.random() < 0.5 else -1.0) > 1e-9
        elif mode == "random":
            keep = bool(rng.random() < 0.5)
        else:
            raise ValueError(mode)

        if keep:
            H, G, score = Hnew, Gnew, new
            accepted += 1
        else:
            m.restore(snap)

        hist.append({
            "step": step,
            "delta": float(delta),
            "keep": bool(keep),
            "score": float(score),
            "ratio": [float((H[1] / H[0]).real), float((H[1] / H[0]).imag)],
        })

    held = heldout_waveform_score(H, A, np.random.default_rng(seed + 990_001))
    return {
        "mode": mode,
        "accepted": accepted,
        "pre": pre,
        "post": {
            "purity": float(score),
            "H": [[float(z.real), float(z.imag)] for z in H],
            "G": [[float(z.real), float(z.imag)] for z in G],
            "ratio": [float((H[1] / H[0]).real), float((H[1] / H[0]).imag)],
            "projective_error": projective_error(H, A),
            **held,
        },
        "body": m.body.tolist(),
        "history": hist,
    }


def signflip(d: np.ndarray) -> float:
    d = np.asarray(d, float)
    n = len(d)
    if not n:
        return float("nan")
    obs = abs(float(d.mean()))
    if n <= 16:
        vals = [abs(float(np.mean(d * np.asarray(s)))) for s in itertools.product((-1.0, 1.0), repeat=n)]
    else:
        rng = np.random.default_rng(0)
        vals = [abs(float(np.mean(d * rng.choice([-1.0, 1.0], n)))) for _ in range(30000)]
    return float(np.mean(np.asarray(vals) >= obs - 1e-15))


def fastica_baseline(A: np.ndarray, seed: int, n: int = 10000):
    try:
        from sklearn.decomposition import FastICA
    except Exception as exc:  # pragma: no cover
        return {"available": False, "error": repr(exc)}
    rng = np.random.default_rng(seed + 700_001)
    s = rng.laplace(size=(2, n))
    x = (A @ s).T
    est = FastICA(n_components=2, whiten="unit-variance", random_state=seed, max_iter=2000).fit_transform(x).T
    C = np.abs(np.corrcoef(np.vstack([est, s]))[:2, 2:])
    best = max((C[0, 0] + C[1, 1]) / 2.0, (C[0, 1] + C[1, 0]) / 2.0)
    return {"available": True, "mean_best_abs_corr": float(best), "corr_matrix": C.tolist()}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--fa-root", default="../FunctionalArbors")
    p.add_argument("--seeds", type=int, default=8)
    p.add_argument("--mutations", type=int, default=28)
    p.add_argument("--bootstrap-mass", type=int, default=90)
    p.add_argument("--arms", default="reward,shuffle,anti")
    p.add_argument("--mix", default="1,.65,.4,1", help="row-major 2x2 mixing matrix")
    p.add_argument("--out", default="fa_bss0_out.json")
    args = p.parse_args()

    vals = [float(x) for x in args.mix.split(",")]
    if len(vals) != 4:
        raise SystemExit("--mix needs four comma-separated numbers")
    A = np.asarray(vals, float).reshape(2, 2)
    if abs(np.linalg.det(A)) < 0.08:
        raise SystemExit("mixing matrix is too close to singular for Gate 0")

    FreeBinaryArbor, FreeConfig = load_functional_arbor(args.fa_root)
    arms = [x.strip() for x in args.arms.split(",") if x.strip()]
    rows = []
    print("FA-BSS0: supervised structural source extraction")
    print("A =", A.tolist(), "ideal H2/H1 =", ideal_ratio(A))

    for seed in range(args.seeds):
        # Keep the original v0.5 dynamics, including its weak saturation.  The
        # transfer score is the corresponding small-signal linearization at zero.
        cfg = FreeConfig(seed=seed, bootstrap_mass=args.bootstrap_mass)
        base = FreeBinaryArbor(cfg)
        boot = base.bootstrap()
        if not boot.get("ok", False):
            print(f" seed {seed}: bootstrap failed")
            continue
        base.mature = True
        item = {"seed": seed, "bootstrap": boot, "arms": {}, "fastica": fastica_baseline(A, seed)}
        for mode in arms:
            r = train_one(base, A, mode, args.mutations, seed)
            item["arms"][mode] = r
            print(
                f" seed {seed:2d} {mode:7s}: "
                f"purity {r['pre']['purity']:.3f}->{r['post']['purity']:.3f} "
                f"corr={r['post']['target_corr']:.3f}/{r['post']['other_corr']:.3f} "
                f"accepted={r['accepted']}"
            )
        rows.append(item)

    summary = {}
    for mode in arms:
        rs = [z["arms"][mode] for z in rows if mode in z["arms"]]
        pre = np.asarray([r["pre"]["purity"] for r in rs])
        post = np.asarray([r["post"]["purity"] for r in rs])
        summary[mode] = {
            "n": len(rs),
            "pre_mean": float(pre.mean()) if len(pre) else float("nan"),
            "post_mean": float(post.mean()) if len(post) else float("nan"),
            "delta_mean": float((post - pre).mean()) if len(post) else float("nan"),
            "delta_values": (post - pre).tolist(),
        }
    if "reward" in arms and "shuffle" in arms:
        R = [z["arms"]["reward"]["post"]["purity"] for z in rows]
        S = [z["arms"]["shuffle"]["post"]["purity"] for z in rows]
        d = np.asarray(R) - np.asarray(S)
        summary["paired_reward_shuffle"] = {
            "mean": float(d.mean()) if len(d) else float("nan"),
            "values": d.tolist(),
            "signflip_p": signflip(d),
        }

    payload = {
        "experiment": "FA-BSS0",
        "mixing_matrix": A.tolist(),
        "ideal_ratio": [ideal_ratio(A).real, ideal_ratio(A).imag],
        "args": vars(args),
        "summary": summary,
        "rows": rows,
    }
    Path(args.out).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("summary:", json.dumps(summary, indent=2))
    print("wrote", args.out)


if __name__ == "__main__":
    main()
