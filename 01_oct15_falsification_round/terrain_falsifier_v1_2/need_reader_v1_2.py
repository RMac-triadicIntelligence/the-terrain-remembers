"""
need_reader_v1_2.py — v1.2 organism. Identical to v1.1 except the reopening rule.

v1.1: a HELD item reopens only if the signal appears OUTSIDE its footprint
      (sign test over non-footprint regions). With >= 10 of 16 regions in the
      footprint that test can never pass: an absorbing hold.
v1.2: a HELD item is reconsidered only on NEW evidence — days after the hold —
      read across the WHOLE terrain against the baseline the hold was judged on.
      Spread (positional sign test) AND persistence (pooled z) are both required,
      so pressure alone still never reopens. The footprint is recorded, not used.
Implements PREREG.json v1.2 exactly.
"""
from __future__ import annotations

import math

import numpy as np

import v1_readers as V1
from need_reader_v1_1 import look, encounters, _cums  # unchanged v1.1 look
from world import DAYS

THRESH, Z_CRIT = V1.THRESH, V1.Z_CRIT
SPAN, BLOCK, FIRST_DAY, MIN_MSG, ALPHA = V1.SPAN, V1.BLOCK, V1.FIRST_DAY, V1.MIN_MSG, V1.ALPHA


def new_evidence_check(cn, ck, d, h, pressure_only=False, old_evidence=False):
    """Returns (fires, regions_evaluated). Requires d - h >= BLOCK (caller enforces)."""
    b_end = h - SPAN + 1                       # baseline = days before the hold-look's span
    bn, bk = cn[b_end], ck[b_end]
    w0 = (d - SPAN + 1) if old_evidence else (h + 1)
    wn, wk = cn[d + 1] - cn[w0], ck[d + 1] - ck[w0]
    elig = (wn >= MIN_MSG) & (bn >= MIN_MSG)
    n_elig = int(elig.sum())
    BN, BK = bn[elig].sum(), bk[elig].sum()
    WN, WK = wn[elig].sum(), wk[elig].sum()
    if n_elig == 0 or WN == 0 or BN == 0:
        return False, n_elig
    p0 = BK / BN
    if not (0 < p0 < 1):
        return False, n_elig
    persist = (WK - WN * p0) / math.sqrt(WN * p0 * (1 - p0)) > Z_CRIT
    if pressure_only:
        return bool(persist), n_elig
    rate = np.where(bn > 0, bk / np.maximum(bn, 1), 0.0)
    pos = int((((wk - wn * rate) > 0) & elig).sum())
    spread = V1.sign_p(pos, n_elig) < ALPHA
    return bool(spread and persist), n_elig


def run_need(nR, kR, enc, pressure_only=False, old_evidence=False, poll=False):
    R = nR.shape[1]
    A = V1.scalar_accumulator(nR.sum(axis=1), kR.sum(axis=1))
    cn, ck = _cums(nR, kR)
    state, F, h = "OPEN", None, None
    out = dict(propose_day=None, looks=0, checks=0, region_evals=0, reopens=0,
               first_look=None, need_events=0, footprint_sizes=[])
    for d in range(FIRST_DAY, DAYS):
        a = A[d]
        prev = A[d - 1] if d > FIRST_DAY else 0.0
        need = (prev <= THRESH < a) or (bool(enc[d]) and a > THRESH)
        if poll:
            need = a > THRESH
        if not need or state == "PROPOSED":
            continue
        out["need_events"] += 1
        if state == "HELD":
            if d - h < BLOCK:                    # not enough new evidence yet: no check
                continue
            fires, n_e = new_evidence_check(cn, ck, d, h, pressure_only, old_evidence)
            out["checks"] += 1
            out["region_evals"] += n_e
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
            state, F, h = "HELD", F_new, d
            out["footprint_sizes"].append(len(F_new))
    out["final_state"] = state
    return out
