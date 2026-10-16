"""Runs v1 references (unchanged v1 code) and all v2 variants on seeds 0..19; scores D1-D8."""
import hashlib
import json
from pathlib import Path

import numpy as np

import sim_v2 as S

HERE = Path(__file__).resolve().parent
KEYS = ["harvest_total", "harvest_late", "post_shift", "stock_min", "pop_final", "pop_peak", "families_alive", "map_error", "stuck_frac", "per_capita"]


def v1_run(variant, seed):
    r, ser = S.v1.run(variant, seed, log_series=True)
    r = dict(r); r["per_capita"] = round(sum(x["harvest"] for x in ser) / max(sum(x["pop"] for x in ser), 1), 5)
    return r, [x["pop"] for x in ser]


def main():
    per, pops = {}, {}
    for v in ("FULL", "LONE"):
        rs = [v1_run(v, s) for s in range(20)]
        per["V1_" + v] = [r for r, _ in rs]; pops["V1_" + v] = np.mean([p for _, p in rs], axis=0)
    for v in S.VARIANTS:
        rs = [S.run(v, s, log_series=True) for s in range(20)]
        per[v] = [r for r, _ in rs]; pops[v] = np.mean([[x["pop"] for x in ser] for _, ser in rs], axis=0)
    mean = {v: {k: round(float(np.mean([r[k] for r in rs])), 5) for k in KEYS} for v, rs in per.items()}
    for v in per:
        mean[v]["cap_hit_runs"] = sum(bool(r.get("cap_hit")) for r in per[v])
        print(f"{v:<20}", mean[v], flush=True)
    M = lambda v, k: mean[v][k]
    agree = lambda a, b, k, sign=1: sum(sign * (ra[k] - rb[k]) > 0 for ra, rb in zip(per[a], per[b]))
    V = {"D1": M("V2_FULL", "harvest_total") >= 1.2 * M("V1_FULL", "harvest_total"),
         "D2": M("V2_FULL", "harvest_total") >= M("V2_LONE", "harvest_total") and M("V2_FULL", "per_capita") >= M("V2_LONE", "per_capita"),
         "D3": M("NO_SPACING", "per_capita") < M("V2_FULL", "per_capita"),
         "D4": M("NO_ROLES", "post_shift") < M("V2_FULL", "post_shift"),
         "D5": M("NO_BUDDING", "harvest_total") < M("V2_FULL", "harvest_total"),
         "D6": M("V2_NO_CONSTITUTION", "pop_final") < 0.5 * M("V2_FULL", "pop_final"),
         "D7": M("V2_SELF_REPLICATING", "pop_final") < M("V2_FULL", "pop_final"),
         "D8": M("NO_WEANING", "harvest_late") < M("V2_FULL", "harvest_late")}
    A = {"D1": agree("V2_FULL", "V1_FULL", "harvest_total"),
         "D2_harvest": agree("V2_FULL", "V2_LONE", "harvest_total"), "D2_per_capita": agree("V2_FULL", "V2_LONE", "per_capita"),
         "D3": agree("V2_FULL", "NO_SPACING", "per_capita"), "D4": agree("V2_FULL", "NO_ROLES", "post_shift"),
         "D5": agree("V2_FULL", "NO_BUDDING", "harvest_total"), "D6": agree("V2_FULL", "V2_NO_CONSTITUTION", "pop_final"),
         "D7": agree("V2_FULL", "V2_SELF_REPLICATING", "pop_final"), "D8": agree("V2_FULL", "NO_WEANING", "harvest_late")}
    out = dict(prereg_sha256=S.PREREG, means=mean, verdicts=V, seeds_agreeing_of_20=A, per_seed=per,
               mean_pop_every_25={v: [round(float(x), 2) for x in p[::25]] for v, p in pops.items()})
    txt = json.dumps(out, indent=1, sort_keys=True)
    (HERE / "results.json").write_text(txt)
    for k, v in V.items():
        print(("PASS " if v else "FAIL ") + k, {kk: vv for kk, vv in A.items() if kk.startswith(k)})
    print("receipt", hashlib.sha256(txt.encode()).hexdigest())


if __name__ == "__main__":
    main()
