"""Faster/progress wrapper for FA-BSS0.

Uses the same experiment and FunctionalArbors v0.5 dynamics as fa_bss0_run.py,
but solves both terminal transfer functions in one sparse factorization and prints
progress around bootstrap/training arms so a long Windows run does not look hung.
"""

from __future__ import annotations

import time
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

import fa_bss0_run as core


def carrier_transfer_fast(model, omega: float | None = None) -> np.ndarray:
    """Same linearized carrier transfer as core, but solve both RHS together."""
    c = model.cfg
    omega = float(c.carrier_omega if omega is None else omega)
    z = np.exp(1j * omega)
    L = core.laplacian_sparse(model).astype(np.complex128)
    N = L.shape[0]
    alpha = (z - 1.0) * (1.0 - (1.0 - c.dt * c.damping) / z)
    alpha += (c.dt**2) * c.restoring
    M = alpha * sp.eye(N, format="csc") - (c.dt**2 * c.stiffness) * L.tocsc()

    rhs = np.zeros((N, 2), dtype=np.complex128)
    for which in (0, 1):
        p = model.source_terminal(which)
        if p is None:
            raise RuntimeError("arbor lost a source terminal")
        rhs[p[0] * c.size + p[1], which] = c.dt**2

    # One factorization, two right-hand sides.
    lu = spla.splu(M)
    P = lu.solve(rhs)
    soma_i = model.soma[0] * c.size + model.soma[1]
    return np.asarray(P[soma_i, :], dtype=np.complex128)


# Replace only the expensive diagnostic; learning logic is unchanged.
core.carrier_transfer = carrier_transfer_fast

_orig_load = core.load_functional_arbor


def load_with_progress(root: str):
    Arbor, Config = _orig_load(root)
    if not getattr(Arbor, "_monday_progress_patch", False):
        orig_bootstrap = Arbor.bootstrap

        def bootstrap_progress(self):
            t0 = time.perf_counter()
            print(f" seed {self.cfg.seed}: bootstrap starting...", flush=True)
            out = orig_bootstrap(self)
            print(
                f" seed {self.cfg.seed}: bootstrap done in {time.perf_counter()-t0:.1f}s "
                f"ok={out.get('ok')} mass={out.get('mass')}",
                flush=True,
            )
            return out

        Arbor.bootstrap = bootstrap_progress
        Arbor._monday_progress_patch = True
    return Arbor, Config


core.load_functional_arbor = load_with_progress

_orig_train = core.train_one


def train_with_progress(base, A, mode: str, mutations: int, seed: int):
    t0 = time.perf_counter()
    print(f" seed {seed}: {mode} arm starting ({mutations} mutations)...", flush=True)
    out = _orig_train(base, A, mode, mutations, seed)
    print(
        f" seed {seed}: {mode} arm done in {time.perf_counter()-t0:.1f}s",
        flush=True,
    )
    return out


core.train_one = train_with_progress


if __name__ == "__main__":
    core.main()
