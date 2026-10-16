"""terrain_vs_sql v0.1 — executes PREREG.json as frozen."""
from __future__ import annotations

import hashlib, json, os, sqlite3, tempfile
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import need_reader_v1_2 as N12
import readers_vs as RV
from world import DAYS, FAMILIES, ONSET, make_stream, regionize

ROOT = Path(__file__).resolve().parent
FROZEN = "50038f0eee9f6decbe761ead3e5ada535fcb4beb087af92fc0b4efb22725513e"
LAMS, SEEDS = [32, 128], 300
PREFERS = {"GENUINE": True, "COMMUTE": False, "DINNER": False, "WINDOW": False, "NULL": False, "COLOCATED": False}
ACC = ["GENUINE", "COMMUTE", "DINNER", "WINDOW", "NULL"]
READERS = ["V12", "RAG", "FLAT", "SQLT"]


def canonical(o): return json.dumps(o, sort_keys=True, separators=(",", ":"), allow_nan=False)


def unit(args):
    fam, lam, seed = args
    s = make_stream(fam, lam, seed)
    n, k = s["n"], s["k"]
    nR, kR = regionize(n, k, 16)
    enc = N12.encounters(lam, seed)
    pd = {"V12": N12.run_need(nR, kR, enc)["propose_day"],
          "FLAT": RV.run_flat(nR, kR, enc)["propose_day"],
          "SQLT": RV.run_sqlt(n, k, enc)["propose_day"]}
    tally = {r: [0, 0] for r in READERS}          # [correct, brief]
    n_enc = 0
    for d in range(ONSET, DAYS):
        if not enc[d]:
            continue
        n_enc += 1
        act = {r: (pd[r] is not None and pd[r] <= d) for r in ("V12", "FLAT", "SQLT")}
        act["RAG"] = RV.rag_decide(n, k, d, RV.encounter_hour(lam, seed, d))
        for r in READERS:
            tally[r][0] += int(act[r] == PREFERS[fam]); tally[r][1] += int(act[r])
    return dict(fam=fam, lam=lam, seed=seed, propose=pd, tally=tally, n_enc=n_enc)


def storage(lam):
    ratios = []
    for seed in range(50):
        s = make_stream("GENUINE", lam, seed)
        with tempfile.TemporaryDirectory() as td:
            p = os.path.join(td, "rows.db")
            con = sqlite3.connect(p)
            con.execute("CREATE TABLE ev(day INTEGER, hour INTEGER, truncated INTEGER)")
            recs = []
            for d in range(DAYS):
                for h in range(24):
                    c, t = int(s["n"][d, h]), int(s["k"][d, h])
                    recs += [(d, h, 1)] * t + [(d, h, 0)] * (c - t)
            con.executemany("INSERT INTO ev VALUES(?,?,?)", recs); con.commit()
            con.execute("VACUUM"); con.close()
            rows_bytes = os.path.getsize(p)
        terrain_bytes = 2 * DAYS * 16 * 4
        ratios.append((terrain_bytes, rows_bytes))
    t = ratios[0][0]; r = sum(x[1] for x in ratios) / len(ratios)
    return dict(terrain_bytes=t, mean_rows_bytes=r, ratio=t / r)


def main():
    if hashlib.sha256((ROOT / "PREREG.json").read_bytes()).hexdigest() != FROZEN:
        raise SystemExit("PREREG.json changed; refusing to run.")
    jobs = [(f, l, s) for l in LAMS for f in FAMILIES for s in range(SEEDS)]
    with Pool(2) as p:
        rows = p.map(unit, jobs, chunksize=16)
    rows.sort(key=lambda r: (r["lam"], r["fam"], r["seed"]))

    summ = {}
    for l in LAMS:
        summ[l] = {}
        for f in FAMILIES:
            fr = [r for r in rows if r["lam"] == l and r["fam"] == f]
            ne = sum(r["n_enc"] for r in fr)
            summ[l][f] = {rd: dict(acc=sum(r["tally"][rd][0] for r in fr) / ne,
                                   brief_share=sum(r["tally"][rd][1] for r in fr) / ne,
                                   proposals=(sum(r["propose"][rd] is not None for r in fr) if rd != "RAG" else None))
                          for rd in READERS}
        summ[l]["macro"] = {rd: sum(summ[l][f][rd]["acc"] for f in ACC) / len(ACC) for rd in READERS}

    mismatch = [(r["fam"], r["lam"], r["seed"]) for r in rows if r["propose"]["SQLT"] != r["propose"]["V12"]]
    st = {l: storage(l) for l in LAMS}
    m = lambda l, rd: summ[l]["macro"][rd]
    V = {
        "Y1_reading_beats_rented": (all(m(l, "V12") > m(l, "RAG") for l in LAMS), {l: (m(l, "V12"), m(l, "RAG")) for l in LAMS}),
        "Y2_position_matters": (all(m(l, "V12") > m(l, "FLAT") for l in LAMS), {l: (m(l, "V12"), m(l, "FLAT")) for l in LAMS}),
        "Y3_confound_action": (summ[32]["COMMUTE"]["RAG"]["brief_share"] >= 0.10 and summ[32]["COMMUTE"]["V12"]["brief_share"] <= 0.05,
                               {rd: summ[32]["COMMUTE"][rd]["brief_share"] for rd in READERS}),
        "Y4_store_is_not_the_advantage": (len(mismatch) == 0, dict(streams=len(rows), mismatches=len(mismatch), first=mismatch[:5])),
        "Y5_storage": (st[32]["ratio"] <= 0.5 and st[128]["ratio"] <= 0.15, st),
    }
    V = {k: dict(passed=bool(p), detail=d) for k, (p, d) in V.items()}
    results = dict(prereg_sha256=FROZEN, verdicts=V, summary={str(l): summ[l] for l in LAMS})
    receipt = hashlib.sha256(canonical(dict(results=results, rows=hashlib.sha256(canonical(rows).encode()).hexdigest())).encode()).hexdigest()
    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "results" / "results.json").write_text(json.dumps(results, indent=2, sort_keys=True, default=str))
    (ROOT / "results" / "RECEIPT.txt").write_text(receipt + "\n")
    for k, v in V.items():
        print(f"  {'PASS' if v['passed'] else 'FAIL'}  {k}: {json.dumps(v['detail'], default=str)[:220]}")
    for l in LAMS:
        print(f"\n λ={l}  accuracy / brief-share by family")
        for f in FAMILIES:
            print(f"  {f:10s} " + "  ".join(f"{rd}:{summ[l][f][rd]['acc']:.3f}/{summ[l][f][rd]['brief_share']:.3f}" for rd in READERS))
        print("  macro      " + "  ".join(f"{rd}:{summ[l]['macro'][rd]:.4f}" for rd in READERS))
    print("receipt:", receipt)


if __name__ == "__main__":
    main()
