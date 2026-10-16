"""
map_v1_9.py — the map layer: local scout, later witness, ask the conductor.
Never changes character, never acts on its own. Implements PREREG.json v1.9 exactly.
"""
from __future__ import annotations

import math

import numpy as np
import v1_readers as V1
from need_reader_v1_1 import _cums
from world import DAYS

THRESH, Z_CRIT, FIRST_DAY, SPAN, BLOCK, MIN_MSG = V1.THRESH, V1.Z_CRIT, V1.FIRST_DAY, V1.SPAN, V1.BLOCK, V1.MIN_MSG
Z_SCOUT = 3.4155                      # one-sided p < 0.01 / 16


def _region_z(cn, ck, r, a, b, base_end):
    hn, hk = cn[base_end][r], ck[base_end][r]
    gn, gk = cn[b + 1][r] - cn[a][r], ck[b + 1][r] - ck[a][r]
    if gn < MIN_MSG or hn < MIN_MSG:
        return None
    p = min(max(hk / hn, 1e-3), 0.999)
    return (gk - gn * p) / math.sqrt(gn * p * (1 - p))


def run_map(nR, kR, enc, character_propose_day):
    R = nR.shape[1]
    A = V1.scalar_accumulator(nR.sum(axis=1), kR.sum(axis=1))
    cn, ck = _cums(nR, kR)
    pending, asked = {}, set()
    out = dict(asks=[], discoveries=0, confirmed=0, lapsed=0)
    for d in range(FIRST_DAY, DAYS):
        a = A[d]; prev = A[d - 1] if d > FIRST_DAY else 0.0
        need = (prev <= THRESH < a) or (bool(enc[d]) and a > THRESH)
        if not need:
            continue
        confirmed_now = []
        for r, f in list(pending.items()):                      # witnesses arrive
            if d - f >= BLOCK:
                z = _region_z(cn, ck, r, f + 1, d, f - SPAN + 1)
                if z is not None and z > Z_CRIT:
                    out["confirmed"] += 1; confirmed_now.append(r)
                else:
                    out["lapsed"] += 1
                del pending[r]
        for r in range(R):                                      # local scouts go out
            if r in pending or r in asked:
                continue
            z = _region_z(cn, ck, r, d - BLOCK + 1, d, d - SPAN + 1)
            if z is not None and z > Z_SCOUT:
                pending[r] = d; out["discoveries"] += 1
        character_crossed = character_propose_day is not None and character_propose_day <= d
        new = [r for r in confirmed_now if r not in asked]
        if new and not character_crossed:                       # ask the conductor, once
            out["asks"].append(dict(day=d, regions=sorted(new)))
            asked.update(new)
    return out
