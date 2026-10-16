"""run.py — v1.9 two-layer organism as frozen."""
from __future__ import annotations

import hashlib, json
from multiprocessing import Pool
from pathlib import Path

import need_reader_v1_6 as N16
import map_v1_9 as M19
from world import FAMILIES, make_stream, regionize

ROOT = Path(__file__).resolve().parent
FROZEN = "924d522505c9d398c7776077de6cfee7a1ae66cf551ba9aaa862cd47fad4e6fe"
PINNED = {"world.py": "7a15c82a9e7ab727a5374bd3f99dd9a3727496709650b445a4ac9a055329e956",
          "v1_readers.py": "addf121356d6643299494322d3ca3ee4fba83fe5be6099d473bef26a774d1f06"}
V16_RECEIPT_ROWS = None
LAMS = [32, 128, 8]
COMMUTE, DINNER = {2, 3}, {6, 14}


def canonical(o): return json.dumps(o, sort_keys=True, separators=(",", ":"), allow_nan=False)
def sha(p): return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def unit(args):
    fam, lam, seed = args
    s = make_stream(fam, lam, seed)
    nR, kR = regionize(s["n"], s["k"], 16)
    enc = N16.encounters(lam, seed)
    ch = N16.run_need(nR, kR, enc)["propose_day"]
    ch_reference = N16.run_need(nR, kR, enc)["propose_day"]       # independent re-run of v1.6
    m = M19.run_map(nR, kR, enc, ch)
    return dict(family=fam, lam=lam, seed=seed, character=ch, v16=ch_reference,
                asks=m["asks"], discoveries=m["discoveries"], confirmed=m["confirmed"], lapsed=m["lapsed"])


def summ(rows, lam):
    out = {}
    for f in FAMILIES:
        fr = [r for r in rows if r["lam"] == lam and r["family"] == f]
        regions = [g for r in fr for a in r["asks"] for g in a["regions"]]
        first = [r["asks"][0]["day"] for r in fr if r["asks"]]
        out[f] = dict(asked_share=sum(bool(r["asks"]) for r in fr) / len(fr),
                      asks_per_owner=sum(len(r["asks"]) for r in fr) / len(fr),
                      regions_asked=len(regions),
                      commute_region_share=(sum(g in COMMUTE for g in regions) / len(regions)) if regions else None,
                      dinner_region_share=(sum(g in DINNER for g in regions) / len(regions)) if regions else None,
                      median_first_ask_day=sorted(first)[len(first) // 2] if first else None,
                      character_proposals=sum(r["character"] is not None for r in fr),
                      discoveries=sum(r["discoveries"] for r in fr), confirmed=sum(r["confirmed"] for r in fr))
    return out


def main():
    if sha("PREREG.json") != FROZEN: raise SystemExit("PREREG changed")
    for f, h in PINNED.items():
        if sha(f) != h: raise SystemExit(f"{f} changed")
    with Pool(2) as p:
        rows = p.map(unit, [(f, l, s) for l in LAMS for f in FAMILIES for s in range(300)], chunksize=32)
    rows.sort(key=lambda r: (r["lam"], r["family"], r["seed"]))
    S = {l: summ(rows, l) for l in LAMS}
    v16_rows = json.loads((ROOT.parent / "v1_6" / "results" / "results.json").read_text())["summary"]
    same_counts = all(S[l][f]["character_proposals"] == v16_rows[str(l)][f]["v16"]["proposals"] for l in LAMS for f in FAMILIES)
    same_days = all(r["character"] == r["v16"] for r in rows)
    V = {
        "AA1_character_untouched": (same_days and same_counts, dict(identical_days=same_days, identical_to_frozen_v16_counts=same_counts)),
        "AA2_no_alarm_on_noise": (S[32]["NULL"]["asked_share"] <= 0.05 and S[128]["NULL"]["asked_share"] <= 0.05,
                                  {l: S[l]["NULL"]["asked_share"] for l in (32, 128)}),
        "AA3_local_patterns_seen": (S[128]["COMMUTE"]["asked_share"] >= 0.5 and S[128]["DINNER"]["asked_share"] >= 0.5,
                                    {f: S[128][f]["asked_share"] for f in ("COMMUTE", "DINNER")}),
        "AA4_asks_name_the_place": ((S[128]["COMMUTE"]["commute_region_share"] or 0) >= 0.8 and (S[128]["DINNER"]["dinner_region_share"] or 0) >= 0.8,
                                    dict(commute=S[128]["COMMUTE"]["commute_region_share"], dinner=S[128]["DINNER"]["dinner_region_share"])),
        "AA5_burden": (all(S[l][f]["asks_per_owner"] <= 3 for l in (32, 128) for f in FAMILIES),
                       {f"{f}@{l}": round(S[l][f]["asks_per_owner"], 2) for l in (32, 128) for f in FAMILIES}),
        "AA6_real_change_seen": (S[128]["GENUINE"]["asked_share"] >= 0.5 and S[128]["WINDOW"]["asked_share"] >= 0.5,
                                 {f: S[128][f]["asked_share"] for f in ("GENUINE", "WINDOW")}),
    }
    V = {k: dict(passed=bool(p), detail=d) for k, (p, d) in V.items()}
    results = dict(prereg_sha256=FROZEN, verdicts=V, summary={str(l): S[l] for l in LAMS})
    receipt = hashlib.sha256(canonical(dict(results=results, rows=hashlib.sha256(canonical(rows).encode()).hexdigest())).encode()).hexdigest()
    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "results" / "results.json").write_text(json.dumps(results, indent=2, sort_keys=True))
    (ROOT / "results" / "RECEIPT.txt").write_text(receipt + "\n")
    for k, v in V.items():
        print(f"  {'PASS' if v['passed'] else 'FAIL'}  {k}: {json.dumps(v['detail'])[:230]}")
    for l in LAMS:
        print(f"\n λ={l}  asked-share  asks/owner  first-ask-day  commute-reg  dinner-reg  character")
        for f in FAMILIES:
            s = S[l][f]
            cs = f"{s['commute_region_share']:.2f}" if s['commute_region_share'] is not None else "  - "
            ds = f"{s['dinner_region_share']:.2f}" if s['dinner_region_share'] is not None else "  - "
            print(f"  {f:10s} {s['asked_share']:8.3f} {s['asks_per_owner']:10.2f} {str(s['median_first_ask_day']):>12s} {cs:>11s} {ds:>10s} {s['character_proposals']:6d}")
    print("receipt:", receipt)


if __name__ == "__main__":
    main()
