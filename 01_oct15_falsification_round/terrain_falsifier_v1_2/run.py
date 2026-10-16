"""
run.py — v1.2: executes PREREG.json as frozen on the same worlds and encounter
schedules as v1 and v1.1, runs both predecessors side by side, scores P0-P9 with
exact counts, runs the probe and mutation lane, writes a deterministic receipt.
"""
from __future__ import annotations

import hashlib, json, math, sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import v1_readers as V1
import need_reader_v1_1 as N11
import need_reader_v1_2 as N12
from world import DAYS, FAMILIES, ONSET, make_stream, regionize

ROOT = Path(__file__).resolve().parent
FROZEN = "3c1e46ee44fd7669834b68144a0557b34f2583d8168e386969796a78e3d8d48b"
PINNED = {"world.py": "7a15c82a9e7ab727a5374bd3f99dd9a3727496709650b445a4ac9a055329e956",
          "v1_readers.py": "addf121356d6643299494322d3ca3ee4fba83fe5be6099d473bef26a774d1f06"}
R = 16
PREFERS = {"GENUINE": True, "COMMUTE": False, "DINNER": False, "WINDOW": False,
           "NULL": False, "COLOCATED": False}
ACC = ["GENUINE", "COMMUTE", "DINNER", "WINDOW", "NULL"]
LAMS = [32, 128, 8]


def canonical(o): return json.dumps(o, sort_keys=True, separators=(",", ":"), allow_nan=False)
def sha(p): return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def checks():
    if sha("PREREG.json") != FROZEN: raise SystemExit("PREREG.json changed; refusing to run.")
    for f, h in PINNED.items():
        if sha(f) != h: raise SystemExit(f"{f} differs from v1; refusing to run.")


def accuracy(pd, enc, fam):
    c = n = 0
    for d in range(ONSET, DAYS):
        if enc[d]:
            c += int((pd is not None and pd <= d) == PREFERS[fam]); n += 1
    return c, n


def unit(args):
    fam, lam, seed = args
    s = make_stream(fam, lam, seed)
    nR, kR = regionize(s["n"], s["k"], R)
    enc = N12.encounters(lam, seed)
    a = N12.run_need(nR, kR, enc)
    b = N11.run_need(nR, kR, enc)
    v1, A = V1.read_stream(nR, kR, ["TERRAIN"])
    end = v1["TERRAIN"] if v1["TERRAIN"] is not None else DAYS - 1
    v1_looks = sum(1 for d in range(V1.FIRST_DAY, end + 1) if A[d] > V1.THRESH)
    row = dict(family=fam, lam=lam, seed=seed, v12=a, v11=b, v1=v1["TERRAIN"],
               v1_looks=v1_looks, v1_region_evals=v1_looks * 3 * R)
    for k, pd in (("v12", a["propose_day"]), ("v11", b["propose_day"]), ("v1", v1["TERRAIN"])):
        row["acc_" + k], row["enc"] = accuracy(pd, enc, fam)
    return row


def S(rows, lam):
    out = {}
    for f in FAMILIES:
        fr = [r for r in rows if r["lam"] == lam and r["family"] == f]
        d = {}
        for k in ("v12", "v11"):
            held = [r for r in fr if r[k]["first_look"] == "HELD"]
            d[k] = dict(proposals=sum(r[k]["propose_day"] is not None for r in fr),
                        held_first=len(held),
                        reopened_share=(sum(r[k]["reopens"] > 0 for r in held) / len(held)) if held else None,
                        looks=sum(r[k]["looks"] for r in fr) / len(fr),
                        evals=sum(r[k]["region_evals"] for r in fr) / len(fr),
                        acc=sum(r["acc_" + k] for r in fr) / sum(r["enc"] for r in fr))
        d["v1"] = dict(proposals=sum(r["v1"] is not None for r in fr),
                       looks=sum(r["v1_looks"] for r in fr) / len(fr),
                       evals=sum(r["v1_region_evals"] for r in fr) / len(fr),
                       acc=sum(r["acc_v1"] for r in fr) / sum(r["enc"] for r in fr))
        out[f] = d
    return out


def macro(s, k): return sum(s[f][k]["acc"] for f in ACC) / len(ACC)


def ztest(a, b, n=300):
    p = (a + b) / (2 * n)
    return 0.0 if p in (0, 1) else (a / n - b / n) / math.sqrt(p * (1 - p) * 2 / n)


def probe():
    n = np.full((DAYS, 16), 100, dtype=np.int64)
    k = np.full_like(n, 10); k[57:63, :] = 90; k[63:, :] = 50
    enc = np.ones(DAYS, dtype=bool)
    o11, o12 = N11.run_need(n, k, enc), N12.run_need(n, k, enc)
    strip = lambda o: {x: o[x] for x in ("final_state", "propose_day", "looks", "checks", "reopens")}
    return dict(v11=strip(o11), v12=strip(o12))


def mutation():
    out = {}
    for name, kw in (("M1_pressure_only", {"pressure_only": True}), ("M2_old_evidence", {"old_evidence": True})):
        res = {}
        for fam in ("COMMUTE", "GENUINE", "WINDOW"):
            held = reop = prop = 0
            for s in range(300):
                st = make_stream(fam, 32, s); nR, kR = regionize(st["n"], st["k"], R)
                o = N12.run_need(nR, kR, N12.encounters(32, s), **kw)
                if o["first_look"] == "HELD":
                    held += 1; reop += o["reopens"] > 0
                prop += o["propose_day"] is not None
            res[fam] = dict(held_first=held, reopened_share=reop / held if held else None, proposals=prop)
        out[name] = res
    out["M1_caught_by_P5"] = out["M1_pressure_only"]["COMMUTE"]["reopened_share"] > 0.05
    pr = nd = 0
    for s in range(60):
        st = make_stream("COMMUTE", 32, s); nR, kR = regionize(st["n"], st["k"], R)
        enc = N12.encounters(32, s)
        p = N12.run_need(nR, kR, enc, poll=True); b = N12.run_need(nR, kR, enc)
        pr += p["looks"] + p["checks"]; nd += b["looks"] + b["checks"]
    out["M3_polling_reads"] = pr / 60; out["M3_need_reads"] = nd / 60
    out["M3_at_least_3x"] = pr >= 3 * nd
    return out


def score(s32, s128, pb):
    P = lambda s, f, k="v12": s[f][k]["proposals"]
    V = {}
    V["P0_lockout_probe"] = (pb["v12"]["final_state"] == "PROPOSED", pb)
    V["P1_genuine_main"] = (P(s32, "GENUINE") >= 160, P(s32, "GENUINE"))
    V["P2_genuine_high"] = (P(s128, "GENUINE") >= 240, P(s128, "GENUINE"))
    V["P3_positional_confounds"] = (all(P(s, f) <= 15 for s in (s32, s128) for f in ("COMMUTE", "DINNER")),
                                    {f"{f}@{l}": P(s, f) for l, s in ((32, s32), (128, s128)) for f in ("COMMUTE", "DINNER")})
    V["P4_difficult_month"] = (P(s32, "WINDOW") <= 20 and P(s128, "WINDOW") <= 54,
                               {"32": P(s32, "WINDOW"), "128": P(s128, "WINDOW")})
    rs = {f"{f}@{l}": s[f]["v12"]["reopened_share"] for l, s in ((32, s32), (128, s128)) for f in ("COMMUTE", "DINNER")}
    V["P5_held_confounds_stay_held"] = (all(v is not None and v <= 0.05 for v in rs.values()), rs)
    m32, m128 = macro(s32, "v12"), macro(s128, "v12")
    V["P6_action"] = (m32 >= 0.8478 and m128 >= 0.8738, {"32": m32, "128": m128})
    V["P7_null"] = (P(s32, "NULL") <= 15 and P(s128, "NULL") <= 15, {"32": P(s32, "NULL"), "128": P(s128, "NULL")})
    z = {l: ztest(P(s, "COLOCATED"), P(s, "GENUINE")) for l, s in ((32, s32), (128, s128))}
    V["P8_information_limit"] = (all(abs(v) < 3 for v in z.values()), z)
    lk = sum(s32[f]["v12"]["looks"] for f in FAMILIES) / 6; lk1 = sum(s32[f]["v1"]["looks"] for f in FAMILIES) / 6
    ev = sum(s32[f]["v12"]["evals"] for f in FAMILIES) / 6; ev1 = sum(s32[f]["v1"]["evals"] for f in FAMILIES) / 6
    V["P9_cost"] = (lk <= 0.1 * lk1 and ev <= 0.25 * ev1, dict(looks=lk, v1_looks=lk1, evals=ev, v1_evals=ev1))
    return {k: dict(passed=bool(p), detail=d) for k, (p, d) in V.items()}


def main():
    checks()
    jobs = [(f, l, s) for l in LAMS for f in FAMILIES for s in range(300)]
    with Pool(2) as pool:
        rows = pool.map(unit, jobs, chunksize=32)
    rows.sort(key=lambda r: (r["lam"], r["family"], r["seed"]))
    summ = {l: S(rows, l) for l in LAMS}
    pb = probe()
    V = score(summ[32], summ[128], pb)
    mut = mutation()
    results = dict(prereg_sha256=FROZEN, streams=len(rows), verdicts=V,
                   summary={str(l): summ[l] for l in LAMS}, mutation=mut)
    payload = dict(results=results, rows_sha256=hashlib.sha256(canonical(rows).encode()).hexdigest())
    receipt = hashlib.sha256(canonical(payload).encode()).hexdigest()
    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "results" / "rows.json").write_text(canonical(rows))
    (ROOT / "results" / "results.json").write_text(json.dumps(results, indent=2, sort_keys=True))
    (ROOT / "results" / "RECEIPT.txt").write_text(receipt + "\n")
    for k, v in V.items():
        print(f"  {'PASS' if v['passed'] else 'FAIL'}  {k}: {json.dumps(v['detail'])[:150]}")
    print("\n proposals /300      v1.2   v1.1   v1")
    for l in LAMS:
        for f in FAMILIES:
            s = summ[l][f]
            print(f"  λ={l:<3d} {f:10s} {s['v12']['proposals']:5d} {s['v11']['proposals']:6d} {s['v1']['proposals']:5d}")
        print(f"  λ={l:<3d} macro acc  {macro(summ[l],'v12'):.4f} {macro(summ[l],'v11'):.4f} {macro(summ[l],'v1'):.4f}")
    print("\nmutation:", json.dumps(mut))
    print("receipt:", receipt)


if __name__ == "__main__":
    main()
