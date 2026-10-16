"""
need_reader_v1_3.py — every reading is a fresh look at the present terrain from the present position.

No anchor: no window or baseline frozen at the hold, no footprint gate.
(A) At every need, OPEN and HELD questions get the unchanged full look.
(B) Basin occupancy (Claude's operationalization, flagged): a HELD question also needs the
    change to have persisted through every complete 14-day block since it was FIRST held,
    against the pre-question baseline.
Implements PREREG.json v1.3 exactly.
"""
from __future__ import annotations

import math

import v1_readers as V1
from need_reader_v1_1 import look, encounters, _cums
from world import DAYS

THRESH, Z_CRIT = V1.THRESH, V1.Z_CRIT
SPAN, BLOCK, FIRST_DAY = V1.SPAN, V1.BLOCK, V1.FIRST_DAY


def lived_through(cn, ck, d, h0):
    """B: persistence through every complete block since first hold. True if no complete block yet."""
    b_end = h0 - SPAN + 1
    BN, BK = cn[b_end].sum(), ck[b_end].sum()
    if BN == 0:
        return False
    p0 = BK / BN
    if not (0 < p0 < 1):
        return False
    s = h0 + 1
    while s + BLOCK - 1 <= d:
        nb = (cn[s + BLOCK] - cn[s]).sum(); kb = (ck[s + BLOCK] - ck[s]).sum()
        if nb == 0 or not (kb - nb * p0) / math.sqrt(nb * p0 * (1 - p0)) > Z_CRIT:
            return False
        s += BLOCK
    return True


def run_need(nR, kR, enc, use_occupancy=True):
    R = nR.shape[1]
    A = V1.scalar_accumulator(nR.sum(axis=1), kR.sum(axis=1))
    cn, ck = _cums(nR, kR)
    state, h0 = "OPEN", None
    out = dict(propose_day=None, looks=0, region_evals=0, first_look=None, b_vetoes=0)
    for d in range(FIRST_DAY, DAYS):
        a = A[d]; prev = A[d - 1] if d > FIRST_DAY else 0.0
        need = (prev <= THRESH < a) or (bool(enc[d]) and a > THRESH)
        if not need or state == "PROPOSED":
            continue
        proposed, _, cost = look(cn, ck, d, R)
        out["looks"] += 1
        out["region_evals"] += cost
        if state == "HELD" and use_occupancy:
            out["region_evals"] += R
            if proposed and not lived_through(cn, ck, d, h0):
                proposed = False
                out["b_vetoes"] += 1
        if out["first_look"] is None:
            out["first_look"] = "PROPOSED" if proposed else "HELD"
        if proposed:
            state, out["propose_day"] = "PROPOSED", d
        elif state != "HELD":
            state, h0 = "HELD", d
    out["final_state"] = state
    return out
