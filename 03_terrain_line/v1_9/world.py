"""
world.py — synthetic owner streams for the terrain-vs-scalar confound falsifier.

Implements PREREG.json "world" exactly. Ground truth is returned alongside the
stream for scoring only; no reader receives it.

A stream is two arrays over (day, hour):  n[d, h] messages, k[d, h] truncations.
Day type is a function of the day index, so (day, hour) fixes Position.
Every truncation draws a size from one shared distribution in every family:
per-event indistinguishable = identical in S.
"""
from __future__ import annotations

import numpy as np

DAYS = 150
ONSET = 50
HOURS = 24
DELTA = 0.08
WINDOW_LEN = 30

FAMILIES = ["GENUINE", "COMMUTE", "DINNER", "WINDOW", "COLOCATED", "NULL"]
CONFOUNDS = ["COMMUTE", "DINNER", "WINDOW", "COLOCATED"]
TRUTH_PREFERS = {"GENUINE": True, "COMMUTE": False, "DINNER": False,
                 "WINDOW": False, "COLOCATED": False, "NULL": False}

# Owner activity profile over hours (fixed). Low overnight.
_PROFILE_W = np.array([0.2] * 6 + [1.0] * 4 + [1.2] * 8 + [1.4] * 4 + [0.6] * 2)
PROFILE = _PROFILE_W / _PROFILE_W.sum()

COMMUTE_HOURS = (7, 8, 9)      # weekday only
DINNER_HOURS = (18, 19, 20)    # every day


def is_weekday(d: int) -> bool:
    return d % 7 < 5


DAYTYPE = np.array([0 if is_weekday(d) else 1 for d in range(DAYS)])  # 0 weekday, 1 weekend


def _family_index(family: str) -> int:
    return FAMILIES.index(family)


def excess_matrix(family: str):
    """Additive truncation-probability excess e[d, h] for a family (before capping).

    COMMUTE and DINNER are scaled so their EXPECTED extra truncations per day,
    averaged over a week, equal GENUINE's (DELTA * lambda)."""
    e = np.zeros((DAYS, HOURS))
    post = np.arange(DAYS) >= ONSET
    if family in ("GENUINE", "COLOCATED"):
        e[post, :] = DELTA
    elif family == "COMMUTE":
        f = PROFILE[list(COMMUTE_HOURS)].sum()
        dc = DELTA / (f * 5.0 / 7.0)
        for d in range(DAYS):
            if post[d] and is_weekday(d):
                e[d, list(COMMUTE_HOURS)] = dc
    elif family == "DINNER":
        f = PROFILE[list(DINNER_HOURS)].sum()
        dd = DELTA / f
        for d in range(DAYS):
            if post[d]:
                e[d, list(DINNER_HOURS)] = dd
    elif family == "WINDOW":
        e[ONSET:ONSET + WINDOW_LEN, :] = DELTA
    elif family == "NULL":
        pass
    else:
        raise ValueError(family)
    return e


_EXCESS = {f: excess_matrix(f) for f in FAMILIES}


def stream_rng(family: str, lam: int, seed: int) -> np.random.Generator:
    # Keyed on (family, lambda, seed) only, so every reader and every resolution
    # sees the SAME world for a given key (paired comparisons).
    return np.random.default_rng([20261010, _family_index(family), lam, seed])


def make_stream(family: str, lam: int, seed: int):
    rng = stream_rng(family, lam, seed)
    # Owner-idiosyncratic terrain: base rate per (day_type, hour) cell.
    base = rng.uniform(0.03, 0.20, size=(2, HOURS))
    p = base[DAYTYPE, :] + _EXCESS[family]          # (DAYS, HOURS)
    p = np.clip(p, 0.0, 1.0)
    n = rng.poisson(lam * PROFILE[None, :], size=(DAYS, HOURS))
    k = rng.binomial(n, p)
    # Size S of every truncation: one shared distribution in every family.
    sizes = rng.beta(2.0, 5.0, size=int(k.sum()))
    # Realised expected daily excess (post-cap), for the matching check only.
    realised_excess = float(((p - np.clip(base[DAYTYPE, :], 0, 1)) * lam * PROFILE[None, :])[ONSET:].sum(axis=1).mean())
    return dict(n=n, k=k, sizes=sizes, base=base, realised_daily_excess=realised_excess,
                truth_prefers=TRUTH_PREFERS[family])


# --------------------------------------------------------------------------- #
# Position: regions at resolution R (PREREG adapter choice)                    #
# --------------------------------------------------------------------------- #

def region_of(R: int):
    """Return an int array reg[d, h] -> region id in [0, R)."""
    reg = np.zeros((DAYS, HOURS), dtype=int)
    hrs = np.arange(HOURS)
    for d in range(DAYS):
        dt = DAYTYPE[d]
        if R == 1:
            reg[d] = 0
        elif R == 2:
            reg[d] = dt
        elif R == 4:
            reg[d] = dt * 2 + (hrs >= 12)
        elif R == 8:
            reg[d] = dt * 4 + hrs // 6
        elif R == 16:
            reg[d] = dt * 8 + hrs // 3
        elif R == 48:
            reg[d] = dt * 24 + hrs
        else:
            raise ValueError(R)
    return reg


def regionize(n, k, R: int):
    """Collapse (DAYS, HOURS) counts to (DAYS, R) counts."""
    reg = region_of(R)
    nR = np.zeros((DAYS, R), dtype=np.int64)
    kR = np.zeros((DAYS, R), dtype=np.int64)
    for d in range(DAYS):
        np.add.at(nR[d], reg[d], n[d])
        np.add.at(kR[d], reg[d], k[d])
    return nR, kR


def commute_regions(R: int):
    """Region ids at resolution R that contain true commute cells (weekday 7-9)."""
    reg = region_of(R)
    wd = next(d for d in range(DAYS) if is_weekday(d))
    return sorted({int(reg[wd, h]) for h in COMMUTE_HOURS})
