"""FA-BSS-CONV0 -- controlled convolutive target with a rotating demixing row.

REAL1B exposed a bad target: raw AuxIVA ratios looked dramatic but a single
frequency-independent projective direction explained them much better than the
arbor.  CONV0 chooses the mixing physics before training and makes that escape
route impossible by construction.

Synthetic FIR world
-------------------
    x1[t] = s1[t] + 0.90 s2[t-14]
    x2[t] = 0.35 s1[t-3] + s2[t]

A frequency-domain source-1 extraction row is, up to projective scale,

    w(omega) = [1, -0.90 exp(-i 14 omega)].

The target therefore has constant coefficient magnitude but a deliberately
rotating phase.  The exact matched FIR extractor is boring and perfect:

    y[t] = x1[t] - 0.90 x2[t-14].

This script does NOT test blind learning.  It tests whether one existing
FunctionalArbor morphology can be structurally compiled toward that coherent
nonconstant operator, plus held-out-frequency and shuffled-order controls.
See notes/conv0_rotating_demixer_contract.md for the pre-registered gate.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

import fa_bss_real0 as r0
import fa_bss_real1b_broadband as b1

EPS = 1e-12

# Frozen before first run; mirrored in the contract.
CROSS_12 = 0.90
CROSS_21 = 0.35
DELAY_12 = 14
DELAY_21 = 3
OMEGA_MIN = 0.07
OMEGA_MAX = 0.35
N_FREQ = 9
HARDNESS_DEG = 30.0


def mixing_matrix(omega: float) -> np.ndarray:
    """2x2 synthetic FIR mixing response A(omega)."""
    z12 = np.exp(-1j * float(omega) * DELAY_12)
    z21 = np.exp(-1j * float(omega) * DELAY_21)
    return np.asarray(
        [[1.0 + 0j, CROSS_12 * z12],
         [CROSS_21 * z21, 1.0 + 0j]],
        np.complex128,
    )


def target_row(omega: float) -> np.ndarray:
    """Projective source-1 extractor; exactly cancels source 2."""
    return np.asarray(
        [1.0 + 0j, -CROSS_12 * np.exp(-1j * float(omega) * DELAY_12)],
        np.complex128,
    )


def target_curve(omegas) -> np.ndarray:
    return np.asarray([target_row(w) for w in omegas], np.complex128)


def algebra_audit(omegas, targets):
    """Verify invertibility and exact interference cancellation numerically."""
    det_mag = []
    desired_mag = []
    leak_mag = []
    for omega, row in zip(omegas, targets):
        A = mixing_matrix(float(omega))
        out = row @ A
        det_mag.append(abs(np.linalg.det(A)))
        desired_mag.append(abs(out[0]))
        leak_mag.append(abs(out[1]))
    return {
        "min_det_magnitude": float(np.min(det_mag)),
        "max_det_magnitude": float(np.max(det_mag)),
        "min_desired_gain": float(np.min(desired_mag)),
        "max_interferer_leak": float(np.max(leak_mag)),
    }


def serialize_complex(v):
    return [[float(z.real), float(z.imag)] for z in np.asarray(v).ravel()]


def run_seed(Arbor, Config, seed, omegas, targets, weights, steps, oracle_steps):
    base = Arbor(Config(seed=int(seed), bootstrap_mass=90))
    boot = base.bootstrap()
    if not boot.get("ok", False):
        return {"seed": int(seed), "bootstrap_ok": False, "bootstrap": boot}
    base.mature = True
    base.protect = base.protect.copy()

    H0 = b1.arbor_curve(base, omegas)
    start = b1.describe_curve(H0, targets, weights)
    start_stats = base.branch_stats()

    shared = b1.compile_shared(
        base,
        omegas,
        targets,
        weights,
        steps,
        seed=510_000 + int(seed),
        label="all_frequencies",
    )

    train_idx = np.arange(0, len(omegas), 2, dtype=int)
    heldout = b1.compile_shared(
        base,
        omegas,
        targets,
        weights,
        steps,
        seed=520_000 + int(seed),
        train_indices=train_idx,
        label="alternating_frequencies",
    )

    # Fixed wrong ordering, chosen before the run: reverse the frequency curve.
    perm = np.arange(len(targets) - 1, -1, -1, dtype=int)
    shuffled = b1.compile_shared(
        base,
        omegas,
        targets[perm],
        weights,
        steps,
        seed=530_000 + int(seed),
        eval_target=targets,
        label="reversed_frequency_curve",
    )
    shuffled["permutation"] = perm.tolist()

    oracle_err = []
    oracle_acc = []
    for j, (omega, target) in enumerate(zip(omegas, targets)):
        err, acc = b1.compile_one_frequency(
            base,
            float(omega),
            target,
            oracle_steps,
            seed=540_000 + 10_000 * int(seed) + j,
        )
        oracle_err.append(float(err))
        oracle_acc.append(int(acc))

    return {
        "seed": int(seed),
        "bootstrap_ok": True,
        "bootstrap": boot,
        "start_branch_stats": start_stats,
        "start": start,
        "shared": shared,
        "heldout": heldout,
        "shuffled": shuffled,
        "independent_body_oracle": {
            "per_frequency_error_deg": np.degrees(oracle_err).tolist(),
            "mean_error_deg": float(np.degrees(np.mean(oracle_err))),
            "accepted": oracle_acc,
        },
    }


def summarise(rows, constant_error_deg, matched_fir_error_deg):
    good = [r for r in rows if r.get("bootstrap_ok")]
    if not good:
        return {"usable_seeds": 0}

    start = np.asarray([r["start"]["mean_error_deg"] for r in good], float)
    final = np.asarray(
        [r["shared"]["final_correct"]["mean_error_deg"] for r in good], float
    )
    improvement_frac = (start - final) / np.maximum(start, EPS)

    held0 = np.asarray(
        [r["heldout"]["heldout_start_error_deg"] for r in good], float
    )
    held1 = np.asarray(
        [r["heldout"]["heldout_final_error_deg"] for r in good], float
    )
    held_improvement = held0 - held1

    shuf0 = np.asarray(
        [r["shuffled"]["start_correct"]["mean_error_deg"] for r in good], float
    )
    shuf1 = np.asarray(
        [r["shuffled"]["final_correct"]["mean_error_deg"] for r in good], float
    )
    shuffled_improvement = shuf0 - shuf1

    oracle = np.asarray(
        [r["independent_body_oracle"]["mean_error_deg"] for r in good], float
    )

    final_below_constant = int(np.sum(final < float(constant_error_deg)))
    rotating_pass = bool(
        float(constant_error_deg) >= HARDNESS_DEG
        and final_below_constant >= math.ceil(0.75 * len(good))
        and float(np.median(improvement_frac)) >= 0.20
    )

    heldout_improved = int(np.sum(held1 < held0))
    heldout_pass = bool(
        heldout_improved >= math.ceil(0.75 * len(good))
        and float(np.median(held_improvement)) > 0.0
        and float(np.median(held_improvement))
        > float(np.median(shuffled_improvement))
    )

    return {
        "usable_seeds": len(good),
        "constant_direction_error_deg": float(constant_error_deg),
        "matched_fir_error_deg": float(matched_fir_error_deg),
        "start_mean_deg": float(np.mean(start)),
        "shared_final_mean_deg": float(np.mean(final)),
        "shared_median_fractional_improvement": float(np.median(improvement_frac)),
        "shared_seeds_improved": int(np.sum(final < start)),
        "shared_seeds_below_constant": final_below_constant,
        "independent_body_oracle_mean_deg": float(np.mean(oracle)),
        "heldout_start_mean_deg": float(np.mean(held0)),
        "heldout_final_mean_deg": float(np.mean(held1)),
        "heldout_seeds_improved": heldout_improved,
        "heldout_median_improvement_deg": float(np.median(held_improvement)),
        "shuffled_correct_start_mean_deg": float(np.mean(shuf0)),
        "shuffled_correct_final_mean_deg": float(np.mean(shuf1)),
        "shuffled_median_improvement_deg": float(np.median(shuffled_improvement)),
        "rotating_representation_pass": rotating_pass,
        "heldout_coupling_pass": heldout_pass,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--fa-root", default="../FunctionalArbors")
    p.add_argument("--seeds", type=int, default=4)
    p.add_argument("--steps", type=int, default=120)
    p.add_argument("--oracle-steps", type=int, default=80)
    p.add_argument("--out", default="fa_bss_conv0_rotating.json")
    a = p.parse_args()

    if a.seeds != 4 or a.steps != 120 or a.oracle_steps != 80:
        raise ValueError(
            "CONV0 is pre-registered for --seeds 4 --steps 120 --oracle-steps 80"
        )

    omegas = np.linspace(OMEGA_MIN, OMEGA_MAX, N_FREQ)
    targets = target_curve(omegas)
    weights = np.ones(N_FREQ, float) / N_FREQ

    audit = algebra_audit(omegas, targets)
    if audit["min_det_magnitude"] < 0.68:
        raise RuntimeError("synthetic mixer unexpectedly close to singular")
    if audit["max_interferer_leak"] > 1e-10:
        raise RuntimeError("analytic demixing row failed cancellation audit")

    constant = b1.best_constant_direction(targets, weights)
    constant_error = b1.mean_error(
        np.tile(constant[None, :], (N_FREQ, 1)), targets, weights
    )
    constant_error_deg = float(np.degrees(constant_error))

    matched = targets.copy()
    matched_fir_error = b1.mean_error(matched, targets, weights)
    matched_fir_error_deg = float(np.degrees(matched_fir_error))

    print("CONV0 controlled rotating demixer")
    print(
        f"  FIR: x1=s1+{CROSS_12:.2f}*delay(s2,{DELAY_12}), "
        f"x2={CROSS_21:.2f}*delay(s1,{DELAY_21})+s2"
    )
    print(
        f"  omega: {OMEGA_MIN:.3f}..{OMEGA_MAX:.3f}, {N_FREQ} points; "
        f"target ratio magnitude={CROSS_12:.2f}"
    )
    print(
        f"  determinant magnitude {audit['min_det_magnitude']:.3f}.."
        f"{audit['max_det_magnitude']:.3f}; max cancellation leak "
        f"{audit['max_interferer_leak']:.3e}"
    )
    print(f"  best constant-direction error: {constant_error_deg:.2f} deg")
    print(f"  exact matched FIR error: {matched_fir_error_deg:.6f} deg")

    if constant_error_deg < HARDNESS_DEG:
        raise RuntimeError(
            f"hardness prerequisite failed: {constant_error_deg:.2f} < {HARDNESS_DEG:.2f} deg"
        )

    Arbor, Config = r0.load_fa(a.fa_root)
    rows = []
    for seed in range(a.seeds):
        row = run_seed(
            Arbor,
            Config,
            seed,
            omegas,
            targets,
            weights,
            a.steps,
            a.oracle_steps,
        )
        rows.append(row)
        if not row.get("bootstrap_ok"):
            print(f"  seed {seed}: bootstrap failed")
            continue
        s = row["start"]["mean_error_deg"]
        f = row["shared"]["final_correct"]["mean_error_deg"]
        h0 = row["heldout"]["heldout_start_error_deg"]
        h1 = row["heldout"]["heldout_final_error_deg"]
        q0 = row["shuffled"]["start_correct"]["mean_error_deg"]
        q1 = row["shuffled"]["final_correct"]["mean_error_deg"]
        oracle = row["independent_body_oracle"]["mean_error_deg"]
        ds = row["start_branch_stats"]
        df = row["shared"]["branch_stats"]
        d0 = ds.get("length_B", 0) - ds.get("length_A", 0)
        d1 = df.get("length_B", 0) - df.get("length_A", 0)
        print(
            f"  seed {seed}: shared {s:.2f}->{f:.2f} deg; "
            f"heldout {h0:.2f}->{h1:.2f}; reversed correct {q0:.2f}->{q1:.2f}; "
            f"oracle {oracle:.2f}; path-delta {d0}->{d1}"
        )

    summary = summarise(rows, constant_error_deg, matched_fir_error_deg)
    print("summary:")
    print(json.dumps(summary, indent=2))

    payload = {
        "experiment": "FA-BSS-CONV0",
        "contract": "notes/conv0_rotating_demixer_contract.md",
        "world": {
            "cross_12": CROSS_12,
            "cross_21": CROSS_21,
            "delay_12": DELAY_12,
            "delay_21": DELAY_21,
            "omega": omegas.tolist(),
            "targets": [serialize_complex(w) for w in targets],
            "target_ratio_H2_H1": [
                [float((w[1] / w[0]).real), float((w[1] / w[0]).imag)]
                for w in targets
            ],
            "audit": audit,
        },
        "baselines": {
            "best_constant_direction": serialize_complex(constant),
            "best_constant_error_deg": constant_error_deg,
            "matched_fir": {
                "description": f"y[t] = x1[t] - {CROSS_12:.2f} * x2[t-{DELAY_12}]",
                "projective_error_deg": matched_fir_error_deg,
            },
        },
        "execution": {
            "seeds": a.seeds,
            "shared_steps": a.steps,
            "oracle_steps": a.oracle_steps,
            "bootstrap_mass": 90,
        },
        "rows": rows,
        "summary": summary,
    }
    Path(a.out).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("wrote", a.out)


if __name__ == "__main__":
    main()
