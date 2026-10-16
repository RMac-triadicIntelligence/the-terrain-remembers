"""
need_reader_v1_4.py — readings deposit onto position.

Every need: a fresh full look at the present terrain (unchanged look, no anchor).
Each look deposits +1 (reads change) or -1 (reads not-yet) onto the question's position.
Deposits never decay. The question PROPOSES when its accumulated position > 0.
Implements PREREG.json v1.4 exactly.
"""
from __future__ import annotations

import v1_readers as V1
from need_reader_v1_1 import look, encounters, _cums
from world import DAYS

THRESH, FIRST_DAY = V1.THRESH, V1.FIRST_DAY


def run_need(nR, kR, enc):
    R = nR.shape[1]
    A = V1.scalar_accumulator(nR.sum(axis=1), kR.sum(axis=1))
    cn, ck = _cums(nR, kR)
    position, state = 0, "OPEN"
    out = dict(propose_day=None, looks=0, region_evals=0, first_look=None, final_position=0)
    for d in range(FIRST_DAY, DAYS):
        a = A[d]; prev = A[d - 1] if d > FIRST_DAY else 0.0
        need = (prev <= THRESH < a) or (bool(enc[d]) and a > THRESH)
        if not need or state == "PROPOSED":
            continue
        reads_change, _, cost = look(cn, ck, d, R)
        out["looks"] += 1
        out["region_evals"] += cost
        position += 1 if reads_change else -1
        crossed = position > 0
        if out["first_look"] is None:
            out["first_look"] = "PROPOSED" if crossed else "HELD"
        if crossed:
            state, out["propose_day"] = "PROPOSED", d
        else:
            state = "HELD"
    out["final_state"], out["final_position"] = state, position
    return out
