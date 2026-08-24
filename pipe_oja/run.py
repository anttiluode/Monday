"""PIPE-OJA-BRANCH0 -- does branching earn its existence?

A deliberately small gate between the old "self-normalizing pipe" idea and
Monday's ICA/IVA direction.

Both organisms see the same whitened two-sensor convolutive mixture, begin from
the same two direct pipes, have the same total structural mass M=1, and receive
the same blind broadband learning pressure.

The only difference is the feasible morphology:

    cable   : exactly one delay-pipe from each sensor may carry mass.
    branch  : mass may split over many delay-pipes from either sensor.

Each delay-pipe p=(sensor i, delay d) contributes

    q_p[k,t] = rho**d * exp(-1j*omega[k]*d) * x_i[k,t]

to the soma. Its non-negative mass m_p scales that contribution:

    y[k,t] = sum_p m_p q_p[k,t].

So moving fixed mass between delays changes one physical transfer curve H_i(w)
rather than setting an independent complex matrix coefficient at every
frequency.

Blind pressure
--------------
For each time frame let

    r_t = sqrt(mean_k |y[k,t]|^2).

We minimize the scale-invariant radial sparsity contrast

    J = E[r] / sqrt(E[r^2]).

For super-Gaussian independent source-vectors this favors a single source over a
mixture, but it does not use source labels. The exact gradient with respect to
one pipe mass contains a nonlinear Hebbian term plus a normalizing term:

    v_p(t) = Re(mean_k conj(y[k,t]) * q_p[k,t])

    dJ/dm_p =
        E[v_p/r] / sqrt(E[r^2])
        - E[r] E[v_p] / E[r^2]^(3/2).

That is the connection to the earlier pipe-Oja language: local transported
signal times a soma-derived nonlinear score, followed by competition for a
fixed mass budget. It is Oja-like, not a claim that this is Oja's literal PCA
rule or a biological dendrite rule.

After every step the same raw gradient is projected onto the arm's morphology
constraint. No hidden source is consulted during learning. Source labels are
used only after freezing for the diagnostic purity score and for capacity
attackers.

The shuffled arm destroys time alignment between pipe current and soma score.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
from scipy.optimize import minimize

EPS = 1e-12


@dataclass
class Config:
    bins: int = 18
    frames: int = 1400
    delays: int = 11
    rho: float = 0.97
    omega_lo_pi: float = 0.14
    omega_hi_pi: float = 0.86
    steps: int = 180
    eta: float = 0.12
    seeds: int = 8
    active_eps: float = 1e-3
    cable_grid: int = 301
    branch_capacity_starts: int = 2


def basis(cfg: Config) -> tuple[np.ndarray, np.ndarray]:
    omega = np.linspace(
        cfg.omega_lo_pi * np.pi,
        cfg.omega_hi_pi * np.pi,
        cfg.bins,
        dtype=float,
    )
    d = np.arange(cfg.delays, dtype=float)[:, None]
    b = (cfg.rho**d) * np.exp(-1j * d * omega[None, :])
    return omega, b.astype(np.complex128)


def mixing_matrices(omega: np.ndarray) -> np.ndarray:
    """A fixed, nontrivial 2x2 convolutive mixture over frequency."""
    A = np.zeros((len(omega), 2, 2), np.complex128)
    for k, w in enumerate(omega):
        A[k, 0, 0] = 1.0
        A[k, 0, 1] = 0.75 * np.exp(-1j * w * 2.0) + 0.35 * np.exp(-1j * w * 5.0)
        A[k, 1, 0] = 0.65 * np.exp(-1j * w * 1.0) + 0.25 * np.exp(-1j * w * 4.0)
        A[k, 1, 1] = 1.0
    return A


def source_vectors(rng: np.random.Generator, cfg: Config) -> np.ndarray:
    """Two independent super-Gaussian IVA-style source vectors."""
    S = np.empty((2, cfg.bins, cfg.frames), np.complex128)
    for j in range(2):
        radial = rng.exponential(scale=1.0, size=cfg.frames) + 0.05
        z = (
            rng.normal(size=(cfg.bins, cfg.frames))
            + 1j * rng.normal(size=(cfg.bins, cfg.frames))
        ) / math.sqrt(2.0)
        z /= np.sqrt(np.mean(np.abs(z) ** 2, axis=0, keepdims=True)) + EPS
        S[j] = z * radial[None, :]
    return S


def whiten_frequency_bins(X: np.ndarray, A: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Whiten the two observed sensors independently at each frequency."""
    _, K, T = X.shape
    Xw = np.empty_like(X)
    Aw = np.empty_like(A)
    V = np.empty_like(A)
    for k in range(K):
        C = (X[:, k, :] @ X[:, k, :].conj().T) / float(T)
        vals, vecs = np.linalg.eigh(C)
        Vk = (vecs * (1.0 / np.sqrt(vals + 1e-9))) @ vecs.conj().T
        V[k] = Vk
        Xw[:, k, :] = Vk @ X[:, k, :]
        Aw[k] = Vk @ A[k]
    return Xw, Aw, V


def make_problem(seed: int, cfg: Config):
    omega, B = basis(cfg)
    A = mixing_matrices(omega)
    S = source_vectors(np.random.default_rng(seed + 100_000), cfg)
    X = np.einsum("kij,jkt->ikt", A, S)
    Xw, Aw, V = whiten_frequency_bins(X, A)
    Q = Xw[:, None, :, :] * B[None, :, :, None]
    return {"omega": omega, "basis": B, "A": A, "Aw": Aw, "V": V, "Xw": Xw, "Q": Q}


def pipe_output(m: np.ndarray, Xw: np.ndarray, B: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    H = np.einsum("id,dk->ik", m, B)
    Y = np.einsum("ik,ikt->kt", H, Xw)
    return Y, H


def radial_objective(Y: np.ndarray) -> float:
    r = np.sqrt(np.mean(np.abs(Y) ** 2, axis=0) + EPS)
    return float(r.mean() / np.sqrt(np.mean(r * r) + EPS))


def pipe_gradient(
    m: np.ndarray,
    Xw: np.ndarray,
    Q: np.ndarray,
    B: np.ndarray,
    *,
    shuffle_score: bool,
    rng: np.random.Generator,
) -> tuple[np.ndarray, float, np.ndarray, np.ndarray]:
    Y, H = pipe_output(m, Xw, B)
    r = np.sqrt(np.mean(np.abs(Y) ** 2, axis=0) + EPS)
    er = float(r.mean())
    er2 = float(np.mean(r * r))

    if shuffle_score:
        idx = rng.permutation(Y.shape[1])
        Yscore = Y[:, idx]
        rscore = r[idx]
    else:
        Yscore = Y
        rscore = r

    v = np.real(np.einsum("kt,idkt->idt", np.conj(Yscore), Q, optimize=True)) / float(Y.shape[0])
    nonlinear_hebb = (v / (rscore[None, None, :] + EPS)).mean(axis=2)
    linear_corr = v.mean(axis=2)
    grad = nonlinear_hebb / math.sqrt(er2 + EPS) - er * linear_corr / ((er2 + EPS) ** 1.5)
    return grad, radial_objective(Y), Y, H


def project_simplex(v: np.ndarray, mass: float = 1.0) -> np.ndarray:
    """Euclidean projection onto m>=0, sum(m)=mass."""
    shape = v.shape
    x = np.asarray(v, float).ravel()
    u = np.sort(x)[::-1]
    cssv = np.cumsum(u) - mass
    ind = np.arange(1, len(x) + 1)
    keep = u - cssv / ind > 0
    if not np.any(keep):
        out = np.zeros_like(x)
        out[int(np.argmax(x))] = mass
        return out.reshape(shape)
    rho = int(ind[keep][-1])
    theta = float(cssv[keep][-1] / rho)
    return np.maximum(x - theta, 0.0).reshape(shape)


def project_two(v: np.ndarray, mass: float = 1.0) -> np.ndarray:
    return project_simplex(np.asarray(v, float), mass).ravel()


def project_cable(v: np.ndarray) -> tuple[np.ndarray, tuple[int, int]]:
    """Project onto the one-delay-pipe-per-sensor morphology."""
    D = v.shape[1]
    base = float(np.sum(v * v))
    best_err = math.inf
    best_m = None
    best_pair = None
    for d0 in range(D):
        for d1 in range(D):
            a = project_two(np.array([v[0, d0], v[1, d1]]), 1.0)
            err = (
                base
                - float(v[0, d0] ** 2)
                - float(v[1, d1] ** 2)
                + float((a[0] - v[0, d0]) ** 2)
                + float((a[1] - v[1, d1]) ** 2)
            )
            if err < best_err:
                m = np.zeros_like(v)
                m[0, d0] = a[0]
                m[1, d1] = a[1]
                best_err = err
                best_m = m
                best_pair = (d0, d1)
    assert best_m is not None and best_pair is not None
    return best_m, best_pair


def source_purity(H: np.ndarray, Aw: np.ndarray) -> dict:
    """Ground-truth diagnostic only; never called by the learning update."""
    G = np.einsum("ik,kij->kj", H, Aw)
    power = np.sum(np.abs(G) ** 2, axis=0)
    frac = power / (float(power.sum()) + EPS)
    winner = int(np.argmax(frac))
    return {
        "best_purity": float(frac[winner]),
        "component": winner,
        "source_power_fraction": frac.tolist(),
    }


def record(step: int, m: np.ndarray, problem, cfg: Config) -> dict:
    Y, H = pipe_output(m, problem["Xw"], problem["basis"])
    p = source_purity(H, problem["Aw"])
    return {
        "step": int(step),
        "objective": radial_objective(Y),
        **p,
        "active_pipes": int(np.sum(m > cfg.active_eps)),
        "mass_sum": float(m.sum()),
        "mass": m.tolist(),
    }


def train_arm(seed: int, arm: str, cfg: Config, problem=None) -> dict:
    problem = make_problem(seed, cfg) if problem is None else problem
    rng = np.random.default_rng(seed + 900_001)
    m = np.zeros((2, cfg.delays), float)
    m[:, 0] = 0.5
    hist = [record(0, m, problem, cfg)]
    shuffle = arm == "branch_shuffle"

    for step in range(1, cfg.steps + 1):
        grad, _, _, _ = pipe_gradient(
            m,
            problem["Xw"],
            problem["Q"],
            problem["basis"],
            shuffle_score=shuffle,
            rng=rng,
        )
        raw = m - cfg.eta * grad
        if arm in ("branch", "branch_shuffle"):
            m = project_simplex(raw, 1.0)
        elif arm == "cable":
            m, _ = project_cable(raw)
        else:
            raise ValueError(arm)
        if step == cfg.steps or step % 10 == 0:
            hist.append(record(step, m, problem, cfg))

    return {"arm": arm, "seed": seed, "final": record(cfg.steps, m, problem, cfg), "history": hist}


def cable_capacity(problem, cfg: Config) -> dict:
    """Supervised representational attacker: best possible one-path cable."""
    B = problem["basis"]
    Aw = problem["Aw"]
    aa = np.linspace(0.0, 1.0, cfg.cable_grid)
    best = (-1.0, None)
    for d0 in range(cfg.delays):
        for d1 in range(cfg.delays):
            h0 = aa[:, None] * B[d0][None, :]
            h1 = (1.0 - aa)[:, None] * B[d1][None, :]
            H = np.stack([h0, h1], axis=1)
            G = np.einsum("nik,kij->nkj", H, Aw)
            power = np.sum(np.abs(G) ** 2, axis=1)
            pur = np.max(power / (power.sum(axis=1, keepdims=True) + EPS), axis=1)
            i = int(np.argmax(pur))
            if float(pur[i]) > best[0]:
                best = (
                    float(pur[i]),
                    {"delay0": d0, "delay1": d1, "mass0": float(aa[i]), "mass1": float(1.0 - aa[i])},
                )
    return {"best_purity": best[0], **best[1]}


def branch_capacity(problem, cfg: Config) -> dict:
    """Supervised capacity attacker for the branching pipe bank."""
    B = problem["basis"]
    Aw = problem["Aw"]
    n = 2 * cfg.delays

    def purity(v, target):
        m = np.asarray(v, float).reshape(2, cfg.delays)
        H = np.einsum("id,dk->ik", m, B)
        G = np.einsum("ik,kij->kj", H, Aw)
        power = np.sum(np.abs(G) ** 2, axis=0)
        return float(power[target] / (power.sum() + EPS))

    cons = {"type": "eq", "fun": lambda v: np.sum(v) - 1.0}
    bounds = [(0.0, 1.0)] * n
    best_p = -1.0
    best_v = None
    best_target = None
    for target in (0, 1):
        for j in range(cfg.branch_capacity_starts):
            r = np.random.default_rng(70_000 + 100 * target + j)
            x0 = r.dirichlet(np.ones(n))
            fit = minimize(
                lambda v: -purity(v, target),
                x0,
                method="SLSQP",
                bounds=bounds,
                constraints=cons,
                options={"maxiter": 400, "ftol": 1e-9, "disp": False},
            )
            p = -float(fit.fun)
            if p > best_p:
                best_p = p
                best_v = np.asarray(fit.x, float)
                best_target = target
    return {"best_purity": float(best_p), "component": int(best_target), "mass": best_v.reshape(2, cfg.delays).tolist()}


def signflip(d: np.ndarray) -> float:
    d = np.asarray(d, float)
    n = len(d)
    obs = abs(float(d.mean()))
    vals = []
    for signs in itertools.product((-1.0, 1.0), repeat=n):
        vals.append(abs(float(np.mean(d * np.asarray(signs)))))
    return float(np.mean(np.asarray(vals) >= obs - 1e-15))


def summarize(rows: list[dict]) -> dict:
    arms = ("branch", "cable", "branch_shuffle")
    out = {}
    for arm in arms:
        vals = np.asarray([row["arms"][arm]["final"]["best_purity"] for row in rows], float)
        objs = np.asarray([row["arms"][arm]["final"]["objective"] for row in rows], float)
        active = np.asarray([row["arms"][arm]["final"]["active_pipes"] for row in rows], float)
        out[arm] = {
            "mean_purity": float(vals.mean()),
            "purity_values": vals.tolist(),
            "mean_objective": float(objs.mean()),
            "mean_active_pipes": float(active.mean()),
        }

    b = np.asarray(out["branch"]["purity_values"])
    c = np.asarray(out["cable"]["purity_values"])
    s = np.asarray(out["branch_shuffle"]["purity_values"])
    cap = np.asarray([r["cable_capacity"]["best_purity"] for r in rows])
    bcap = np.asarray([r["branch_capacity"]["best_purity"] for r in rows])
    out["comparisons"] = {
        "branch_minus_cable_mean": float(np.mean(b - c)),
        "branch_minus_cable_p": signflip(b - c),
        "branch_minus_shuffle_mean": float(np.mean(b - s)),
        "branch_minus_shuffle_p": signflip(b - s),
        "mean_cable_capacity": float(cap.mean()),
        "mean_branch_capacity": float(bcap.mean()),
        "branch_minus_cable_capacity_values": (b - cap).tolist(),
        "all_branch_above_cable_capacity": bool(np.all(b > cap)),
    }
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=8)
    ap.add_argument("--steps", type=int, default=180)
    ap.add_argument("--eta", type=float, default=0.12)
    ap.add_argument("--frames", type=int, default=1400)
    ap.add_argument("--out", default="pipe_oja_branch0.json")
    args = ap.parse_args()
    cfg = Config(seeds=args.seeds, steps=args.steps, eta=args.eta, frames=args.frames)

    rows = []
    print("PIPE-OJA-BRANCH0")
    print("same initial pipes; same total mass; same blind broadband gradient")
    print("arms: branch / cable / branch_shuffle")
    for seed in range(cfg.seeds):
        problem = make_problem(seed, cfg)
        item = {
            "seed": seed,
            "arms": {},
            "cable_capacity": cable_capacity(problem, cfg),
            "branch_capacity": branch_capacity(problem, cfg),
        }
        for arm in ("branch", "cable", "branch_shuffle"):
            r = train_arm(seed, arm, cfg, problem=problem)
            item["arms"][arm] = r
            f = r["final"]
            print(f" seed {seed:2d} {arm:14s} J={f['objective']:.4f} purity={f['best_purity']:.4f} active={f['active_pipes']:2d} mass={f['mass_sum']:.9f}")
        print(f"          capacity: cable={item['cable_capacity']['best_purity']:.4f} branch={item['branch_capacity']['best_purity']:.4f}")
        rows.append(item)

    result = {"gate": "PIPE-OJA-BRANCH0", "config": asdict(cfg), "rows": rows}
    result["summary"] = summarize(rows)
    out = Path(args.out)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")

    s = result["summary"]
    print("\nSUMMARY")
    print(" branch purity       ", f"{s['branch']['mean_purity']:.4f}")
    print(" cable purity        ", f"{s['cable']['mean_purity']:.4f}")
    print(" branch shuffle      ", f"{s['branch_shuffle']['mean_purity']:.4f}")
    print(" cable capacity      ", f"{s['comparisons']['mean_cable_capacity']:.4f}")
    print(" branch capacity     ", f"{s['comparisons']['mean_branch_capacity']:.4f}")
    print(" branch-cable        ", f"{s['comparisons']['branch_minus_cable_mean']:+.4f}", f"p={s['comparisons']['branch_minus_cable_p']:.5f}")
    print(" branch-shuffle      ", f"{s['comparisons']['branch_minus_shuffle_mean']:+.4f}", f"p={s['comparisons']['branch_minus_shuffle_p']:.5f}")
    print(" all learned branches above cable capacity:", s["comparisons"]["all_branch_above_cable_capacity"])
    print("wrote", out)


if __name__ == "__main__":
    main()
