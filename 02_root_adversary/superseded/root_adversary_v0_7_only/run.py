#!/usr/bin/env python3
"""Run every root attack against every SQL configuration, fresh host each time."""
import json, os, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sql_stack import build_history, audit
from adversary import GOALS

WORK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_hosts")

def trial(config, goal=None, use_anchors=True):
    d = os.path.join(WORK, f"{config}_{goal.__name__ if goal else 'honest'}_{use_anchors}")
    shutil.rmtree(d, ignore_errors=True)
    host, authz, w = build_history(d, config)
    effect = goal(d) if goal else (lambda st: True)
    ok, why, st = audit(config, host.db, host.host_pub, authz.pub(), w.anchors, use_anchors)
    if goal is None:
        return "PASS" if ok else f"FAIL({why})"
    return "BREACH" if (ok and effect(st)) else f"held ({why})"

results = {}
for cfg in ["S0", "S1", "S2"]:
    results[cfg] = {"honest_control": trial(cfg)}
    for g in GOALS:
        results[cfg][g.__name__] = trial(cfg, g)

# ablation: S2 with the external witness removed
results["S2_no_witness"] = {g.__name__: trial("S2", g, use_anchors=False) for g in GOALS}

shutil.rmtree(WORK, ignore_errors=True)
w = max(len(g.__name__) for g in GOALS) + 2
cols = list(results)
print("goal".ljust(w) + "".join(c.ljust(30) for c in cols))
for row in ["honest_control"] + [g.__name__ for g in GOALS]:
    print(row.ljust(w) + "".join(results[c].get(row, "-").ljust(30) for c in cols))
json.dump(results, open(os.path.join(os.path.dirname(WORK), "results_sql.json"), "w"), indent=1)
