"""Validate Monday's sparse carrier solve against direct v0.5 time stepping.

The comparison is projective (H2/H1), because the demixing direction rather than
an arbitrary common complex scale is what FA-BSS0 uses.
"""

from __future__ import annotations

import argparse

import numpy as np

from fa_bss0_run import carrier_transfer, load_functional_arbor


def direct_gain(model, which: int, steps: int, burn: int, amp: float = 1e-3):
    c = model.cfg
    p = model.source_terminal(which)
    if p is None:
        raise RuntimeError("missing source terminal")
    model.reset_fast(clear_E=False)
    samples = []
    for t in range(steps):
        src = np.zeros_like(model.psi)
        src[p] = amp * np.exp(1j * c.carrier_omega * t)
        model.advance(src, accumulate=False, mature=True)
        if t >= burn:
            samples.append(model.psi[model.soma] * np.exp(-1j * c.carrier_omega * t) / amp)
    return np.mean(np.asarray(samples))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--fa-root", default="../FunctionalArbors")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--steps", type=int, default=2200)
    p.add_argument("--burn", type=int, default=1600)
    p.add_argument("--tol", type=float, default=0.01)
    args = p.parse_args()

    FreeBinaryArbor, FreeConfig = load_functional_arbor(args.fa_root)
    m = FreeBinaryArbor(FreeConfig(seed=args.seed, bootstrap_mass=90))
    boot = m.bootstrap()
    if not boot.get("ok", False):
        raise SystemExit("bootstrap failed")
    m.mature = True

    Ha = carrier_transfer(m)
    Hd = np.asarray([direct_gain(m, k, args.steps, args.burn) for k in (0, 1)])
    ra = Ha[1] / Ha[0]
    rd = Hd[1] / Hd[0]
    err = abs(ra - rd)

    print("analytic H =", Ha, "ratio =", ra)
    print("direct   H =", Hd, "ratio =", rd)
    print("ratio absolute error =", err)
    if not np.isfinite(err) or err > args.tol:
        raise SystemExit(f"FAIL: ratio error {err} > tolerance {args.tol}")
    print("PASS")


if __name__ == "__main__":
    main()
