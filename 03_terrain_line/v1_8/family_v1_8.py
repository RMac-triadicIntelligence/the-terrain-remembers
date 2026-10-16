"""
family_v1_8.py — scout finds go pending; a different member arrives LATER and confirms the
same regions on new ground; unconfirmed finds lapse with no penalty; housekeeper keeps the
record. Implements PREREG.json v1.8 exactly.
"""
from __future__ import annotations

import math

import numpy as np
import v1_readers as V1
from need_reader_v1_1 import encounters, _cums
from family_v1_7 import scout
from world import DAYS

THRESH, Z_CRIT, FIRST_DAY, SPAN, BLOCK = V1.THRESH, V1.Z_CRIT, V1.FIRST_DAY, V1.SPAN, V1.BLOCK
MIN_MSG, ALPHA = V1.MIN_MSG, V1.ALPHA


def witness(cn, ck, find, d):
    """Read the find's up-regions on days f+1..d only, against the find's own baseline."""
    f, up = find["day"], find["up"]
    base = f - SPAN + 1
    hn, hk = cn[base], ck[base]
    gn, gk = cn[d + 1] - cn[f + 1], ck[d + 1] - ck[f + 1]
    rate = np.clip(np.where(hn > 0, hk / np.maximum(hn, 1), 0.0), 1e-3, 0.999)
    check = up & (gn >= MIN_MSG) & (hn >= MIN_MSG)
    m = int(check.sum())
    if m == 0:
        return False
    agree = int((((gk - gn * rate) > 0) & check).sum())
    p0 = hk.sum() / hn.sum() if hn.sum() > 0 else 0.0
    N, K = gn[check].sum(), gk[check].sum()
    if N == 0 or not (0 < p0 < 1):
        return False
    z = (K - N * p0) / math.sqrt(N * p0 * (1 - p0))
    return V1.sign_p(agree, m) < ALPHA and z > Z_CRIT


def run_family(nR, kR, enc, scout_alone=False, lapse_penalty=False):
    R = nR.shape[1]
    A = V1.scalar_accumulator(nR.sum(axis=1), kR.sum(axis=1))
    cn, ck = _cums(nR, kR)
    record, pending, state = [], None, "OPEN"
    out = dict(propose_day=None, discoveries=0, confirmed=0, lapsed=0, region_evals=0)
    for d in range(FIRST_DAY, DAYS):
        a = A[d]; prev = A[d - 1] if d > FIRST_DAY else 0.0
        need = (prev <= THRESH < a) or (bool(enc[d]) and a > THRESH)
        if not need or state == "PROPOSED":
            continue
        if pending is not None and d - pending["day"] >= BLOCK:          # the witness arrives
            out["region_evals"] += R
            if witness(cn, ck, pending, d):
                out["confirmed"] += 1; record.append((d, 1))
            else:
                out["lapsed"] += 1
                record.append((d, -1 if lapse_penalty else 0))           # knowledge, no weight
            pending = None
        if pending is None:                                              # the scout goes out
            out["region_evals"] += R
            found, up = scout(cn, ck, d)
            if found:
                out["discoveries"] += 1
                if scout_alone:
                    record.append((d, 1))
                else:
                    pending = dict(day=d, up=up)
        present = sum(v for day, v in record if day >= d - SPAN + 1)
        if present > 0:
            state, out["propose_day"] = "PROPOSED", d
        else:
            state = "HELD"
    out["final_state"] = state
    return out
