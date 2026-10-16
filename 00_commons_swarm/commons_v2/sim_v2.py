"""Commons swarm v2. Implements PREREG.json (frozen first). World, energy, constitution, births, jubilee as v1."""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PREREG = (HERE / "PREREG.sha256").read_text().split()[0]
assert hashlib.sha256((HERE / "PREREG.json").read_bytes()).hexdigest() == PREREG, "PREREG changed"
sys.path.insert(0, str(HERE.parent / "commons_sim"))
import sim as v1  # noqa: E402  frozen v1: world builder and constants reused

N, STEPS, SEASON, NPATCH = v1.N, v1.STEPS, v1.SEASON, v1.NPATCH
REGROW, SEED_FOOD, KFLOOR = v1.REGROW, v1.SEED_FOOD, v1.KFLOOR
NOISE, EAT, METAB, E0 = v1.NOISE, v1.EAT, v1.METAB, v1.E0
FAMS, FOUNDERS, WITNESS_T, WITNESS_TOL = v1.FAMS, v1.FOUNDERS, v1.WITNESS_T, v1.WITNESS_TOL
D_TOL, D_UP, D_DOWN, D_STAY, RADIUS = v1.D_TOL, v1.D_UP, v1.D_DOWN, v1.D_STAY, v1.RADIUS
GRACE_EVERY, GRACE_MIN, JUBILEE = v1.GRACE_EVERY, v1.GRACE_MIN, v1.JUBILEE
BIRTH_EVERY, BIRTH_HARVEST, BIRTH_STOCK, BIRTH_COST, SPLIT_E, SAFETY_CAP = (
    v1.BIRTH_EVERY, v1.BIRTH_HARVEST, v1.BIRTH_STOCK, v1.BIRTH_COST, v1.SPLIT_E, v1.SAFETY_CAP)
# v2 constants (PREREG)
SPACING_W, WEAN_W, WEAN_TAU, WEAN_FLOOR = 0.3, 0.2, 100.0, 0.02
DWELL_FOOD, SCOUT_EVERY, CALL_LOW, CALL_VALUE, BUD_SIZE = 0.05, 3, 0.1, 0.3, 10

VARIANTS = ["V2_FULL", "V2_LONE", "NO_SPACING", "NO_ROLES", "NO_BUDDING", "NO_WEANING",
            "V2_NO_CONSTITUTION", "V2_SELF_REPLICATING"]


class Agent:
    __slots__ = ("id", "fam", "lineage", "x", "y", "e", "d", "run", "belief", "target", "alive", "born")

    def __init__(self, aid, fam, lineage, x, y, e, belief, born):
        self.id, self.fam, self.lineage, self.x, self.y, self.e = aid, fam, lineage, x, y, e
        self.d, self.run, self.belief, self.target, self.alive, self.born = 0.0, 0, belief, None, True, born


class Family:
    def __init__(self, M=None, C=None, T=None):
        self.M = np.zeros((N, N)) if M is None else M.copy()
        self.C = np.zeros((N, N)) if C is None else C.copy()
        self.T = -np.ones((N, N)) if T is None else T.copy()   # time each cell was last confirmed
        self.pending, self.period_harvest = [], 0.0


def step_toward(a, tx, ty):
    a.x = (a.x + int(np.sign(v1.wrap_delta(a.x, tx)))) % N
    a.y = (a.y + int(np.sign(v1.wrap_delta(a.y, ty)))) % N


def window(a):
    xs = [(a.x + dx) % N for dx in range(-RADIUS, RADIUS + 1)]
    ys = [(a.y + dy) % N for dy in range(-RADIUS, RADIUS + 1)]
    return xs, ys


def run(variant, seed, log_series=False):
    wrng = np.random.default_rng([seed, 1]); arng = np.random.default_rng([seed, 2])
    centres = [tuple(wrng.integers(0, N, 2)) for _ in range(NPATCH)]
    K = v1.capacity(centres); R = K.copy(); R0 = R.sum()
    lone = variant == "V2_LONE"
    spacing = variant != "NO_SPACING"; roles = variant != "NO_ROLES"
    budding = variant not in ("NO_BUDDING", "V2_SELF_REPLICATING", "V2_LONE")
    weaning = variant != "NO_WEANING"
    direct = variant in ("V2_NO_CONSTITUTION", "V2_LONE")
    fams, agents, nid, nfam = {}, [], 0, 0
    for f in range(FAMS):
        if not lone:
            fams[nfam] = Family(); fid = nfam; nfam += 1
        for _ in range(FOUNDERS):
            if lone:
                fams[nfam] = Family(); fid = nfam; nfam += 1
            x, y = (int(v) for v in arng.integers(0, N, 2))
            agents.append(Agent(nid, fid, f, x, y, E0, np.zeros((N, N)), 0)); nid += 1
    out = dict(h=0.0, late=0.0, post=0.0, smin=1.0, peak=0, me=0.0, men=0, ast=0, stuck=0, cap=False)
    series = []
    for t in range(STEPS):
        if t > 0 and t % SEASON == 0:
            centres = [tuple(wrng.integers(0, N, 2)) for _ in range(NPATCH)]; K = v1.capacity(centres)
        live = [a for a in agents if a.alive]
        occ = {}
        for a in live:
            g = occ.setdefault(a.fam, np.zeros((N, N))); g[a.x, a.y] += 1
        crowd = {f: sum(np.roll(np.roll(g, dx, 0), dy, 1) for dx in (-1, 0, 1) for dy in (-1, 0, 1)) for f, g in occ.items()}
        order = arng.permutation(len(live)); ht = 0.0
        for i in order:
            a = live[i]; fam = fams[a.fam]
            obs = R[a.x, a.y] + NOISE * arng.standard_normal()
            if abs(obs - a.belief[a.x, a.y]) > D_TOL:
                a.d += D_UP * (1 - a.d)
            else:
                a.d -= D_DOWN * a.d
            a.belief[a.x, a.y] = obs
            if direct:
                fam.M[a.x, a.y], fam.C[a.x, a.y], fam.T[a.x, a.y] = obs, 1.0, t
            else:
                hit = None
                for k, (px, py, v, pid, pt) in enumerate(fam.pending):
                    if px == a.x and py == a.y and pid != a.id and t - pt <= WITNESS_T and abs(v - obs) < WITNESS_TOL:
                        hit = k; break
                if hit is not None:
                    px, py, v, pid, pt = fam.pending.pop(hit)
                    fam.M[a.x, a.y], fam.C[a.x, a.y], fam.T[a.x, a.y] = (v + obs) / 2, 1.0, t
                else:
                    fam.pending.append((a.x, a.y, obs, a.id, t))
            e = min(EAT, R[a.x, a.y]); R[a.x, a.y] -= e
            a.e += e - METAB; ht += e; fam.period_harvest += e
        # love: sharing never stops; copying fades with experience (weaning)
        for a in live:
            fam = fams[a.fam]
            w = WEAN_W * max(WEAN_FLOOR / WEAN_W, np.exp(-(t - a.born) / WEAN_TAU)) if weaning else WEAN_W
            a.belief += w * fam.C * (fam.M - a.belief)
        # move: dwell where it matters, scouts explore, keepers spread out, calls for witness
        for a in live:
            out["ast"] += 1; fam = fams[a.fam]
            if a.target is not None:
                if (a.x, a.y) == a.target:
                    a.target = None
                else:
                    step_toward(a, *a.target); continue
            here = a.belief[a.x, a.y]
            if a.d > D_STAY and here > DWELL_FOOD:
                a.run += 1; out["stuck"] += 1; continue
            a.run = 0
            xs, ys = window(a)
            scout = roles and a.id % SCOUT_EVERY == 0
            if scout:
                sub = fam.C[np.ix_(xs, ys)] + 1e-3 * arng.random((2 * RADIUS + 1, 2 * RADIUS + 1))
                i, j = np.unravel_index(int(np.argmin(sub)), sub.shape)
            else:
                sub = a.belief[np.ix_(xs, ys)]
                if spacing and a.fam in crowd:
                    c = crowd[a.fam][np.ix_(xs, ys)].copy(); c[RADIUS, RADIUS] -= 1  # not counting itself
                    sub = sub - SPACING_W * c
                if a.belief[np.ix_(xs, ys)].max() <= CALL_LOW and not direct:
                    calls = [p for p in fam.pending if p[2] > CALL_VALUE and p[3] != a.id]
                    if calls:
                        p = max(calls, key=lambda q: q[4]); a.target = (p[0], p[1]); step_toward(a, p[0], p[1]); continue
                if a.belief[np.ix_(xs, ys)].max() <= 0.05:
                    a.x = (a.x + int(arng.integers(-1, 2))) % N; a.y = (a.y + int(arng.integers(-1, 2))) % N; continue
                i, j = np.unravel_index(int(np.argmax(sub)), sub.shape)
            a.x = (a.x + int(np.sign(i - RADIUS))) % N; a.y = (a.y + int(np.sign(j - RADIUS))) % N
        # grace toward the frontier: kin's most recent confirmed discovery
        if t % GRACE_EVERY == 0:
            cand = [a for a in live if a.run >= GRACE_MIN]
            if cand:
                a = max(cand, key=lambda z: (z.run, -z.id)); fam = fams[a.fam]
                a.d, a.run = 0.3, 0
                fresh = np.where(fam.M > CALL_VALUE, fam.T, -1)
                if fresh.max() >= 0:
                    a.target = tuple(int(v) for v in np.unravel_index(int(np.argmax(fresh)), fresh.shape))
        for fam in fams.values():
            fam.C *= JUBILEE
            fam.pending = [p for p in fam.pending if t - p[4] <= WITNESS_T]
        for a in live:
            if a.e <= 0:
                a.alive = False
        live = [a for a in agents if a.alive]
        # births
        if variant == "V2_SELF_REPLICATING":
            for a in list(live):
                if a.e > SPLIT_E:
                    if len(live) >= SAFETY_CAP:
                        out["cap"] = True; continue
                    a.e /= 2
                    agents.append(Agent(nid, a.fam, a.lineage, a.x, a.y, a.e, fams[a.fam].M.copy(), t)); nid += 1
                    live.append(agents[-1])
        elif t > 0 and t % BIRTH_EVERY == 0:
            if budding:
                for fid in list(fams):
                    members = sorted([a for a in live if a.fam == fid], key=lambda z: z.id)
                    if len(members) > BUD_SIZE:
                        old = fams[fid]; nf = nfam; nfam += 1
                        fams[nf] = Family(old.M, old.C, old.T)
                        for a in members[len(members) // 2:]:
                            a.fam = nf
            if R.sum() >= BIRTH_STOCK * R0:
                for fid, fam in list(fams.items()):
                    members = [a for a in live if a.fam == fid]
                    if members and fam.period_harvest > BIRTH_HARVEST and len(live) < SAFETY_CAP:
                        p = max(members, key=lambda z: (z.e, -z.id))
                        if p.e > BIRTH_COST:
                            p.e -= BIRTH_COST
                            if lone:
                                nf = nfam; nfam += 1; fams[nf] = Family(); belief = np.zeros((N, N))
                            else:
                                nf = fid; belief = fam.M.copy()
                            agents.append(Agent(nid, nf, p.lineage, p.x, p.y, BIRTH_COST, belief, t)); nid += 1
                            live.append(agents[-1])
            for fam in fams.values():
                fam.period_harvest = 0.0
        Keff = np.maximum(K, KFLOOR)
        R = np.clip(R + REGROW * R * (1 - R / Keff) + SEED_FOOD, 0, None)
        out["h"] += ht
        if t >= 300:
            out["late"] += ht
        if any(s <= t < s + 50 for s in (150, 300, 450)):
            out["post"] += ht
        out["smin"] = min(out["smin"], R.sum() / R0); out["peak"] = max(out["peak"], len(live))
        for fid, fam in fams.items():
            m = fam.C > 0.2
            if m.any() and any(a.fam == fid for a in live):
                out["me"] += float(np.abs(fam.M[m] - R[m]).mean()); out["men"] += 1
        if log_series:
            series.append(dict(t=t, pop=len(live), harvest=round(ht, 4)))
    live = [a for a in agents if a.alive]
    res = dict(harvest_total=round(float(out["h"]), 4), harvest_late=round(float(out["late"]), 4),
               post_shift=round(float(out["post"]), 4), stock_min=round(float(out["smin"]), 4),
               pop_final=len(live), pop_peak=out["peak"], families_alive=len({a.lineage for a in live}),
               households_final=len({a.fam for a in live}),
               map_error=round(out["me"] / max(out["men"], 1), 4), stuck_frac=round(out["stuck"] / max(out["ast"], 1), 4),
               per_capita=round(float(out["h"]) / max(out["ast"], 1), 5), cap_hit=out["cap"])
    return (res, series) if log_series else res
