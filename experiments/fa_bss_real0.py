"""FA-BSS-REAL0 -- real two-sensor audio probe + anatomical demixer compile.

Inputs are the two WAV files saved by TWO EARS:
    Wav/two_ears_in0.wav   microphone / XLR
    Wav/two_ears_in1.wav   pickup / instrument jack

This is deliberately NOT yet a claim that FunctionalArbors performs blind audio
source separation.  The script asks three narrower questions:

1. Are the two recorded channels actually a nontrivial shared-mixture problem?
   (cross-channel correlation/coherence + digital FastICA/AuxIVA diagnostics)
2. What complex two-sensor demixing vector does AuxIVA learn at informative
   frequency bins in this real recording?
3. Can legal v0.5 FunctionalArbor morphologies physically approximate ONE such
   real-data demixing vector at the arbor's internal carrier frequency?

The last step is a teacher/compile test: AuxIVA supplies the target demixing row.
It is the real-data analogue of supervised FA-BSS0, not blind learning.  A blind
one-unit cumulant arm is also reported as an exploratory diagnostic only.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy.io import wavfile
from scipy import signal
import scipy.sparse as sp
import scipy.sparse.linalg as spla

EPS = 1e-12


# ---------------------------------------------------------------- audio I/O / basic diagnostics

def _wav_float(path: Path):
    fs, x = wavfile.read(path)
    if x.ndim != 1:
        raise ValueError(f"{path} must be mono; got shape {x.shape}")
    if np.issubdtype(x.dtype, np.integer):
        info = np.iinfo(x.dtype)
        scale = max(abs(info.min), abs(info.max))
        x = x.astype(np.float64) / float(scale)
    else:
        x = x.astype(np.float64)
    return int(fs), x


def load_pair(p0: Path, p1: Path):
    fs0, x0 = _wav_float(p0)
    fs1, x1 = _wav_float(p1)
    if fs0 != fs1:
        raise ValueError(f"sample-rate mismatch: {fs0} vs {fs1}")
    n = min(len(x0), len(x1))
    if n < fs0:
        raise ValueError("need at least one second of simultaneous audio")
    x = np.vstack([x0[:n], x1[:n]])
    x -= x.mean(axis=1, keepdims=True)
    return fs0, x


def rms(x):
    return float(np.sqrt(np.mean(np.asarray(x, float) ** 2)))


def best_lag_corr(a, b, fs, ms=40.0):
    a = np.asarray(a, float) - np.mean(a)
    b = np.asarray(b, float) - np.mean(b)
    c = signal.correlate(a, b, mode="full", method="fft")
    lags = signal.correlation_lags(len(a), len(b), mode="full")
    m = int(round(ms * 1e-3 * fs))
    keep = np.abs(lags) <= m
    c = c[keep] / (np.linalg.norm(a) * np.linalg.norm(b) + EPS)
    l = lags[keep]
    i = int(np.argmax(np.abs(c)))
    return {"corr": float(c[i]), "abs_corr": float(abs(c[i])),
            "lag_samples": int(l[i]), "lag_ms": float(1000 * l[i] / fs)}


def spectral_probe(x, fs):
    nper = min(8192, max(1024, 2 ** int(np.floor(np.log2(fs / 5)))))
    f, p0 = signal.welch(x[0], fs=fs, nperseg=nper)
    _, p1 = signal.welch(x[1], fs=fs, nperseg=nper)
    fc, coh = signal.coherence(x[0], x[1], fs=fs, nperseg=nper)
    band = (f >= 40) & (f <= min(10000, fs / 2 - 1))
    idx = np.flatnonzero(band)

    def top_rows(score, count=10):
        if not len(idx):
            return []
        ii = idx[np.argsort(score[idx])[-count:][::-1]]
        return [{"hz": float(f[j]), "value": float(score[j])} for j in ii]

    ratio10 = 10 * np.log10((p1 + 1e-20) / (p0 + 1e-20))
    # coherence grid is produced with the same nperseg, hence same f in scipy here.
    return {
        "welch_nperseg": int(nper),
        "top_pickup_over_mic_db": top_rows(ratio10),
        "top_mic_over_pickup_db": top_rows(-ratio10),
        "top_coherence": top_rows(coh),
        "median_coherence_40_10k": float(np.median(coh[idx])) if len(idx) else float("nan"),
        "p95_coherence_40_10k": float(np.quantile(coh[idx], .95)) if len(idx) else float("nan"),
    }


# ---------------------------------------------------------------- FastICA reference

def fastica_probe(x, seed=0):
    try:
        from sklearn.decomposition import FastICA
    except Exception as exc:
        return {"available": False, "error": repr(exc)}
    z = x.T
    est = FastICA(n_components=2, whiten="unit-variance", random_state=seed,
                  max_iter=2000, tol=1e-6).fit(z)
    y = est.transform(z).T
    A = np.asarray(est.mixing_, float)  # channels x components
    sig = np.abs(A)
    sig /= np.maximum(sig.sum(axis=0, keepdims=True), EPS)
    sig = sig.T
    cc = float(np.corrcoef(y[0], y[1])[0, 1])
    return {
        "available": True,
        "output_corr": cc,
        "channel_signature": sig.tolist(),
        "component_rms": [rms(y[0]), rms(y[1])],
    }


# ---------------------------------------------------------------- compact AuxIVA reference

def stft_pair(x, nfft=2048):
    hop = nfft // 2
    win = np.hanning(nfft + 1)[:nfft]
    M, L = x.shape
    T = max(1, 1 + (L - nfft) // hop)
    X = np.empty((M, nfft // 2 + 1, T), np.complex128)
    for t in range(T):
        seg = x[:, t * hop:t * hop + nfft] * win
        X[:, :, t] = np.fft.rfft(seg, axis=-1)
    return X


def auxiva_ip(X, n_iter=30):
    X = np.asarray(X)
    M, K, T = X.shape
    W = np.tile(np.eye(M, dtype=np.complex128), (K, 1, 1))
    Xk = np.transpose(X, (1, 0, 2))  # K,M,T
    eyes = np.tile(np.eye(M, dtype=np.complex128), (K, 1, 1))
    for _ in range(int(n_iter)):
        Y = np.einsum("kmn,knt->kmt", W, Xk)
        p = np.sum(np.abs(Y) ** 2, axis=0)
        r = np.sqrt(np.maximum(p, EPS))
        wgt = 1.0 / r
        for n in range(M):
            Vn = np.einsum("kmt,knt->kmn", Xk * wgt[n][None, None, :], Xk.conj()) / T
            WV = np.einsum("kmn,knp->kmp", W, Vn)
            en = eyes[:, :, n][:, :, None]
            try:
                wn = np.linalg.solve(WV, en)[:, :, 0]
            except np.linalg.LinAlgError:
                wn = np.linalg.solve(WV + 1e-8 * eyes, en)[:, :, 0]
            nrm = np.einsum("km,kmn,kn->k", wn.conj(), Vn, wn).real
            wn = wn / np.sqrt(np.maximum(nrm, EPS))[:, None]
            W[:, n, :] = wn.conj()
    # projection-back/minimal-distortion scaling
    Winv = np.linalg.pinv(W)
    for k in range(K):
        W[k] = np.diag(np.diag(Winv[k])) @ W[k]
    Y = np.einsum("kmn,knt->kmt", W, Xk)
    return np.transpose(Y, (1, 0, 2)), W


def channel_signature(W):
    A = np.linalg.pinv(W)  # K,M,M
    mag = np.abs(A).mean(axis=0)
    sig = mag / np.maximum(mag.sum(axis=0, keepdims=True), EPS)
    return sig.T


def complex_corr(a, b):
    a = np.asarray(a).ravel().astype(np.complex128)
    b = np.asarray(b).ravel().astype(np.complex128)
    a -= a.mean(); b -= b.mean()
    return float(abs(np.vdot(a, b)) / (np.linalg.norm(a) * np.linalg.norm(b) + EPS))


def complex_cumulant_score(y):
    y = np.asarray(y, np.complex128).ravel()
    y = y - y.mean()
    m2 = float(np.mean(np.abs(y) ** 2))
    if m2 < 1e-20:
        return 0.0
    p2 = np.mean(y ** 2)
    m4 = float(np.mean(np.abs(y) ** 4))
    c4 = m4 - 2 * m2 * m2 - abs(p2) ** 2
    return float(abs(c4) / (m2 * m2 + EPS))


def auxiva_probe(x, fs, nfft=2048, iters=30):
    X = stft_pair(x, nfft)
    Y, W = auxiva_ip(X, iters)
    sig = channel_signature(W)
    en = np.sqrt(np.mean(np.abs(Y) ** 2, axis=(1, 2)))
    # pick the component with strongest pickup association as the likely EM-world candidate
    target = int(np.argmax(sig[:, 1]))
    freqs = np.fft.rfftfreq(nfft, 1.0 / fs)

    # Choose informative target bins: target has energy, both W coefficients are usable,
    # and restrict to a human/electrical band rather than DC/Nyquist.
    ebin = np.mean(np.abs(Y[target]) ** 2, axis=1)
    valid = (freqs >= 40) & (freqs <= min(10000, fs / 2 - 1))
    valid &= np.abs(W[:, target, 0]) > 1e-10
    cand = np.flatnonzero(valid)
    cand = cand[np.argsort(ebin[cand])[-12:][::-1]] if len(cand) else np.array([], int)
    bins = []
    for k in cand:
        w = W[k, target, :]
        bins.append({
            "bin": int(k), "hz": float(freqs[k]), "energy": float(ebin[k]),
            "w": [[float(z.real), float(z.imag)] for z in w],
            "ratio_w1_w0": [float((w[1] / w[0]).real), float((w[1] / w[0]).imag)],
            "target_kurtosis": complex_cumulant_score(Y[target, k]),
        })
    return {
        "X": X, "Y": Y, "W": W, "sig": sig, "target": target, "bins": bins,
        "summary": {
            "nfft": int(nfft), "iters": int(iters),
            "component_energy": en.tolist(),
            "channel_signature": sig.tolist(),
            "pickup_associated_component": target,
            "signature_separation_l1": float(np.sum(np.abs(sig[0] - sig[1]))),
            "output_tf_corr": complex_corr(Y[0], Y[1]),
            "top_target_bins": bins,
        },
    }


# ---------------------------------------------------------------- FunctionalArbor carrier transfer

def load_fa(root):
    root = str(Path(root).resolve())
    if root not in sys.path:
        sys.path.insert(0, root)
    from v05_free_arbor.free_arbor import FreeBinaryArbor, FreeConfig  # type: ignore
    return FreeBinaryArbor, FreeConfig


def _shift_sparse_laplacian(model):
    kr, kl, kd, ku = model.bond_fields(True)
    n = model.cfg.size
    rows, cols, data = [], [], []
    directions = ((0, 1, kr), (0, -1, kl), (1, 0, kd), (-1, 0, ku))
    for y in range(n):
        for x in range(n):
            i = y * n + x
            diag = 0.0
            for dy, dx, field in directions:
                k = float(field[y, x]); diag -= k
                yy, xx = y + dy, x + dx
                if 0 <= yy < n and 0 <= xx < n:
                    rows.append(i); cols.append(yy * n + xx); data.append(k)
            rows.append(i); cols.append(i); data.append(diag)
    N = n * n
    return sp.csr_matrix((data, (rows, cols)), shape=(N, N))


def arbor_transfer(model, omega=None):
    c = model.cfg
    omega = float(c.carrier_omega if omega is None else omega)
    z = np.exp(1j * omega)
    L = _shift_sparse_laplacian(model).astype(np.complex128)
    N = L.shape[0]
    alpha = (z - 1.0) * (1.0 - (1.0 - c.dt * c.damping) / z)
    alpha += (c.dt ** 2) * c.restoring
    M = alpha * sp.eye(N, format="csc") - (c.dt ** 2 * c.stiffness) * L.tocsc()
    rhs = np.zeros((N, 2), np.complex128)
    for q in (0, 1):
        p = model.source_terminal(q)
        if p is None:
            raise RuntimeError("arbor lost terminal")
        rhs[p[0] * c.size + p[1], q] = c.dt ** 2
    P = spla.splu(M).solve(rhs)
    si = model.soma[0] * c.size + model.soma[1]
    return np.asarray(P[si, :], np.complex128)


def proj_error(h, w):
    h = np.asarray(h, np.complex128); w = np.asarray(w, np.complex128)
    h /= np.linalg.norm(h) + EPS; w /= np.linalg.norm(w) + EPS
    ov = float(np.clip(abs(np.vdot(w, h)), 0.0, 1.0))
    return float(math.acos(ov))


def _copy_fa(base):
    m = base.copy(); m.mature = True
    # v0.5 copy() omits post-bootstrap endpoint protection.
    m.protect = base.protect.copy()
    return m


def compile_one_bin(base, Xbin, Ytarget, w_target, steps, seed, mode="teacher"):
    m = _copy_fa(base)
    rng = np.random.default_rng(seed + (900_001 if mode == "teacher" else 910_001))
    H = arbor_transfer(m)
    err = proj_error(H, w_target)
    blind = complex_cumulant_score(H @ Xbin)
    best_match = complex_corr(H @ Xbin, Ytarget)
    accepted = 0
    history = []
    for j in range(int(steps)):
        # Proposal weighting has a nonzero baseline even with E=0.  This keeps REAL0
        # about morphology-space search rather than pretending we already solved local
        # real-audio credit assignment.
        snap = m.snapshot()
        prop = m.propose_detour(int(rng.integers(2)))
        if prop is None:
            continue
        Hn = arbor_transfer(m)
        errn = proj_error(Hn, w_target)
        blindn = complex_cumulant_score(Hn @ Xbin)
        keep = (errn < err - 1e-9) if mode == "teacher" else (blindn > blind + 1e-9)
        if keep:
            H, err, blind = Hn, errn, blindn
            accepted += 1
            best_match = complex_corr(H @ Xbin, Ytarget)
        else:
            m.restore(snap)
        if keep or j in (0, steps - 1):
            history.append({"step": j, "keep": bool(keep), "error": float(err),
                            "blind_score": float(blind), "auxiva_bin_corr": float(best_match)})
    return {
        "mode": mode, "accepted": accepted,
        "final_error_rad": float(err),
        "final_blind_score": float(blind),
        "auxiva_bin_corr": float(best_match),
        "H": [[float(z.real), float(z.imag)] for z in H],
        "ratio_H1_H0": [float((H[1] / H[0]).real), float((H[1] / H[0]).imag)],
        "history": history,
    }


def arbor_real_compile(aux, fa_root, seeds=4, steps=80):
    if not aux["bins"]:
        return {"available": False, "reason": "AuxIVA produced no candidate bins"}
    # strongest target-component bin
    b = aux["bins"][0]
    k = int(b["bin"]); n = int(aux["target"])
    w = np.asarray(aux["W"][k, n, :], np.complex128)
    Xbin = aux["X"][:, k, :]
    Ytarget = aux["Y"][n, k, :]

    Arbor, Config = load_fa(fa_root)
    rows = []
    for seed in range(int(seeds)):
        base = Arbor(Config(seed=seed, bootstrap_mass=90))
        boot = base.bootstrap()
        if not boot.get("ok", False):
            rows.append({"seed": seed, "bootstrap_ok": False})
            continue
        base.mature = True
        H0 = arbor_transfer(base)
        start = {
            "error_rad": proj_error(H0, w),
            "blind_score": complex_cumulant_score(H0 @ Xbin),
            "auxiva_bin_corr": complex_corr(H0 @ Xbin, Ytarget),
            "ratio_H1_H0": [float((H0[1]/H0[0]).real), float((H0[1]/H0[0]).imag)],
        }
        teacher = compile_one_bin(base, Xbin, Ytarget, w, steps, seed, "teacher")
        blind = compile_one_bin(base, Xbin, Ytarget, w, steps, seed, "blind")
        rows.append({"seed": seed, "bootstrap_ok": True, "start": start,
                     "teacher": teacher, "blind": blind})
    return {
        "available": True,
        "note": "single audio STFT bin compiled into one internal arbor carrier; no Hz mapping is claimed",
        "audio_bin": b,
        "rows": rows,
    }


# ---------------------------------------------------------------- main

def strip_arrays(aux):
    return aux["summary"]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--mic", default="Wav/two_ears_in0.wav")
    p.add_argument("--pickup", default="Wav/two_ears_in1.wav")
    p.add_argument("--fa-root", default="../FunctionalArbors")
    p.add_argument("--nfft", type=int, default=2048)
    p.add_argument("--iva-iters", type=int, default=30)
    p.add_argument("--fa-seeds", type=int, default=4)
    p.add_argument("--fa-steps", type=int, default=80)
    p.add_argument("--out", default="fa_bss_real0.json")
    a = p.parse_args()

    fs, x = load_pair(Path(a.mic), Path(a.pickup))
    print(f"REAL0 WAV: fs={fs} Hz samples={x.shape[1]} duration={x.shape[1]/fs:.3f}s")
    print(f"  mic    rms={rms(x[0]):.6f} peak={np.max(np.abs(x[0])):.6f}")
    print(f"  pickup rms={rms(x[1]):.6f} peak={np.max(np.abs(x[1])):.6f}")
    lag = best_lag_corr(x[0], x[1], fs)
    print("  best cross-channel lag/corr:", lag)

    spec = spectral_probe(x, fs)
    print(f"  coherence median={spec['median_coherence_40_10k']:.3f} p95={spec['p95_coherence_40_10k']:.3f}")
    print("  strongest pickup/mic spectral ratios:")
    for r in spec["top_pickup_over_mic_db"][:6]:
        print(f"    {r['hz']:8.1f} Hz  {r['value']:+7.2f} dB")

    fi = fastica_probe(x)
    print("FastICA:", json.dumps(fi, indent=2))

    aux = auxiva_probe(x, fs, a.nfft, a.iva_iters)
    print("AuxIVA summary:")
    print(json.dumps(aux["summary"], indent=2))

    comp = arbor_real_compile(aux, a.fa_root, a.fa_seeds, a.fa_steps)
    if comp.get("available"):
        print("FunctionalArbor one-bin compile:")
        print(f"  audio bin {comp['audio_bin']['hz']:.1f} Hz target ratio={comp['audio_bin']['ratio_w1_w0']}")
        for row in comp["rows"]:
            if not row.get("bootstrap_ok"):
                print(f"  seed {row['seed']}: bootstrap failed")
                continue
            s, t, b = row["start"], row["teacher"], row["blind"]
            print(f"  seed {row['seed']}: start err={s['error_rad']:.3f} corr={s['auxiva_bin_corr']:.3f} | "
                  f"teacher err={t['final_error_rad']:.3f} corr={t['auxiva_bin_corr']:.3f} acc={t['accepted']} | "
                  f"blind J={b['final_blind_score']:.3f} corr={b['auxiva_bin_corr']:.3f} acc={b['accepted']}")

    payload = {
        "experiment": "FA-BSS-REAL0",
        "inputs": {"mic": a.mic, "pickup": a.pickup, "fs": fs,
                   "samples": int(x.shape[1]), "duration_s": float(x.shape[1]/fs),
                   "rms": [rms(x[0]), rms(x[1])],
                   "peak": [float(np.max(np.abs(x[0]))), float(np.max(np.abs(x[1])))],
                   "best_lag_corr": lag,
                   "note": "TWO EARS save_wavs normalizes inputs separately; channel scaling is therefore not physical gain calibration."},
        "spectral": spec,
        "fastica": fi,
        "auxiva": strip_arrays(aux),
        "functional_arbor_compile": comp,
    }
    Path(a.out).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("wrote", a.out)


if __name__ == "__main__":
    main()
