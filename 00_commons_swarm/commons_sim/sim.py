"""Commons swarm v1. Implements PREREG.json (frozen before this file). Scored only on what the world gives back."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PREREG = (HERE / "PREREG.sha256").read_text().split()[0]
assert hashlib.sha256((HERE / "PREREG.json").read_bytes()).hexdigest() == PREREG, "PREREG changed"
assert hashlib.sha256((HERE / "AMENDMENT_1.json").read_bytes()).hexdigest() == (HERE / "AMENDMENT_1.sha256").read_text().split()[0]

N, STEPS, SEASON, NPATCH, SIG = 32, 600, 150, 6, 3.0
REGROW, SEED_FOOD, KFLOOR = 0.03, 0.001, 0.02
NOISE, EAT, METAB, E0 = 0.25, 0.2, 0.025, 1.0  # METAB per AMENDMENT_1 (was 0.05)
FAMS, FOUNDERS = 4, 6
WITNESS_T, WITNESS_TOL = 20, 0.3
D_TOL, D_UP, D_DOWN, D_STAY = 0.25, 0.15, 0.10, 0.6
RADIUS = 6
GRACE_EVERY, GRACE_MIN = 10, 15
LOVE_W, LOVE_CLOSE = 0.2, 150
TRUST_TOL, TRUST_MULT = 0.3, 0.7
JUBILEE = 0.99
BIRTH_EVERY, BIRTH_HARVEST, BIRTH_STOCK, BIRTH_COST = 25, 1.0, 0.5, 0.5
SPLIT_E = 2.0
SAFETY_CAP = 500  # not in PREREG; declared in README as a safety amendment; reported if ever reached

VARIANTS = ["FULL", "LONE", "NO_CONSTITUTION", "SELF_REPLICATING", "NO_DWELL",
            "NO_GRACE", "LOVE_WINDOW", "KEEPS_RECORD", "NO_JUBILEE"]


def wrap_delta(a, b):
    d = (b - a) % N
    return d - N if d > N // 2 else d


def capacity(centres):
    xs, ys = np.meshgrid(np.arange(N), np.arange(N), indexing="ij")
    K = np.zeros((N, N))
    for cx, cy in centres:
        dx = np.minimum(np.abs(xs - cx), N - np.abs(xs - cx))
        dy = np.minimum(np.abs(ys - cy), N - np.abs(ys - cy))
        K = np.maximum(K, np.exp(-(dx ** 2 + dy ** 2) / (2 * SIG ** 2)))
    return K


class Agent:
    __slots__ = ("id", "fam", "lineage", "x", "y", "e", "d", "run", "belief", "trust", "target", "alive")

    def __init__(self, aid, fam, lineage, x, y, e, belief):
        self.id, self.fam, self.lineage, self.x, self.y, self.e = aid, fam, lineage, x, y, e
        self.d, self.run, self.belief, self.trust, self.target, self.alive = 0.0, 0, belief, {}, None, True


class Family:
    def __init__(self):
        self.M, self.C = np.zeros((N, N)), np.zeros((N, N))
        self.author = -np.ones((N, N, 2), dtype=int)
        self.pending = []  # (x, y, value, agent_id, t)
        self.period_harvest = 0.0


def run(variant, seed, log_series=False):
    wrng = np.random.default_rng([seed, 1])
    arng = np.random.default_rng([seed, 2])
    centres = [tuple(wrng.integers(0, N, 2)) for _ in range(NPATCH)]
    K = capacity(centres); R = K.copy(); R0 = R.sum()
    lone = variant == "LONE"
    fams, agents, next_id = {}, [], 0
    for f in range(FAMS):
        for _ in range(FOUNDERS):
            fid = next_id if lone else f
            fams.setdefault(fid, Family())
            x, y = (int(v) for v in arng.integers(0, N, 2))
            agents.append(Agent(next_id, fid, f, x, y, E0, np.zeros((N, N)))); next_id += 1
    out = dict(harvest_total=0.0, harvest_late=0.0, post_shift=0.0, stock_min=1.0, pop_peak=0,
               map_err_sum=0.0, map_err_n=0, agent_steps=0, stuck_steps=0, cap_hit=False)
    series = []
    for t in range(STEPS):
        if t > 0 and t % SEASON == 0:
            centres = [tuple(wrng.integers(0, N, 2)) for _ in range(NPATCH)]
            K = capacity(centres)
        live = [a for a in agents if a.alive]
        order = arng.permutation(len(live))
        harvest_t = 0.0
        for i in order:
            a = live[i]; fam = fams[a.fam]
            obs = R[a.x, a.y] + NOISE * arng.standard_normal()
            # dwelling
            if variant == "NO_DWELL":
                a.d = 0.0
            elif abs(obs - a.belief[a.x, a.y]) > D_TOL:
                a.d += D_UP * (1 - a.d)
            else:
                a.d -= D_DOWN * a.d
            a.belief[a.x, a.y] = obs
            # keeps a record: judge the kin who marked this cell
            if variant == "KEEPS_RECORD" and fam.C[a.x, a.y] > 0:
                if abs(obs - fam.M[a.x, a.y]) > TRUST_TOL:
                    for au in fam.author[a.x, a.y]:
                        if au >= 0 and au != a.id:
                            a.trust[au] = a.trust.get(au, 1.0) * TRUST_MULT
            # constitution: marks need a different witness
            if variant in ("NO_CONSTITUTION", "LONE"):
                fam.M[a.x, a.y], fam.C[a.x, a.y] = obs, 1.0
                fam.author[a.x, a.y] = (a.id, a.id)
            else:
                hit = None
                for k, (px, py, v, pid, pt) in enumerate(fam.pending):
                    if px == a.x and py == a.y and pid != a.id and t - pt <= WITNESS_T and abs(v - obs) < WITNESS_TOL:
                        hit = k; break
                if hit is not None:
                    px, py, v, pid, pt = fam.pending.pop(hit)
                    fam.M[a.x, a.y], fam.C[a.x, a.y] = (v + obs) / 2, 1.0
                    fam.author[a.x, a.y] = (pid, a.id)
                else:
                    fam.pending.append((a.x, a.y, obs, a.id, t))
            # eat
            e = min(EAT, R[a.x, a.y]); R[a.x, a.y] -= e
            a.e += e - METAB; harvest_t += e; fam.period_harvest += e
        # love: enduring sharing of the family map
        if not (variant == "LOVE_WINDOW" and t >= LOVE_CLOSE):
            for a in live:
                fam = fams[a.fam]
                w = LOVE_W * fam.C
                if variant == "KEEPS_RECORD" and a.trust:
                    tr = np.ones((N, N))
                    for au, val in a.trust.items():
                        m = (fam.author[..., 0] == au) | (fam.author[..., 1] == au)
                        tr[m] = np.minimum(tr[m], val)
                    w = w * tr
                a.belief += w * (fam.M - a.belief)
        # move or dwell
        for a in live:
            out["agent_steps"] += 1
            if a.target is not None:
                tx, ty = a.target
                if (a.x, a.y) == (tx, ty):
                    a.target = None
                else:
                    a.x = (a.x + int(np.sign(wrap_delta(a.x, tx)))) % N
                    a.y = (a.y + int(np.sign(wrap_delta(a.y, ty)))) % N
                    continue
            if a.d > D_STAY:
                a.run += 1; out["stuck_steps"] += 1; continue
            a.run = 0
            xs = [(a.x + dx) % N for dx in range(-RADIUS, RADIUS + 1)]
            ys = [(a.y + dy) % N for dy in range(-RADIUS, RADIUS + 1)]
            sub = a.belief[np.ix_(xs, ys)]
            if sub.max() <= 0.05:
                a.x = (a.x + int(arng.integers(-1, 2))) % N; a.y = (a.y + int(arng.integers(-1, 2))) % N
            else:
                i, j = np.unravel_index(int(np.argmax(sub)), sub.shape)
                a.x = (a.x + int(np.sign(i - RADIUS))) % N; a.y = (a.y + int(np.sign(j - RADIUS))) % N
        # grace from outside: release the longest dweller, toward its family's best cell
        if variant != "NO_GRACE" and t % GRACE_EVERY == 0:
            cand = [a for a in live if a.run >= GRACE_MIN]
            if cand:
                a = max(cand, key=lambda z: (z.run, -z.id)); fam = fams[a.fam]
                a.d, a.run = 0.3, 0
                score = fam.M * fam.C
                if score.max() > 0:
                    a.target = tuple(int(v) for v in np.unravel_index(int(np.argmax(score)), score.shape))
        # jubilee and pending expiry
        for fam in fams.values():
            if variant != "NO_JUBILEE":
                fam.C *= JUBILEE
            fam.pending = [p for p in fam.pending if t - p[4] <= WITNESS_T]
        # deaths
        for a in live:
            if a.e <= 0:
                a.alive = False
        live = [a for a in agents if a.alive]
        # births
        if variant == "SELF_REPLICATING":
            for a in list(live):
                if a.e > SPLIT_E and len(live) < SAFETY_CAP:
                    a.e /= 2
                    fam = fams[a.fam]
                    agents.append(Agent(next_id, a.fam, a.lineage, a.x, a.y, a.e, fam.M.copy())); next_id += 1
                    live.append(agents[-1])
                elif a.e > SPLIT_E:
                    out["cap_hit"] = True
        elif t > 0 and t % BIRTH_EVERY == 0:
            if R.sum() >= BIRTH_STOCK * R0:
                for fid, fam in list(fams.items()):
                    members = [a for a in live if a.fam == fid]
                    if members and fam.period_harvest > BIRTH_HARVEST and len(live) < SAFETY_CAP:
                        p = max(members, key=lambda z: (z.e, -z.id))
                        if p.e > BIRTH_COST:
                            p.e -= BIRTH_COST
                            if lone:
                                nf = next_id; fams[nf] = Family(); belief = np.zeros((N, N))
                            else:
                                nf = fid; belief = fam.M.copy()
                            agents.append(Agent(next_id, nf, p.lineage, p.x, p.y, BIRTH_COST, belief)); next_id += 1
                            live.append(agents[-1])
            for fam in fams.values():
                fam.period_harvest = 0.0
        # world regrows
        Keff = np.maximum(K, KFLOOR)
        R = np.clip(R + REGROW * R * (1 - R / Keff) + SEED_FOOD, 0, None)
        # outcomes from the world
        out["harvest_total"] += harvest_t
        if t >= 300:
            out["harvest_late"] += harvest_t
        if any(s <= t < s + 50 for s in (150, 300, 450)):
            out["post_shift"] += harvest_t
        out["stock_min"] = min(out["stock_min"], R.sum() / R0)
        out["pop_peak"] = max(out["pop_peak"], len(live))
        for fid, fam in fams.items():
            m = fam.C > 0.2
            if m.any() and any(a.fam == fid for a in live):
                out["map_err_sum"] += float(np.abs(fam.M[m] - R[m]).mean()); out["map_err_n"] += 1
        if log_series:
            series.append(dict(t=t, pop=len(live), stock=round(R.sum() / R0, 4), harvest=round(harvest_t, 4)))
    live = [a for a in agents if a.alive]
    res = dict(harvest_total=round(float(out["harvest_total"]), 4), harvest_late=round(float(out["harvest_late"]), 4),
               post_shift=round(float(out["post_shift"]), 4), stock_min=round(float(out["stock_min"]), 4),
               pop_final=len(live), pop_peak=out["pop_peak"],
               families_alive=len({a.lineage for a in live}),
               map_error=round(out["map_err_sum"] / max(out["map_err_n"], 1), 4),
               stuck_frac=round(out["stuck_steps"] / max(out["agent_steps"], 1), 4), cap_hit=out["cap_hit"])
    return (res, series) if log_series else res


if __name__ == "__main__":
    if sys.argv[1:] == ["calibrate"]:
        r, s = run("FULL", 999, log_series=True)
        print("calibration FULL seed 999 (never scored):", r)
        print("pop every 50 steps:", [x["pop"] for x in s[::50]])
        sys.exit(0)
