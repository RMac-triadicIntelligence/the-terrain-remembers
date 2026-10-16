"""
need_reader.py — v1.1 organism: deposits every reply, looks only when it needs direction.

States: OPEN -> (look) -> PROPOSED | HELD_UNKNOWN(footprint F)
A HELD item is re-examined only at a need, and only by a partial read of the regions
OUTSIDE its footprint: has the signal spread to new places? Pressure alone never reopens.
Implements PREREG.json v1.1 exactly.
"""
from __future__ import annotations

import math

import numpy as np

import v1_readers as V1
from world import DAYS

THRESH, Z_CRIT = V1.THRESH, V1.Z_CRIT
SPAN, BLOCK, NBLOCKS, FIRST_DAY, MIN_MSG, ALPHA = (V1.SPAN, V1.BLOCK, V1.NBLOCKS,
                                                   V1.FIRST_DAY, V1.MIN_MSG, V1.ALPHA)
Z_FOOT = 1.6448536269514722            # one-sided p < 0.05 for the footprint
ENCOUNTER_P = 2.0 / 7.0


def encounters(lam: int, seed: int) -> np.ndarray:
    """Encounter days: depends only on (lambda, seed), identical across families."""
    rng = np.random.default_rng([20261011, lam, seed])
    return rng.random(DAYS) < ENCOUNTER_P


def _cums(nR, kR):
    z = np.zeros((1, nR.shape[1]), dtype=np.int64)
    return np.vstack([z, np.cumsum(nR, axis=0)]), np.vstack([z, np.cumsum(kR, axis=0)])


def _span_hist(cn, ck, d):
    h_end = d - SPAN + 1
    hn, hk = cn[h_end], ck[h_end]
    sn, sk = cn[d + 1] - cn[h_end], ck[d + 1] - ck[h_end]
    return hn, hk, sn, sk


def _region_z(sn, sk, hn, hk):
    rate = np.clip(np.where(hn > 0, hk / np.maximum(hn, 1), 0.0), 1e-3, 0.999)
    return (sk - sn * rate) / np.sqrt(np.maximum(sn * rate * (1 - rate), 1e-12)), rate


def look(cn, ck, d, R):
    """Full terrain read at day d. Returns (proposed, footprint, region_evals)."""
    hn, hk, sn, sk = _span_hist(cn, ck, d)
    elig = (sn >= MIN_MSG) & (hn >= MIN_MSG)
    z, rate = _region_z(sn, sk, hn, hk)
    excess = sk - sn * rate
    pos = int(((excess > 0) & elig).sum())
    position_ok = V1.sign_p(pos, int(elig.sum())) < ALPHA
    pooled = hk.sum() / hn.sum() if hn.sum() > 0 else 0.0
    persist_ok = True
    for i in range(NBLOCKS):
        s = d - SPAN + 1 + i * BLOCK
        nb = (cn[s + BLOCK] - cn[s]).sum()
        kb = (ck[s + BLOCK] - ck[s]).sum()
        if nb == 0 or not (0 < pooled < 1):
            persist_ok = False
            break
        zb = (kb - nb * pooled) / math.sqrt(nb * pooled * (1 - pooled))
        if not zb > Z_CRIT:
            persist_ok = False
            break
    footprint = frozenset(int(r) for r in np.flatnonzero(elig & (z > Z_FOOT)))
    return position_ok and persist_ok, footprint, R + 3


def reopen_check(cn, ck, d, footprint):
    """Partial read of regions outside the footprint: has the signal spread to new places?"""
    hn, hk, sn, sk = _span_hist(cn, ck, d)
    elig = (sn >= MIN_MSG) & (hn >= MIN_MSG)
    outside = elig.copy()
    for r in footprint:
        outside[r] = False
    _z, rate = _region_z(sn, sk, hn, hk)
    excess = sk - sn * rate
    pos = int(((excess > 0) & outside).sum())
    n_out = int(outside.sum())
    return V1.sign_p(pos, n_out) < ALPHA, n_out


def run_need(nR, kR, enc, ignore_footprint=False, poll=False):
    """One stream. ignore_footprint / poll are MUTANTS for the mutation lane only."""
    R = nR.shape[1]
    A = V1.scalar_accumulator(nR.sum(axis=1), kR.sum(axis=1))
    cn, ck = _cums(nR, kR)
    state, F = "OPEN", None
    out = dict(propose_day=None, looks=0, checks=0, region_evals=0, reopens=0,
               first_look=None, need_events=0)
    for d in range(FIRST_DAY, DAYS):
        a = A[d]
        prev = A[d - 1] if d > FIRST_DAY else 0.0
        crossing = prev <= THRESH < a
        need = crossing or (bool(enc[d]) and a > THRESH)
        if poll:
            need = a > THRESH
        if not need or state == "PROPOSED":
            continue
        out["need_events"] += 1
        if state == "HELD":
            fp = frozenset() if ignore_footprint else F
            fires, n_out = reopen_check(cn, ck, d, fp)
            out["checks"] += 1
            out["region_evals"] += n_out
            if not fires:
                continue
            out["reopens"] += 1
        proposed, F_new, cost = look(cn, ck, d, R)
        out["looks"] += 1
        out["region_evals"] += cost
        if out["first_look"] is None:
            out["first_look"] = "PROPOSED" if proposed else "HELD"
        if proposed:
            state, out["propose_day"] = "PROPOSED", d
        else:
            state, F = "HELD", F_new
    out["final_state"] = state
    return out
