"""run.py — v1.8 family as frozen; ablations, v1.7, v1.6, v1.2 alongside."""
from __future__ import annotations

import hashlib, json, math
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import v1_readers as V1
import need_reader_v1_2 as N12
import need_reader_v1_6 as N16
import family_v1_7 as F17
import family_v1_8 as F18
from world import DAYS, HOURS, FAMILIES, ONSET, PROFILE, make_stream, regionize

ROOT = Path(__file__).resolve().parent
FROZEN = "155419c676ae402ffe9717e8c5c537236ad40656bf143133646baabcaa4fb03d"
PINNED = {"world.py": "7a15c82a9e7ab727a5374bd3f99dd9a3727496709650b445a4ac9a055329e956",
          "v1_readers.py": "addf121356d6643299494322d3ca3ee4fba83fe5be6099d473bef26a774d1f06"}
R, LAMS = 16, [32, 128, 8]
PREFERS = {"GENUINE": True, "COMMUTE": False, "DINNER": False, "WINDOW": False, "NULL": False, "COLOCATED": False}
ACC = ["GENUINE", "COMMUTE", "DINNER", "WINDOW", "NULL"]
KEYS = ["fam", "scout", "lapse", "v17", "v16", "v12"]


def canonical(o): return json.dumps(o, sort_keys=True, separators=(",", ":"), allow_nan=False)
def sha(p): return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def acc(pd, enc, fam):
    c = n = 0
    for d in range(ONSET, DAYS):
        if enc[d]:
            c += int((pd is not None and pd <= d) == PREFERS[fam]); n += 1
    return c, n


def readers(nR, kR, enc):
    return {"fam": F18.run_family(nR, kR, enc), "scout": F18.run_family(nR, kR, enc, scout_alone=True),
            "lapse": F18.run_family(nR, kR, enc, lapse_penalty=True), "v17": F17.run_family(nR, kR, enc),
            "v16": N16.run_need(nR, kR, enc), "v12": N12.run_need(nR, kR, enc)}


def unit(args):
    fam, lam, seed = args
    s = make_stream(fam, lam, seed)
    nR, kR = regionize(s["n"], s["k"], R)
    enc = N16.encounters(lam, seed)
    o = readers(nR, kR, enc)
    v1, A = V1.read_stream(nR, kR, ["TERRAIN"])
    end = v1["TERRAIN"] if v1["TERRAIN"] is not None else DAYS - 1
    v1l = sum(1 for d in range(V1.FIRST_DAY, end + 1) if A[d] > V1.THRESH)
    row = dict(family=fam, lam=lam, seed=seed, v1_evals=v1l * 3 * R)
    for k in KEYS:
        row[k] = dict(pd=o[k]["propose_day"], evals=o[k]["region_evals"],
                      disc=o[k].get("discoveries", 0), conf=o[k].get("confirmed", 0))
        row["acc_" + k], row["enc"] = acc(o[k]["propose_day"], enc, fam)
    return row


def summ(rows, lam):
    out = {}
    for f in FAMILIES:
        fr = [r for r in rows if r["lam"] == lam and r["family"] == f]
        out[f] = {k: dict(proposals=sum(r[k]["pd"] is not None for r in fr),
                          evals=sum(r[k]["evals"] for r in fr) / len(fr),
                          discoveries=sum(r[k]["disc"] for r in fr), confirmed=sum(r[k]["conf"] for r in fr),
                          acc=sum(r["acc_" + k] for r in fr) / sum(r["enc"] for r in fr)) for k in KEYS}
        out[f]["v1_evals"] = sum(r["v1_evals"] for r in fr) / len(fr)
    return out


def macro(s, k): return sum(s[f][k]["acc"] for f in ACC) / 5


def z2(a, b, n=300):
    p = (a + b) / (2 * n)
    return 0.0 if p in (0, 1) else (a - b) / n / math.sqrt(p * (1 - p) * 2 / n)


def probe():
    n = np.full((DAYS, 16), 100, dtype=np.int64); k = np.full_like(n, 10); k[57:63, :] = 90; k[63:, :] = 50
    o = F18.run_family(n, k, np.ones(DAYS, dtype=bool))
    return {x: o[x] for x in ("final_state", "propose_day", "discoveries", "confirmed", "lapsed")}


def burst():
    out = {}
    for b in (5, 8):
        c = {k: 0 for k in KEYS}
        for seed in range(200):
            s = make_stream("NULL", 32, seed)
            rng = np.random.default_rng([20261015, 1, int(b * 10), seed])
            mean = np.zeros((DAYS, HOURS)); mean[70:91, :] = b * PROFILE[None, :]
            add = rng.poisson(mean)
            nR, kR = regionize(s["n"] + add, s["k"] + add, R)
            o = readers(nR, kR, N16.encounters(32, seed))
            for k in KEYS:
                c[k] += o[k]["propose_day"] is not None
        out[str(b)] = c
    return out


def main():
    if sha("PREREG.json") != FROZEN: raise SystemExit("PREREG changed")
    for f, h in PINNED.items():
        if sha(f) != h: raise SystemExit(f"{f} changed")
    with Pool(2) as p:
        rows = p.map(unit, [(f, l, s) for l in LAMS for f in FAMILIES for s in range(300)], chunksize=32)
    rows.sort(key=lambda r: (r["lam"], r["family"], r["seed"]))
    S = {l: summ(rows, l) for l in LAMS}
    pb, bu = probe(), burst()
    P = lambda l, f, k="fam": S[l][f][k]["proposals"]
    V = {
        "Z1_probe": (pb["final_state"] == "PROPOSED", pb),
        "Z2_genuine": (P(32, "GENUINE") >= 158 and P(128, "GENUINE") >= 240, {"32": P(32, "GENUINE"), "128": P(128, "GENUINE")}),
        "Z3_positional_confounds": (all(P(l, f) <= 5 for l in (32, 128) for f in ("COMMUTE", "DINNER")),
                                    {f"{f}@{l}": P(l, f) for l in (32, 128) for f in ("COMMUTE", "DINNER")}),
        "Z4_difficult_month": (P(32, "WINDOW") < 29 and P(128, "WINDOW") < 109, {"32": P(32, "WINDOW"), "128": P(128, "WINDOW")}),
        "Z5_null": (P(32, "NULL") <= 15 and P(128, "NULL") <= 15, {"32": P(32, "NULL"), "128": P(128, "NULL")}),
        "Z6_burst": (bu["8"]["fam"] <= 5, bu["8"]),
        "Z7_action": (macro(S[32], "fam") > 0.8221 and macro(S[128], "fam") > 0.8659, {"32": macro(S[32], "fam"), "128": macro(S[128], "fam")}),
        "Z8_information_limit": (all(abs(z2(P(l, "COLOCATED"), P(l, "GENUINE"))) < 3 for l in (32, 128)),
                                 {l: z2(P(l, "COLOCATED"), P(l, "GENUINE")) for l in (32, 128)}),
        "Z9_no_penalty": (P(32, "GENUINE") > P(32, "GENUINE", "lapse"), {"v18": P(32, "GENUINE"), "lapse_penalty": P(32, "GENUINE", "lapse")}),
    }
    V = {k: dict(passed=bool(p), detail=d) for k, (p, d) in V.items()}
    results = dict(prereg_sha256=FROZEN, verdicts=V, summary={str(l): S[l] for l in LAMS}, burst_descriptive=bu)
    receipt = hashlib.sha256(canonical(dict(results=results, rows=hashlib.sha256(canonical(rows).encode()).hexdigest())).encode()).hexdigest()
    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "results" / "results.json").write_text(json.dumps(results, indent=2, sort_keys=True))
    (ROOT / "results" / "RECEIPT.txt").write_text(receipt + "\n")
    for k, v in V.items():
        print(f"  {'PASS' if v['passed'] else 'FAIL'}  {k}: {json.dumps(v['detail'])[:170]}")
    print("\n proposals /300     v1.8  scout  lapse-1  v1.7  v1.6  v1.2")
    for l in LAMS:
        for f in FAMILIES:
            print(f"  λ={l:<3d} {f:10s} {P(l,f):4d} {P(l,f,'scout'):6d} {P(l,f,'lapse'):7d} {P(l,f,'v17'):5d} {P(l,f,'v16'):5d} {P(l,f,'v12'):5d}")
        print(f"  λ={l:<3d} macro    " + "  ".join(f"{k}:{macro(S[l],k):.4f}" for k in KEYS))
    for l in (32, 128):
        print(f"  λ={l} discoveries / confirmed:", {f: (S[l][f]["fam"]["discoveries"], S[l][f]["fam"]["confirmed"]) for f in FAMILIES})
    print("burst false /200:", json.dumps(bu))
    print("receipt:", receipt)


if __name__ == "__main__":
    main()
