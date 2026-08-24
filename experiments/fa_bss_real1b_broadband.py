"""FA-BSS-REAL1B -- one body, many frequencies.

This gate attacks the interpretation left alive by REAL0.

REAL0 showed that a FunctionalArbor morphology could be moved toward ONE complex
AuxIVA demixing coefficient. That can still be dismissed as an eccentric way to
store one complex weight.

REAL1B asks the harder representational question:

    Can ONE fixed morphology move toward a whole frequency-dependent AuxIVA
    demixing curve at once?

The experiment remains supervised. AuxIVA supplies target demixing directions.
We are testing structural expressivity/coupling, not blind source separation and
not biological learning.

Important frequency warning
---------------------------
The FunctionalArbor simulator is dimensionless. We therefore do NOT claim that
an audio frequency in Hz is the same physical frequency as the arbor solver's
omega. Selected audio bins are mapped through ONE global linear scale so that
the geometric-mean selected audio frequency maps to FreeConfig.carrier_omega.
This preserves ordering and relative frequency ratios while avoiding a fake Hz
calibration.

Controls
--------
1. Best constant complex demixing direction across the selected bins.
2. Independent-body oracle: each frequency gets its own separately remodeled
   morphology. This measures the price of forcing one anatomy to satisfy all bins.
3. Held-out frequencies: optimize alternating bins, score the unseen interleaved
   bins. Useful improvement would indicate coherent structural coupling rather
   than independent per-bin memorization.
4. Shuffled-curve control: optimize the same target vectors assigned to the wrong
   frequencies, then score against the correct curve.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

import fa_bss_real0 as r0

EPS = 1e-12


def _unit(v):
    v = np.asarray(v, np.complex128)
    return v / (np.linalg.norm(v) + EPS)


def projective_errors(H, W):
    H = np.asarray(H, np.complex128)
    W = np.asarray(W, np.complex128)
    return np.asarray([r0.proj_error(h, w) for h, w in zip(H, W)], float)


def mean_error(H, W, weights=None, indices=None):
    e = projective_errors(H, W)
    if indices is not None:
        indices = np.asarray(indices, int)
        e = e[indices]
        if weights is not None:
            weights = np.asarray(weights, float)[indices]
    if weights is None:
        return float(np.mean(e))
    weights = np.asarray(weights, float)
    weights = weights / (weights.sum() + EPS)
    return float(np.sum(weights * e))


def best_constant_direction(W, weights=None):
    """Principal projective direction for a frequency-independent 2-vector."""
    W = np.asarray([_unit(w) for w in W], np.complex128)
    if weights is None:
        weights = np.ones(len(W), float)
    weights = np.asarray(weights, float)
    weights = weights / (weights.sum() + EPS)
    S = np.zeros((2, 2), np.complex128)
    for a, w in zip(weights, W):
        S += a * np.outer(w, w.conj())
    val, vec = np.linalg.eigh(S)
    return _unit(vec[:, int(np.argmax(val))])


def select_spread_bins(aux, fs, nfft, count=9, fmin=400.0, fmax=2400.0):
    """Pick energetic bins spread across log-frequency rather than one cluster."""
    W = aux["W"]
    Y = aux["Y"]
    target = int(aux["target"])
    freqs = np.fft.rfftfreq(int(nfft), 1.0 / float(fs))
    energy = np.mean(np.abs(Y[target]) ** 2, axis=1)
    valid = (freqs >= float(fmin)) & (freqs <= float(fmax))
    valid &= np.abs(W[:, target, 0]) > 1e-10
    valid &= np.abs(W[:, target, 1]) > 1e-10
    candidates = np.flatnonzero(valid)
    if len(candidates) < count:
        raise RuntimeError(f"only {len(candidates)} usable bins in requested band")

    lo, hi = math.log(float(fmin)), math.log(float(fmax))
    edges = np.linspace(lo, hi, int(count) + 1)
    chosen = []
    used = set()
    for j in range(int(count)):
        a, b = math.exp(edges[j]), math.exp(edges[j + 1])
        if j == int(count) - 1:
            m = candidates[(freqs[candidates] >= a) & (freqs[candidates] <= b)]
        else:
            m = candidates[(freqs[candidates] >= a) & (freqs[candidates] < b)]
        m = np.asarray([k for k in m if int(k) not in used], int)
        if len(m):
            k = int(m[int(np.argmax(energy[m]))])
            chosen.append(k)
            used.add(k)

    # Fill any empty log bands with the strongest still-unused valid bins.
    if len(chosen) < count:
        for k in candidates[np.argsort(energy[candidates])[::-1]]:
            k = int(k)
            if k not in used:
                chosen.append(k)
                used.add(k)
                if len(chosen) == count:
                    break

    chosen = np.asarray(sorted(chosen[:count], key=lambda k: freqs[k]), int)
    targets = np.asarray([W[k, target, :] for k in chosen], np.complex128)
    energies = np.asarray([energy[k] for k in chosen], float)

    # Uniform scoring is deliberate: one loud bin must not define the whole gate.
    weights = np.ones(len(chosen), float) / len(chosen)
    return {
        "bins": chosen,
        "hz": freqs[chosen],
        "targets": targets,
        "energies": energies,
        "weights": weights,
    }


def omega_map(hz, carrier_omega):
    """One scale through zero; geometric-mean selected Hz maps to carrier_omega."""
    hz = np.asarray(hz, float)
    ref = float(np.exp(np.mean(np.log(hz))))
    scale = float(carrier_omega) / ref
    return hz * scale, ref, scale


def arbor_curve(model, omegas):
    return np.asarray(
        [r0.arbor_transfer(model, float(w)) for w in omegas],
        np.complex128,
    )


def describe_curve(H, W, weights):
    e = projective_errors(H, W)
    m = mean_error(H, W, weights)
    return {
        "mean_error_rad": m,
        "mean_error_deg": float(np.degrees(m)),
        "per_bin_error_rad": e.tolist(),
        "per_bin_error_deg": np.degrees(e).tolist(),
        "H": [[[float(z.real), float(z.imag)] for z in h] for h in H],
        "ratio_H1_H0": [
            [float((h[1] / h[0]).real), float((h[1] / h[0]).imag)] for h in H
        ],
    }


def compile_shared(
    base,
    omegas,
    W_target,
    weights,
    steps,
    seed,
    train_indices=None,
    eval_target=None,
    label="shared",
):
    m = r0._copy_fa(base)
    m.rng = np.random.default_rng(int(seed))
    W_target = np.asarray(W_target, np.complex128)
    eval_target = W_target if eval_target is None else np.asarray(eval_target, np.complex128)
    if train_indices is None:
        train_indices = np.arange(len(omegas), dtype=int)
    train_indices = np.asarray(train_indices, int)
    train_set = set(train_indices.tolist())
    eval_indices = np.asarray(
        [i for i in range(len(omegas)) if i not in train_set], int
    )

    H = arbor_curve(m, omegas)
    H_start = H.copy()
    train_err = mean_error(H, W_target, weights, train_indices)
    start_correct = describe_curve(H, eval_target, weights)
    held_start = (
        mean_error(H_start, eval_target, weights, eval_indices)
        if len(eval_indices)
        else float("nan")
    )
    accepted = 0
    hist = []

    for j in range(int(steps)):
        snap = m.snapshot()
        prop = m.propose_detour(j & 1)
        if prop is None:
            continue
        Hn = arbor_curve(m, omegas)
        en = mean_error(Hn, W_target, weights, train_indices)
        keep = en < train_err - 1e-10
        if keep:
            H = Hn
            train_err = en
            accepted += 1
            correct_all = mean_error(H, eval_target, weights)
            held = (
                mean_error(H, eval_target, weights, eval_indices)
                if len(eval_indices)
                else float("nan")
            )
            hist.append(
                {
                    "step": int(j),
                    "accepted": int(accepted),
                    "train_error_deg": float(np.degrees(train_err)),
                    "correct_all_error_deg": float(np.degrees(correct_all)),
                    "heldout_error_deg": (
                        float(np.degrees(held)) if np.isfinite(held) else None
                    ),
                    "proposal": prop,
                }
            )
        else:
            m.restore(snap)

    final_correct = describe_curve(H, eval_target, weights)
    final_train = mean_error(H, W_target, weights, train_indices)
    held_final = (
        mean_error(H, eval_target, weights, eval_indices)
        if len(eval_indices)
        else float("nan")
    )

    return {
        "label": label,
        "accepted": int(accepted),
        "train_indices": train_indices.tolist(),
        "eval_indices": eval_indices.tolist(),
        "start_correct": start_correct,
        "final_correct": final_correct,
        "final_train_error_deg": float(np.degrees(final_train)),
        "heldout_start_error_deg": (
            float(np.degrees(held_start)) if np.isfinite(held_start) else None
        ),
        "heldout_final_error_deg": (
            float(np.degrees(held_final)) if np.isfinite(held_final) else None
        ),
        "history": hist,
        "mass": int(m.mass()),
        "branch_stats": m.branch_stats(),
    }


def compile_one_frequency(base, omega, target, steps, seed):
    m = r0._copy_fa(base)
    m.rng = np.random.default_rng(int(seed))
    H = r0.arbor_transfer(m, float(omega))
    err = r0.proj_error(H, target)
    accepted = 0
    for j in range(int(steps)):
        snap = m.snapshot()
        prop = m.propose_detour(j & 1)
        if prop is None:
            continue
        Hn = r0.arbor_transfer(m, float(omega))
        en = r0.proj_error(Hn, target)
        if en < err - 1e-10:
            H, err = Hn, en
            accepted += 1
        else:
            m.restore(snap)
    return float(err), int(accepted)


def run_seed(Arbor, Config, seed, omegas, targets, weights, steps, oracle_steps):
    base = Arbor(Config(seed=int(seed), bootstrap_mass=90))
    boot = base.bootstrap()
    if not boot.get("ok", False):
        return {"seed": int(seed), "bootstrap_ok": False, "bootstrap": boot}
    base.mature = True
    base.protect = base.protect.copy()

    H0 = arbor_curve(base, omegas)
    start = describe_curve(H0, targets, weights)

    allfit = compile_shared(
        base,
        omegas,
        targets,
        weights,
        steps,
        seed=100_000 + seed,
        label="all_bins",
    )

    train_idx = np.arange(0, len(omegas), 2, dtype=int)
    heldout = compile_shared(
        base,
        omegas,
        targets,
        weights,
        steps,
        seed=200_000 + seed,
        train_indices=train_idx,
        label="alternating_train",
    )

    rng = np.random.default_rng(300_000 + seed)
    perm = rng.permutation(len(targets))
    if np.all(perm == np.arange(len(targets))):
        perm = np.roll(perm, 1)
    shuffled = compile_shared(
        base,
        omegas,
        targets[perm],
        weights,
        steps,
        seed=310_000 + seed,
        eval_target=targets,
        label="shuffled_curve",
    )
    shuffled["permutation"] = perm.tolist()

    oracle_err = []
    oracle_acc = []
    for j, (omega, target) in enumerate(zip(omegas, targets)):
        e, acc = compile_one_frequency(
            base,
            omega,
            target,
            oracle_steps,
            seed=400_000 + 10_000 * seed + j,
        )
        oracle_err.append(e)
        oracle_acc.append(acc)

    return {
        "seed": int(seed),
        "bootstrap_ok": True,
        "bootstrap": boot,
        "start": start,
        "all_bins": allfit,
        "heldout": heldout,
        "shuffled": shuffled,
        "independent_body_oracle": {
            "per_bin_error_deg": np.degrees(oracle_err).tolist(),
            "mean_error_deg": float(np.degrees(np.mean(oracle_err))),
            "accepted": oracle_acc,
        },
    }


def summarise(rows, constant_deg):
    good = [r for r in rows if r.get("bootstrap_ok")]
    if not good:
        return {"usable_seeds": 0}

    start = np.asarray([r["start"]["mean_error_deg"] for r in good], float)
    final = np.asarray(
        [r["all_bins"]["final_correct"]["mean_error_deg"] for r in good], float
    )
    held0 = np.asarray(
        [r["heldout"]["heldout_start_error_deg"] for r in good], float
    )
    held1 = np.asarray(
        [r["heldout"]["heldout_final_error_deg"] for r in good], float
    )
    shuf0 = np.asarray(
        [r["shuffled"]["start_correct"]["mean_error_deg"] for r in good], float
    )
    shuf1 = np.asarray(
        [r["shuffled"]["final_correct"]["mean_error_deg"] for r in good], float
    )
    oracle = np.asarray(
        [r["independent_body_oracle"]["mean_error_deg"] for r in good], float
    )

    improvement_frac = (start - final) / np.maximum(start, EPS)
    held_improve = held0 - held1
    shuf_improve = shuf0 - shuf1

    # Predeclared conservative interpretation flags, not a biological claim.
    representation_pass = bool(
        np.median(improvement_frac) >= 0.15
        and np.sum(final < start) >= math.ceil(0.75 * len(good))
        and np.median(final) < float(constant_deg)
    )
    coupling_hint = bool(
        np.sum(held1 < held0) >= math.ceil(0.75 * len(good))
        and np.median(held_improve) > np.median(shuf_improve)
    )

    return {
        "usable_seeds": len(good),
        "start_mean_deg": float(np.mean(start)),
        "final_shared_mean_deg": float(np.mean(final)),
        "median_fractional_improvement": float(np.median(improvement_frac)),
        "seeds_improved": int(np.sum(final < start)),
        "constant_direction_error_deg": float(constant_deg),
        "heldout_start_mean_deg": float(np.mean(held0)),
        "heldout_final_mean_deg": float(np.mean(held1)),
        "heldout_seeds_improved": int(np.sum(held1 < held0)),
        "shuffled_correct_start_mean_deg": float(np.mean(shuf0)),
        "shuffled_correct_final_mean_deg": float(np.mean(shuf1)),
        "independent_body_oracle_mean_deg": float(np.mean(oracle)),
        "representation_pass": representation_pass,
        "coupling_hint": coupling_hint,
        "interpretation": (
            "representation_pass tests whether one morphology captures useful frequency dependence; "
            "coupling_hint additionally asks whether fitting interleaved frequencies helps unseen bins more than a shuffled curve."
        ),
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--mic", default="Wav/two_ears_in0.wav")
    p.add_argument("--pickup", default="Wav/two_ears_in1.wav")
    p.add_argument("--fa-root", default="../FunctionalArbors")
    p.add_argument("--nfft", type=int, default=2048)
    p.add_argument("--iva-iters", type=int, default=30)
    p.add_argument("--bins", type=int, default=9)
    p.add_argument("--fmin", type=float, default=400.0)
    p.add_argument("--fmax", type=float, default=2400.0)
    p.add_argument("--seeds", type=int, default=4)
    p.add_argument("--steps", type=int, default=70)
    p.add_argument("--oracle-steps", type=int, default=45)
    p.add_argument("--out", default="fa_bss_real1b_broadband.json")
    a = p.parse_args()

    fs, x = r0.load_pair(Path(a.mic), Path(a.pickup))
    aux = r0.auxiva_probe(x, fs, a.nfft, a.iva_iters)
    sel = select_spread_bins(aux, fs, a.nfft, a.bins, a.fmin, a.fmax)

    Arbor, Config = r0.load_fa(a.fa_root)
    probe_cfg = Config(seed=0, bootstrap_mass=90)
    omegas, hz_ref, omega_scale = omega_map(sel["hz"], probe_cfg.carrier_omega)

    targets = sel["targets"]
    weights = sel["weights"]
    const = best_constant_direction(targets, weights)
    const_curve = np.tile(const[None, :], (len(targets), 1))
    constant_deg = float(np.degrees(mean_error(const_curve, targets, weights)))

    print("REAL1B broadband structural compile")
    print(f"  fs={fs} nfft={a.nfft} target_component={aux['target']}")
    print(
        f"  selected {len(targets)} bins, "
        f"{sel['hz'][0]:.1f}..{sel['hz'][-1]:.1f} Hz"
    )
    print(
        f"  one global frequency scale: geometric mean {hz_ref:.2f} Hz "
        f"-> omega {probe_cfg.carrier_omega:.4f}"
    )
    print(f"  omega range: {omegas[0]:.4f} .. {omegas[-1]:.4f}")
    print(f"  best constant-direction error: {constant_deg:.2f} deg")

    rows = []
    for seed in range(int(a.seeds)):
        row = run_seed(
            Arbor, Config, seed, omegas, targets, weights, a.steps, a.oracle_steps
        )
        rows.append(row)
        if not row.get("bootstrap_ok"):
            print(f"  seed {seed}: bootstrap failed")
            continue
        s = row["start"]["mean_error_deg"]
        f = row["all_bins"]["final_correct"]["mean_error_deg"]
        h0 = row["heldout"]["heldout_start_error_deg"]
        h1 = row["heldout"]["heldout_final_error_deg"]
        sh0 = row["shuffled"]["start_correct"]["mean_error_deg"]
        sh1 = row["shuffled"]["final_correct"]["mean_error_deg"]
        o = row["independent_body_oracle"]["mean_error_deg"]
        print(
            f"  seed {seed}: shared {s:.2f}->{f:.2f} deg | "
            f"heldout {h0:.2f}->{h1:.2f} | "
            f"shuffled correct {sh0:.2f}->{sh1:.2f} | "
            f"per-bin oracle {o:.2f}"
        )

    summary = summarise(rows, constant_deg)
    print("summary:")
    print(json.dumps(summary, indent=2))

    payload = {
        "experiment": "FA-BSS-REAL1B",
        "claim_scope": (
            "supervised broadband structural compile; not blind BSS; "
            "no physical Hz-to-omega calibration claimed"
        ),
        "inputs": {
            "mic": a.mic,
            "pickup": a.pickup,
            "fs": int(fs),
            "nfft": int(a.nfft),
            "iva_iters": int(a.iva_iters),
            "fmin": float(a.fmin),
            "fmax": float(a.fmax),
            "selected_bins": int(a.bins),
            "seeds": int(a.seeds),
            "steps": int(a.steps),
            "oracle_steps": int(a.oracle_steps),
        },
        "frequency_map": {
            "kind": "one global linear scale through zero",
            "audio_geometric_mean_hz": hz_ref,
            "carrier_omega": float(probe_cfg.carrier_omega),
            "omega_per_hz": omega_scale,
            "hz": sel["hz"].tolist(),
            "omega": omegas.tolist(),
        },
        "targets": {
            "auxiva_component": int(aux["target"]),
            "stft_bins": sel["bins"].tolist(),
            "energy": sel["energies"].tolist(),
            "W": [
                [[float(z.real), float(z.imag)] for z in w] for w in targets
            ],
            "ratio_w1_w0": [
                [float((w[1] / w[0]).real), float((w[1] / w[0]).imag)]
                for w in targets
            ],
            "best_constant_direction": [
                [float(z.real), float(z.imag)] for z in const
            ],
            "best_constant_error_deg": constant_deg,
        },
        "rows": rows,
        "summary": summary,
    }
    Path(a.out).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("wrote", a.out)


if __name__ == "__main__":
    main()
