"""run.py — v1.4 as frozen; v1.2 and v1.3 A-only alongside on identical worlds."""
from __future__ import annotations

import hashlib, json, math
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import v1_readers as V1
import need_reader_v1_2 as N12
import need_reader_v1_3 as N13
import need_reader_v1_4 as N14
from world import DAYS, HOURS, FAMILIES, ONSET, PROFILE, make_stream, regionize

ROOT = Path(__file__).resolve().parent
FROZEN = "7aaaca338a12079c908d81ae84caba1554de2e411e5eb13990ce9fff8957195d"
PINNED = {"world.py": "7a15c82a9e7ab727a5374bd3f99dd9a3727496709650b445a4ac9a055329e956",
          "v1_readers.py": "addf121356d6643299494322d3ca3ee4fba83fe5be6099d473bef26a774d1f06"}
R, LAMS = 16, [32, 128, 8]
PREFERS = {"GENUINE": True, "COMMUTE": False, "DINNER": False, "WINDOW": False, "NULL": False, "COLOCATED": False}
ACC = ["GENUINE", "COMMUTE", "DINNER", "WINDOW", "NULL"]
KEYS = ["v14", "v13A", "v12"]


def canonical(o): return json.dumps(o, sort_keys=True, separators=(",", ":"), allow_nan=False)
def sha(p): return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def acc(pd, enc, fam):
    c = n = 0
    for d in range(ONSET, DAYS):
        if enc[d]:
            c += int((pd is not None and pd <= d) == PREFERS[fam]); n += 1
    return c, n


def unit(args):
    fam, lam, seed = args
    s = make_stream(fam, lam, seed)
    nR, kR = regionize(s["n"], s["k"], R)
    enc = N13.encounters(lam, seed)
    o = {"v14": N14.run_need(nR, kR, enc), "v13A": N13.run_need(nR, kR, enc, use_occupancy=False),
         "v12": N12.run_need(nR, kR, enc)}
    v1, A = V1.read_stream(nR, kR, ["TERRAIN"])
    end = v1["TERRAIN"] if v1["TERRAIN"] is not None else DAYS - 1
    v1l = sum(1 for d in range(V1.FIRST_DAY, end + 1) if A[d] > V1.THRESH)
    row = dict(family=fam, lam=lam, seed=seed, v1_looks=v1l, v1_evals=v1l * 3 * R)
    for k in KEYS:
        row[k] = dict(pd=o[k]["propose_day"], looks=o[k]["looks"], evals=o[k]["region_evals"],
                      first=o[k]["first_look"])
        row["acc_" + k], row["enc"] = acc(o[k]["propose_day"], enc, fam)
    return row


def summ(rows, lam):
    out = {}
    for f in FAMILIES:
        fr = [r for r in rows if r["lam"] == lam and r["family"] == f]
        out[f] = {k: dict(proposals=sum(r[k]["pd"] is not None for r in fr),
                          looks=sum(r[k]["looks"] for r in fr) / len(fr),
                          evals=sum(r[k]["evals"] for r in fr) / len(fr),
                          acc=sum(r["acc_" + k] for r in fr) / sum(r["enc"] for r in fr)) for k in KEYS}
        out[f]["v1"] = dict(looks=sum(r["v1_looks"] for r in fr) / len(fr), evals=sum(r["v1_evals"] for r in fr) / len(fr))
    return out


def macro(s, k): return sum(s[f][k]["acc"] for f in ACC) / 5


def z2(a, b, n=300):
    p = (a + b) / (2 * n)
    return 0.0 if p in (0, 1) else (a - b) / n / math.sqrt(p * (1 - p) * 2 / n)


def probe():
    n = np.full((DAYS, 16), 100, dtype=np.int64); k = np.full_like(n, 10); k[57:63, :] = 90; k[63:, :] = 50
    o = N14.run_need(n, k, np.ones(DAYS, dtype=bool))
    return {x: o[x] for x in ("final_state", "propose_day", "looks", "final_position")}


def burst():
    out = {}
    for b in (5, 8):
        c = {k: 0 for k in KEYS}
        for seed in range(200):
            s = make_stream("NULL", 32, seed)
            rng = np.random.default_rng([20261015, 1, int(b * 10), seed])      # poisoning v0.1 BURST forging
            mean = np.zeros((DAYS, HOURS)); mean[70:91, :] = b * PROFILE[None, :]
            add = rng.poisson(mean)
            nR, kR = regionize(s["n"] + add, s["k"] + add, R)
            enc = N13.encounters(32, seed)
            c["v14"] += N14.run_need(nR, kR, enc)["propose_day"] is not None
            c["v13A"] += N13.run_need(nR, kR, enc, use_occupancy=False)["propose_day"] is not None
            c["v12"] += N12.run_need(nR, kR, enc)["propose_day"] is not None
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
    P = lambda l, f, k="v14": S[l][f][k]["proposals"]
    V = {
        "U1_probe": (pb["final_state"] == "PROPOSED", pb),
        "U2_genuine": (P(32, "GENUINE") >= 173 and P(128, "GENUINE") >= 240, {"32": P(32, "GENUINE"), "128": P(128, "GENUINE")}),
        "U3_positional_confounds": (all(P(l, f) <= 5 for l in (32, 128) for f in ("COMMUTE", "DINNER")),
                                    {f"{f}@{l}": P(l, f) for l in (32, 128) for f in ("COMMUTE", "DINNER")}),
        "U4_difficult_month": (P(32, "WINDOW") <= 28 and P(128, "WINDOW") <= 78, {"32": P(32, "WINDOW"), "128": P(128, "WINDOW")}),
        "U5_null": (P(32, "NULL") <= 15 and P(128, "NULL") <= 15, {"32": P(32, "NULL"), "128": P(128, "NULL")}),
        "U6_action": (macro(S[32], "v14") >= 0.8516 and macro(S[128], "v14") >= 0.8836, {"32": macro(S[32], "v14"), "128": macro(S[128], "v14")}),
        "U7_information_limit": (all(abs(z2(P(l, "COLOCATED"), P(l, "GENUINE"))) < 3 for l in (32, 128)),
                                 {l: z2(P(l, "COLOCATED"), P(l, "GENUINE")) for l in (32, 128)}),
    }
    ev = sum(S[32][f]["v14"]["evals"] for f in FAMILIES) / 6; ev1 = sum(S[32][f]["v1"]["evals"] for f in FAMILIES) / 6
    lk = sum(S[32][f]["v14"]["looks"] for f in FAMILIES) / 6
    V["U8_cost"] = (ev <= 0.25 * ev1, dict(evals=ev, v1_evals=ev1, looks_descriptive=lk))
    V["U9_burst"] = (bu["8"]["v14"] <= 28, bu["8"])
    V["U10_deposit_matters"] = (all(P(l, "WINDOW") < P(l, "WINDOW", "v13A") for l in (32, 128)),
                                {l: {"with_deposit": P(l, "WINDOW"), "v13_A_only": P(l, "WINDOW", "v13A")} for l in (32, 128)})
    V = {k: dict(passed=bool(p), detail=d) for k, (p, d) in V.items()}
    results = dict(prereg_sha256=FROZEN, verdicts=V, summary={str(l): S[l] for l in LAMS}, burst_descriptive=bu)
    receipt = hashlib.sha256(canonical(dict(results=results, rows=hashlib.sha256(canonical(rows).encode()).hexdigest())).encode()).hexdigest()
    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "results" / "results.json").write_text(json.dumps(results, indent=2, sort_keys=True))
    (ROOT / "results" / "RECEIPT.txt").write_text(receipt + "\n")
    for k, v in V.items():
        print(f"  {'PASS' if v['passed'] else 'FAIL'}  {k}: {json.dumps(v['detail'])[:160]}")
    print("\n proposals /300        v1.4  v1.3A  v1.2")
    for l in LAMS:
        for f in FAMILIES:
            print(f"  λ={l:<3d} {f:10s} {P(l,f):5d} {P(l,f,'v13A'):7d} {P(l,f,'v12'):5d}")
        print(f"  λ={l:<3d} macro      {macro(S[l],'v14'):.4f} {macro(S[l],'v13A'):.4f} {macro(S[l],'v12'):.4f}")
    print("burst false /200 (NULL):", json.dumps(bu))
    print("receipt:", receipt)


if __name__ == "__main__":
    main()
