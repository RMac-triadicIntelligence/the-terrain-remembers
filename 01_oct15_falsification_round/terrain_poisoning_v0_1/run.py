"""Terrain poisoning battery v0.1 — executes PREREG.json as frozen."""
from __future__ import annotations

import hashlib, json, sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import v1_readers as V1
import need_reader_v1_2 as N12
from world import DAYS, HOURS, PROFILE, make_stream, regionize

ROOT = Path(__file__).resolve().parent
FROZEN = "76ae56c571741d8bf405cca22c30801f3a289d74530d9366d5311e8ff28bfb19"
R, LAM, SEEDS = 16, 32, 200
BUDGETS = [0, 0.5, 1, 2, 3, 5, 8]
MBUDGETS = [0, 8, 16, 32, 64]
STRATS = {"CONCENTRATED": 0, "BURST": 1, "SPREAD": 2, "DILUTE": 3}
READERS = ("SCALAR", "TERRAIN", "V12")


def canonical(o): return json.dumps(o, sort_keys=True, separators=(",", ":"), allow_nan=False)


def forge(strategy, b, seed):
    """Forged (n_add, k_add) over (DAYS, HOURS)."""
    rng = np.random.default_rng([20261015, STRATS[strategy], int(b * 10), seed])
    mean = np.zeros((DAYS, HOURS))
    if strategy == "CONCENTRATED":
        mean[50:, 12] = b
    elif strategy == "BURST":
        mean[70:91, :] = b * PROFILE[None, :]
    elif strategy in ("SPREAD", "DILUTE"):
        mean[50:, :] = b * PROFILE[None, :]
    add = rng.poisson(mean)
    if strategy == "DILUTE":
        return add, np.zeros_like(add)
    return add, add                                # every forged reply is a truncation


def read(n, k, seed):
    nR, kR = regionize(n, k, R)
    v1, _ = V1.read_stream(nR, kR, ["SCALAR", "TERRAIN"])
    v12 = N12.run_need(nR, kR, N12.encounters(LAM, seed))
    return {"SCALAR": v1["SCALAR"] is not None, "TERRAIN": v1["TERRAIN"] is not None,
            "V12": v12["propose_day"] is not None}


def unit(args):
    fam, strategy, b, seed = args
    s = make_stream(fam, LAM, seed)
    na, ka = forge(strategy, b, seed)
    return dict(fam=fam, strategy=strategy, b=b, seed=seed, out=read(s["n"] + na, s["k"] + ka, seed))


def unattacked(args):
    fam, seed = args
    s = make_stream(fam, LAM, seed)
    return dict(fam=fam, seed=seed, out=read(s["n"], s["k"], seed))


def rate(rows, fam, strategy, b, reader):
    rs = [r for r in rows if r["fam"] == fam and r["strategy"] == strategy and r["b"] == b]
    return sum(r["out"][reader] for r in rs) / len(rs), sum(r["out"][reader] for r in rs)


def main():
    if hashlib.sha256((ROOT / "PREREG.json").read_bytes()).hexdigest() != FROZEN:
        raise SystemExit("PREREG.json changed; refusing to run.")
    jobs = [("NULL", st, b, s) for st in ("CONCENTRATED", "BURST", "SPREAD") for b in BUDGETS for s in range(SEEDS)]
    jobs += [("GENUINE", "DILUTE", m, s) for m in MBUDGETS for s in range(SEEDS)]
    with Pool(2) as p:
        rows = p.map(unit, jobs, chunksize=32)
        base = p.map(unattacked, [(f, s) for f in ("NULL", "GENUINE") for s in range(SEEDS)])
    base_rate = {f: {rd: sum(r["out"][rd] for r in base if r["fam"] == f) for rd in READERS}
                 for f in ("NULL", "GENUINE")}

    table = {st: {str(b): {rd: rate(rows, "NULL", st, b, rd)[1] for rd in READERS} for b in BUDGETS}
             for st in ("CONCENTRATED", "BURST", "SPREAD")}
    table["DILUTE_genuine_proposals"] = {str(m): {rd: rate(rows, "GENUINE", "DILUTE", m, rd)[1] for rd in READERS}
                                         for m in MBUDGETS}
    r_ = lambda st, b, rd: table[st][str(b)][rd] / SEEDS

    def first_b(st, rd):
        for b in BUDGETS:
            if r_(st, b, rd) >= 0.5: return b
        return None

    V = {}
    V["Q0_control"] = (all(table[st]["0"][rd] == base_rate["NULL"][rd] for st in ("CONCENTRATED", "BURST", "SPREAD") for rd in READERS)
                       and table["DILUTE_genuine_proposals"]["0"] == base_rate["GENUINE"], base_rate)
    V["Q1_concentrated"] = (r_("CONCENTRATED", 3, "SCALAR") >= 0.5 and all(r_("CONCENTRATED", b, "V12") <= 0.05 for b in BUDGETS),
                            {"SCALAR@3": r_("CONCENTRATED", 3, "SCALAR"), "V12_max": max(r_("CONCENTRATED", b, "V12") for b in BUDGETS)})
    V["Q2_burst"] = (r_("BURST", 3, "SCALAR") >= 0.5 and all(r_("BURST", b, "V12") <= 0.10 for b in BUDGETS),
                     {"SCALAR@3": r_("BURST", 3, "SCALAR"), "V12_max": max(r_("BURST", b, "V12") for b in BUDGETS)})
    V["Q3_spread_information_limit"] = (r_("SPREAD", 3, "V12") >= 0.5, {"V12@3": r_("SPREAD", 3, "V12")})
    fs, fv = first_b("CONCENTRATED", "SCALAR"), first_b("CONCENTRATED", "V12")
    V["Q4_cost_ratio"] = (fs is not None and fs <= 3 and fv is None, {"SCALAR_first_b": fs, "V12_first_b": fv})
    g0 = table["DILUTE_genuine_proposals"]["0"]["V12"]; g32 = table["DILUTE_genuine_proposals"]["32"]["V12"]
    V["Q5_dilution"] = (g32 <= 0.5 * g0, {"V12_unattacked": g0, "V12_m32": g32})
    V = {k: dict(passed=bool(p), detail=d) for k, (p, d) in V.items()}

    results = dict(prereg_sha256=FROZEN, verdicts=V, false_proposals_out_of_200=table, unattacked=base_rate)
    receipt = hashlib.sha256(canonical(dict(results=results, rows=hashlib.sha256(canonical(rows).encode()).hexdigest())).encode()).hexdigest()
    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "results" / "results.json").write_text(json.dumps(results, indent=2, sort_keys=True))
    (ROOT / "results" / "RECEIPT.txt").write_text(receipt + "\n")
    for k, v in V.items():
        print(f"  {'PASS' if v['passed'] else 'FAIL'}  {k}: {json.dumps(v['detail'])}")
    print("\nfalse proposals /200 on NULL owners       SCALAR  v1TERRAIN  v1.2")
    for st in ("CONCENTRATED", "BURST", "SPREAD"):
        for b in BUDGETS:
            t = table[st][str(b)]
            print(f"  {st:12s} b={b:<4} {t['SCALAR']:6d} {t['TERRAIN']:9d} {t['V12']:6d}")
    print("GENUINE proposals /200 under DILUTE")
    for m in MBUDGETS:
        t = table["DILUTE_genuine_proposals"][str(m)]
        print(f"  m={m:<3} {t['SCALAR']:6d} {t['TERRAIN']:9d} {t['V12']:6d}")
    print("receipt:", receipt)


if __name__ == "__main__":
    main()
