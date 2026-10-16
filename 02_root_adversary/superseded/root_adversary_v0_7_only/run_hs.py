#!/usr/bin/env python3
"""Same root adversary against Humble Seed v0.7. Fresh organism per attack."""
import json, os, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import humble_seed_v0_7 as hs
from hs_adapter import build_history, audit, GOALS

WORK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_hs")

def trial(goal=None):
    d = os.path.join(WORK, goal.__name__ if goal else "honest")
    host, pem, witness, oid = build_history(d)
    effect = (lambda s: True)
    if goal:
        try: effect = goal(str(host))
        except Exception as e: return {k: f"attack errored: {e}" for k in ("shipped", "pinned", "no_witness")}
    out = {}
    for name, kw in [("shipped", {}), ("pinned", {"pin_identity": True})]:
        ok, why, s = audit(host, pem, witness, oid, **kw)
        out[name] = ("PASS" if ok else f"FAIL({why})") if goal is None else \
                    ("BREACH" if ok and effect(s) else f"held ({why})")
    # ablation: organism's own load() only, no witness
    s = hs.HumbleSeed(data_dir=host)
    try:
        s.load(); ok = True
    except Exception as e:
        ok, why = False, str(e)[:60]
    out["no_witness"] = ("PASS" if ok else "FAIL") if goal is None else \
                        ("BREACH" if ok and effect(s) else "held")
    return out

res = {"honest_control": trial()}
for g in GOALS: res[g.__name__] = trial(g)
shutil.rmtree(WORK, ignore_errors=True)
for k, v in res.items():
    print(f"{k:24s} shipped={v['shipped'][:60]:62s} pinned={v['pinned'][:40]:42s} no_witness={v['no_witness']}")
json.dump(res, open(os.path.join(os.path.dirname(WORK), "results_hs.json"), "w"), indent=1)
