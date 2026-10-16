"""
need_reader_v1_6.py — the organism rereads its own record from where it stands now.

As v1.5, plus: every reading is stored with what it saw (SDKP trace). When torn (present look
reads change, present tally not > 0), the organism chooses to consult its record. Readings
older than the present span are re-read from the present position: an old reading whose
positive regions agree with the present reading's positive regions (look's sign test,
p < .01) re-reads as 'the beginning of this' (+1). Otherwise 0: knowledge, no penalty.
Implements PREREG.json v1.6 exactly.
"""
from __future__ import annotations

import math

import numpy as np
import v1_readers as V1
from need_reader_v1_1 import look, encounters, _cums, _span_hist, _region_z
from world import DAYS

THRESH, FIRST_DAY, SPAN, BLOCK, NBLOCKS = V1.THRESH, V1.FIRST_DAY, V1.SPAN, V1.BLOCK, V1.NBLOCKS
MIN_MSG, ALPHA = V1.MIN_MSG, V1.ALPHA


def sdkp_trace(cn, ck, d):
    """What a reading at day d saw: Position (region signs), Density, Kinetics (block z)."""
    hn, hk, sn, sk = _span_hist(cn, ck, d)
    elig = (sn >= MIN_MSG) & (hn >= MIN_MSG)
    _z, rate = _region_z(sn, sk, hn, hk)
    excess = sk - sn * rate
    signs = np.where(elig, np.sign(excess), 0).astype(int)
    pooled = hk.sum() / hn.sum() if hn.sum() > 0 else 0.0
    kin = []
    for i in range(NBLOCKS):
        s = d - SPAN + 1 + i * BLOCK
        nb = (cn[s + BLOCK] - cn[s]).sum(); kb = (ck[s + BLOCK] - ck[s]).sum()
        kin.append(float((kb - nb * pooled) / math.sqrt(nb * pooled * (1 - pooled)))
                   if nb > 0 and 0 < pooled < 1 else 0.0)
    return dict(position=signs, density=int(sn.sum()), kinetics=kin)


def rereads_as_beginning(old, now):
    pos_now = now["position"] == 1
    m = int(pos_now.sum())
    if m == 0:
        return False
    agree = int((old["position"][pos_now] == 1).sum())
    return V1.sign_p(agree, m) < ALPHA


def run_need(nR, kR, enc):
    R = nR.shape[1]
    A = V1.scalar_accumulator(nR.sum(axis=1), kR.sum(axis=1))
    cn, ck = _cums(nR, kR)
    record, state = [], "OPEN"
    out = dict(propose_day=None, looks=0, region_evals=0, first_look=None,
               consults=0, rereads_beginning=0, crossed_by_reread=False)
    for d in range(FIRST_DAY, DAYS):
        a = A[d]; prev = A[d - 1] if d > FIRST_DAY else 0.0
        need = (prev <= THRESH < a) or (bool(enc[d]) and a > THRESH)
        if not need or state == "PROPOSED":
            continue
        reads_change, _, cost = look(cn, ck, d, R)
        out["looks"] += 1
        out["region_evals"] += cost
        now = sdkp_trace(cn, ck, d)
        record.append(dict(day=d, verdict=1 if reads_change else -1, trace=now))
        present = sum(e["verdict"] for e in record if e["day"] >= d - SPAN + 1)
        crossed = present > 0
        if reads_change and not crossed:                         # torn: its own choice to consult
            out["consults"] += 1
            older = [e for e in record if e["day"] < d - SPAN + 1]
            out["region_evals"] += R * len(older)
            gained = sum(1 for e in older if rereads_as_beginning(e["trace"], now))
            out["rereads_beginning"] += gained
            if present + gained > 0:
                crossed, out["crossed_by_reread"] = True, True
        if out["first_look"] is None:
            out["first_look"] = "PROPOSED" if crossed else "HELD"
        if crossed:
            state, out["propose_day"] = "PROPOSED", d
        else:
            state = "HELD"
    out["final_state"] = state
    return out
