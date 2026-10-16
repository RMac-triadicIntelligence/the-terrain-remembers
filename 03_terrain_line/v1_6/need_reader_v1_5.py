"""
need_reader_v1_5.py — the record is knowledge, not a penalty.

Fresh full look at every need. Every reading is kept in the question's record forever.
Only readings of the PRESENT terrain (taken within the current look's 42-day span) weigh
on the crossing. Older readings remain in the record and carry no weight.
Implements PREREG.json v1.5 exactly.
"""
from __future__ import annotations

import v1_readers as V1
from need_reader_v1_1 import look, encounters, _cums
from world import DAYS

THRESH, FIRST_DAY, SPAN = V1.THRESH, V1.FIRST_DAY, V1.SPAN


def run_need(nR, kR, enc):
    R = nR.shape[1]
    A = V1.scalar_accumulator(nR.sum(axis=1), kR.sum(axis=1))
    cn, ck = _cums(nR, kR)
    record, state = [], "OPEN"           # record: (day, +1/-1), never deleted
    out = dict(propose_day=None, looks=0, region_evals=0, first_look=None)
    for d in range(FIRST_DAY, DAYS):
        a = A[d]; prev = A[d - 1] if d > FIRST_DAY else 0.0
        need = (prev <= THRESH < a) or (bool(enc[d]) and a > THRESH)
        if not need or state == "PROPOSED":
            continue
        reads_change, _, cost = look(cn, ck, d, R)
        out["looks"] += 1
        out["region_evals"] += cost
        record.append((d, 1 if reads_change else -1))
        present = sum(v for day, v in record if day >= d - SPAN + 1)
        crossed = present > 0
        if out["first_look"] is None:
            out["first_look"] = "PROPOSED" if crossed else "HELD"
        if crossed:
            state, out["propose_day"] = "PROPOSED", d
        else:
            state = "HELD"
    out["final_state"], out["record_len"] = state, len(record)
    return out
