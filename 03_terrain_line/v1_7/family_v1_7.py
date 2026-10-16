"""
family_v1_7.py — scout, homemaker (confirms), housekeeper (keeps the record).
Implements PREREG.json v1.7 exactly.
"""
from __future__ import annotations

import math

import numpy as np
import v1_readers as V1
from need_reader_v1_1 import encounters, _cums
from world import DAYS

THRESH, Z_CRIT, FIRST_DAY, SPAN, BLOCK = V1.THRESH, V1.Z_CRIT, V1.FIRST_DAY, V1.SPAN, V1.BLOCK
MIN_MSG, ALPHA = V1.MIN_MSG, V1.ALPHA


def _ground(cn, ck, d, a, b):
    """Counts on days [a, b] and the per-region baseline before the span (days < d-41)."""
    base = d - SPAN + 1
    hn, hk = cn[base], ck[base]
    gn, gk = cn[b + 1] - cn[a], ck[b + 1] - ck[a]
    rate = np.clip(np.where(hn > 0, hk / np.maximum(hn, 1), 0.0), 1e-3, 0.999)
    elig = (gn >= MIN_MSG) & (hn >= MIN_MSG)
    excess = gk - gn * rate
    p0 = hk.sum() / hn.sum() if hn.sum() > 0 else 0.0
    N, K = gn[elig].sum(), gk[elig].sum()
    z = (K - N * p0) / math.sqrt(N * p0 * (1 - p0)) if N > 0 and 0 < p0 < 1 else -np.inf
    return elig, excess, z


def scout(cn, ck, d):
    elig, excess, z = _ground(cn, ck, d, d - BLOCK + 1, d)
    up = elig & (excess > 0)
    found = V1.sign_p(int(up.sum()), int(elig.sum())) < ALPHA and z > Z_CRIT
    return found, up


def homemaker(cn, ck, d, up):
    elig, excess, z = _ground(cn, ck, d, d - SPAN + 1, d - BLOCK)
    check = up & elig
    m = int(check.sum())
    if m == 0:
        return False
    agree = int(((excess > 0) & check).sum())
    return V1.sign_p(agree, m) < ALPHA and z > Z_CRIT


def run_family(nR, kR, enc, scout_alone=False):
    R = nR.shape[1]
    A = V1.scalar_accumulator(nR.sum(axis=1), kR.sum(axis=1))
    cn, ck = _cums(nR, kR)
    record, state = [], "OPEN"
    out = dict(propose_day=None, scout_reads=0, discoveries=0, confirmed=0, region_evals=0)
    for d in range(FIRST_DAY, DAYS):
        a = A[d]; prev = A[d - 1] if d > FIRST_DAY else 0.0
        need = (prev <= THRESH < a) or (bool(enc[d]) and a > THRESH)
        if not need or state == "PROPOSED":
            continue
        out["scout_reads"] += 1; out["region_evals"] += R
        found, up = scout(cn, ck, d)
        if not found:
            continue
        out["discoveries"] += 1
        if scout_alone:
            ok = True
        else:
            out["region_evals"] += R
            ok = homemaker(cn, ck, d, up)
        out["confirmed"] += int(ok)
        record.append((d, 1 if ok else -1))                      # housekeeper
        present = sum(v for day, v in record if day >= d - SPAN + 1)
        if present > 0:
            state, out["propose_day"] = "PROPOSED", d
        else:
            state = "HELD"
    out["final_state"] = state
    return out
