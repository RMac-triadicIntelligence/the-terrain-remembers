"""FLAT, RAG and SQLT readers for terrain_vs_sql v0.1 (PREREG.json)."""
from __future__ import annotations

import math, sqlite3

import numpy as np
import v1_readers as V1
import need_reader_v1_2 as N12
from need_reader_v1_1 import encounters, look as look_v11, _cums
from world import DAYS, HOURS, DAYTYPE, PROFILE, region_of

THRESH, Z_CRIT = V1.THRESH, V1.Z_CRIT
SPAN, BLOCK, NBLOCKS, FIRST_DAY, MIN_MSG = V1.SPAN, V1.BLOCK, V1.NBLOCKS, V1.FIRST_DAY, V1.MIN_MSG
REG16 = region_of(16)


# ------------------------------------------------------------------ FLAT
def look_flat(cn, ck, d, R):
    """v1.1 look with the positional sign test treated as passed."""
    h_end = d - SPAN + 1
    hn, hk = cn[h_end], ck[h_end]
    pooled = hk.sum() / hn.sum() if hn.sum() > 0 else 0.0
    for i in range(NBLOCKS):
        s = d - SPAN + 1 + i * BLOCK
        nb = (cn[s + BLOCK] - cn[s]).sum(); kb = (ck[s + BLOCK] - ck[s]).sum()
        if nb == 0 or not (0 < pooled < 1):
            return False, frozenset(), R + 3
        if not (kb - nb * pooled) / math.sqrt(nb * pooled * (1 - pooled)) > Z_CRIT:
            return False, frozenset(), R + 3
    return True, frozenset(), R + 3


def run_generic(enc, A, cn, ck, R, look_fn, pressure_only):
    """V12's control flow with injectable look/check and injectable data access."""
    state, h = "OPEN", None
    out = dict(propose_day=None, looks=0, checks=0, reopens=0)
    for d in range(FIRST_DAY, DAYS):
        a = A[d]; prev = A[d - 1] if d > FIRST_DAY else 0.0
        need = (prev <= THRESH < a) or (bool(enc[d]) and a > THRESH)
        if not need or state == "PROPOSED":
            continue
        if state == "HELD":
            if d - h < BLOCK:
                continue
            fires, _ = N12.new_evidence_check(cn, ck, d, h, pressure_only=pressure_only)
            out["checks"] += 1
            if not fires:
                continue
            out["reopens"] += 1
        proposed, _, _ = look_fn(cn, ck, d, R)
        out["looks"] += 1
        if proposed:
            state, out["propose_day"] = "PROPOSED", d
        else:
            state, h = "HELD", d
    return out


def run_flat(nR, kR, enc):
    A = V1.scalar_accumulator(nR.sum(axis=1), kR.sum(axis=1))
    cn, ck = _cums(nR, kR)
    return run_generic(enc, A, cn, ck, nR.shape[1], look_flat, pressure_only=True)


# ------------------------------------------------------------------ SQLT
def rows_db(n, k, path=":memory:"):
    """One row per reply: (day, hour, region, truncated)."""
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE ev(day INTEGER, hour INTEGER, region INTEGER, truncated INTEGER)")
    recs = []
    for d in range(DAYS):
        for hr in range(HOURS):
            c, t = int(n[d, hr]), int(k[d, hr])
            if c:
                r = int(REG16[d, hr])
                recs += [(d, hr, r, 1)] * t + [(d, hr, r, 0)] * (c - t)
    con.executemany("INSERT INTO ev VALUES(?,?,?,?)", recs)
    con.commit()
    return con


class SQLCum:
    """cn[t] / ck[t] = per-region message / truncation counts over days < t, by SQL."""
    def __init__(self, con, R, col):
        self.con, self.R, self.col, self.cache = con, R, col, {}
    def __getitem__(self, t):
        if t not in self.cache:
            q = ("SELECT region, COUNT(*), SUM(truncated) FROM ev WHERE day < ? GROUP BY region")
            v = np.zeros(self.R, dtype=np.int64)
            for reg, cnt, tr in self.con.execute(q, (int(t),)):
                v[reg] = cnt if self.col == "n" else (tr or 0)
            self.cache[t] = v
        return self.cache[t]


def run_sqlt(n, k, enc):
    con = rows_db(n, k)
    nt = np.zeros(DAYS, dtype=np.int64); kt = np.zeros(DAYS, dtype=np.int64)
    for d, c, t in con.execute("SELECT day, COUNT(*), SUM(truncated) FROM ev GROUP BY day"):
        nt[d], kt[d] = c, t or 0
    A = V1.scalar_accumulator(nt, kt)
    out = run_generic(enc, A, SQLCum(con, 16, "n"), SQLCum(con, 16, "k"), 16, look_v11, pressure_only=False)
    con.close()
    return out


# ------------------------------------------------------------------ RAG
def encounter_hour(lam, seed, d):
    return int(np.random.default_rng([20261016, lam, seed, d]).choice(HOURS, p=PROFILE))


def rag_decide(n, k, d, h_e):
    """Stateless context retrieval: same day type, hours within 1 of h_e."""
    if d < FIRST_DAY:
        return False
    hours = [h for h in (h_e - 1, h_e, h_e + 1) if 0 <= h < HOURS]
    same = DAYTYPE == DAYTYPE[d]
    days = np.arange(DAYS)
    hist = same & (days < d - SPAN + 1)
    HN, HK = n[hist][:, hours].sum(), k[hist][:, hours].sum()
    if HN == 0:
        return False
    p0 = HK / HN
    if not (0 < p0 < 1):
        return False
    for i in range(NBLOCKS):
        s = d - SPAN + 1 + i * BLOCK
        m = same & (days >= s) & (days < s + BLOCK)
        nb, kb = n[m][:, hours].sum(), k[m][:, hours].sum()
        if nb == 0 or not (kb - nb * p0) / math.sqrt(nb * p0 * (1 - p0)) > Z_CRIT:
            return False
    return True
