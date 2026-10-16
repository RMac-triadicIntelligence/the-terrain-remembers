"""
readers.py — SCALAR and TERRAIN readers plus the five preregistered variants.

Every reader sees only (n, k) counts and the region map. No reader sees family,
truth, base rates or onset. Output: the first day it PROPOSES a character change,
or None. A proposal would still need the external authority grant; that gate is
held constant and outside this experiment.

Timeline at evaluation day d (data through day d inclusive):
  span    = days d-41 .. d            (42 days)
  blocks  = [d-41..d-28], [d-27..d-14], [d-13..d]
  history = days 0 .. d-42            (must be >= 21 days, so d >= 62)
"""
from __future__ import annotations

import math

import numpy as np
from scipy.stats import binom

from world import DAYS, DELTA

SPAN, BLOCK, NBLOCKS = 42, 14, 3
MIN_HISTORY = 21
FIRST_DAY = SPAN + MIN_HISTORY - 1          # 62
HALF_LIFE = 14.0
DECAY = 0.5 ** (1.0 / HALF_LIFE)
FLOOR = -5.0
THRESH = math.log(19.0)
ALPHA = 0.01
MIN_MSG = 5
Z_CRIT = 2.3263478740408408                  # one-sided p < 0.01

READERS = ["SCALAR", "TERRAIN", "TERRAIN_NO_P", "TERRAIN_NO_K",
           "TERRAIN_NO_HISTORY", "TERRAIN_SHUF_P", "TERRAIN_SHUF_K"]

# Sign-test upper-tail table: P(Binom(Re, .5) >= m)
_SIGN = {Re: binom.sf(np.arange(Re + 2) - 1, Re, 0.5) for Re in range(0, 49)}


def sign_p(positives: int, eligible: int) -> float:
    if eligible == 0:
        return 1.0
    return float(_SIGN[eligible][positives])


def scalar_accumulator(n_tot, k_tot):
    """Recency-weighted log-likelihood pooling. Returns A[d] (nan before FIRST_DAY).
    p0 = pooled historical rate (days < d-41); p1 = p0 + DELTA (true delta: generous)."""
    A = np.full(DAYS, np.nan)
    cn = np.concatenate([[0], np.cumsum(n_tot)])
    ck = np.concatenate([[0], np.cumsum(k_tot)])
    acc = 0.0
    for d in range(FIRST_DAY, DAYS):
        h_end = d - SPAN + 1                     # history = days [0, h_end)
        hn, hk = cn[h_end], ck[h_end]
        p0 = min(max(hk / hn if hn > 0 else 0.1, 1e-4), 0.98)
        p1 = min(p0 + DELTA, 0.99)
        nd, kd = n_tot[d], k_tot[d]
        llr = kd * math.log(p1 / p0) + (nd - kd) * math.log((1 - p1) / (1 - p0))
        acc = max(acc * DECAY + llr, FLOOR)
        A[d] = acc
    return A


def _block_sign_pass(nb, kb, hn, hk, pooled_rate, own_history=True):
    """One block: sign test that region excess over history is positive more often than chance."""
    elig = (nb >= MIN_MSG) & (hn >= MIN_MSG)
    if not elig.any():
        return False
    if own_history:
        rate = np.where(hn > 0, hk / np.maximum(hn, 1), 0.0)
    else:
        rate = np.full_like(nb, pooled_rate, dtype=float)
    excess = kb - nb * rate
    pos = int(((excess > 0) & elig).sum())
    return sign_p(pos, int(elig.sum())) < ALPHA


def _block_pooled_pass(nb, kb, pooled_rate):
    N, K = nb.sum(), kb.sum()
    if N == 0 or pooled_rate <= 0 or pooled_rate >= 1:
        return False
    z = (K - N * pooled_rate) / math.sqrt(N * pooled_rate * (1 - pooled_rate))
    return z > Z_CRIT


def read_stream(nR, kR, readers, shuffle_key=None):
    """Run the requested readers over one regionized stream.
    Returns {reader: first proposal day or None} and the scalar accumulator."""
    n_tot, k_tot = nR.sum(axis=1), kR.sum(axis=1)
    A = scalar_accumulator(n_tot, k_tot)
    cn = np.vstack([np.zeros((1, nR.shape[1]), dtype=np.int64), np.cumsum(nR, axis=0)])
    ck = np.vstack([np.zeros((1, kR.shape[1]), dtype=np.int64), np.cumsum(kR, axis=0)])
    out = {r: None for r in readers}
    rng = np.random.default_rng(shuffle_key) if shuffle_key is not None else None

    for d in range(FIRST_DAY, DAYS):
        scalar_ok = A[d] > THRESH
        if "SCALAR" in out and out["SCALAR"] is None and scalar_ok:
            out["SCALAR"] = d
        if not scalar_ok:
            continue                                 # TERRAIN variants are nested in SCALAR
        h_end = d - SPAN + 1
        hn, hk = cn[h_end], ck[h_end]
        pooled = hk.sum() / hn.sum() if hn.sum() > 0 else 0.0
        starts = [d - SPAN + 1 + i * BLOCK for i in range(NBLOCKS)]
        blocks = [(cn[s + BLOCK] - cn[s], ck[s + BLOCK] - ck[s]) for s in starts]

        for r in readers:
            if r == "SCALAR" or out[r] is not None:
                continue
            if r == "TERRAIN":
                ok = all(_block_sign_pass(nb, kb, hn, hk, pooled) for nb, kb in blocks)
            elif r == "TERRAIN_NO_P":
                ok = all(_block_pooled_pass(nb, kb, pooled) for nb, kb in blocks)
            elif r == "TERRAIN_NO_K":
                nb, kb = blocks[-1]
                ok = _block_sign_pass(nb, kb, hn, hk, pooled)
            elif r == "TERRAIN_NO_HISTORY":
                ok = all(_block_sign_pass(nb, kb, hn, hk, pooled, own_history=False) for nb, kb in blocks)
            elif r == "TERRAIN_SHUF_P":
                ok = True
                for nb, kb in blocks:
                    K = int(kb.sum())
                    kb_s = rng.multivariate_hypergeometric(nb.astype(np.int64), K) if K > 0 else np.zeros_like(kb)
                    if not _block_sign_pass(nb, kb_s, hn, hk, pooled):
                        ok = False
                        break
            elif r == "TERRAIN_SHUF_K":
                days = np.arange(d - SPAN + 1, d + 1)
                perm = rng.permutation(days)
                ok = True
                for i in range(NBLOCKS):
                    sel = perm[i * BLOCK:(i + 1) * BLOCK]
                    nb = nR[sel].sum(axis=0)
                    kb = kR[sel].sum(axis=0)
                    if not _block_sign_pass(nb, kb, hn, hk, pooled):
                        ok = False
                        break
            else:
                raise ValueError(r)
            if ok:
                out[r] = d
    return out, A


def top_excess_region(nR, kR, d=DAYS - 1):
    """Region with the largest pooled count excess over its own history in the last 42 days."""
    cn = np.vstack([np.zeros((1, nR.shape[1]), dtype=np.int64), np.cumsum(nR, axis=0)])
    ck = np.vstack([np.zeros((1, kR.shape[1]), dtype=np.int64), np.cumsum(kR, axis=0)])
    h_end = d - SPAN + 1
    hn, hk = cn[h_end], ck[h_end]
    sn, sk = cn[d + 1] - cn[h_end], ck[d + 1] - ck[h_end]
    elig = (sn >= MIN_MSG) & (hn >= MIN_MSG)
    rate = np.where(hn > 0, hk / np.maximum(hn, 1), 0.0)
    excess = np.where(elig, sk - sn * rate, -np.inf)
    return int(np.argmax(excess))
