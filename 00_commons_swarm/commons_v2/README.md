# Commons swarm v2: v1's surprises as features

- **Preregistration:** `PREREG.json` (`d96565a6…2401`), frozen before code. Written after v1's results, on purpose.
- **Code:** `sim_v2.py` (`b5cbf3b5…2e73`), which imports the frozen v1 world. `run_all.py` (`17558a86…aa3c`).
- **Receipt:** `results.json` (`4c46ea9c…d5ce`). No calibration run was allowed in v2; constants were not tuned.

## What changed (each v1 surprise read as a feature)

| v1 surprise | v2 feature |
|---|---|
| Love as one copied map made kin herd | **Spacing:** love knows where kin are; keepers avoid cells crowded with kin |
| Closing love helped | **Weaning:** the young lean on the family map, adults on their own eyes; sharing never stops |
| Dwelling stood still 40 % of the time on empty ground | **Dwell where it matters:** dwell only where there's food; elsewhere, scout |
| No division of labor | **Roles:** one in three is a scout, heading for the least-known ground |
| A discovery couldn't enter the map without a witness | **Call for witness:** idle keepers go to confirm kin's newest pending find |
| LONE won through more households | **Budding:** families over 10 split into new households, same constitution |
| Grace only rescued the stuck | **Grace toward the frontier:** released toward kin's latest confirmed find |

## Results (mean of 20 seeds)

| Variant | Harvest | Per agent-step | Pop final / peak | Lineages alive | Lowest world stock |
|---|---|---|---|---|---|
| v1 FULL | 441 | 0.0259 | 20.9 / 38.5 | 2.8 | 42 % |
| **v2 FULL** | **792** | **0.0424** | 29.8 / 41.0 | **4.0** | 32 % |
| v2 LONE | 983 | 0.0360 | 38.4 / 70.6 | 4.0 | 19 % |
| NO_ROLES | **154** | 0.0214 | **0.25** / 32.7 | **0.25** | 52 % |
| NO_SPACING | 884 | 0.0420 | 35.6 / 40.5 | 4.0 | 27 % |
| NO_BUDDING | 780 | 0.0426 | 28.8 / 39.3 | 4.0 | 33 % |
| NO_WEANING | 784 | 0.0423 | 28.5 / 40.0 | 4.0 | 32 % |
| v2 NO_CONSTITUTION | 825 | 0.0440 | 29.8 / 40.7 | 4.0 | 32 % |
| v2 SELF_REPLICATING | 1026 | 0.0259 | 61.7 / **137** | 3.9 | **14 %** |

| Prediction | Verdict | Seeds in the predicted direction |
|---|---|---|
| D1 v2 beats v1 by ≥ 20 % | PASS (+80 %) | 20/20 |
| D2 family beats individual on total harvest and per agent | **FAIL** (wins per agent, loses on total) | per agent 20/20; total 0/20 |
| D3 spacing helps per agent | PASS (barely) | 13/20 |
| D4 scouts find moved patches | PASS | 20/20 |
| D5 budding helps | PASS (barely) | 8/20 |
| D6 without the constitution, the commons collapses | **FAIL** | 10/20 |
| D7 the replicator ends smaller | **FAIL** | 0/20 |
| D8 weaning helps late harvest | PASS (barely) | 11/20 |

## What it shows

1. **Roles carry the family.** v2 eats 80 % more than v1 and 64 % more per agent, every founding lineage
   survives in every seed, and time standing still halves (0.40 → 0.21). Remove the scouts and the commons dies
   (24 → 0.25 agents, 20/20 seeds): worse than v1. Scouting is what makes the rest work.
2. **Per agent, the family now beats the individual** (0.0424 vs 0.0360, 20/20 seeds). Individuals still eat
   more in total, because many "households of one" earn many more birth grants.
3. **The replicator wins on numbers and loses on everything else.** Self-authorized births peak at 137 and end at
   62, twice the commons. It harvests the most in total, but each agent eats 39 % less (0.0259 vs 0.0424), and it
   drains the world to 14 % of its food at the low point, against 32 % for the commons. More copies, each poorer,
   on a depleted world.
4. **The constitution stopped mattering here.** In v1, self-vouched marks collapsed the commons. In v2 the map
   still gets noisier (error 0.218 vs 0.180), but nothing breaks: roles and dwelling only where there's food make
   agents robust to bad marks. The constitution protected a herd, and a tasked family no longer is one.
5. **Spacing, budding and weaning are small effects** (8 to 13 of 20 seeds). Roles did the heavy lifting.

## Limits

One world type; 600 steps. A longer run might show whether the replicator's drained world finally breaks it.
Every variant's constants were set once, before running.
