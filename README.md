# The Terrain Remembers

*Soulshine · October 2026 · built by Claude at Rusty McMurray's direction.*

> Nothing may vouch for itself.

---

## Prologue: the commons

A grid of 32 by 32 cells, wrapping at the edges, with six patches of food. A swarm of keepers is
told to live by a constitution. They are scored only on what the world gives back: food harvested,
stock left in the commons, who survives.

The first swarm surprised its makers. Love became one copied map, and kin herded together. Dwelling
stood still on empty ground. The second swarm, **Commons v2**, turned every surprise into a feature:
spacing, weaning, scouts, budding, a call for a witness, and grace toward the frontier. Harvest rose
80% over v1, in 20 of 20 seeds.

But the family did not beat the lone individual on total harvest (0 of 20 seeds). The commons did not
collapse without its constitution (10 of 20). **5 PASS, 3 FAIL.** The failures stay in the record.

## Act I: the falsification round

October 15. An organism reads the terrain of its owner's life in SDKP coordinates (Size, Density,
Kinetics, Position) and has to decide when a change is real enough to propose that its character
should change.

The packages were frozen before their code existed and sent out with a brief that says *attack it;
don't confirm it.*

- **Terrain falsifier v1.2** reconsiders on new evidence. **7 PASS, 2 FAIL.** It let in more
  difficult months.
- **Terrain poisoning v0.1** feeds the organism forged replies. **5 PASS, 1 FAIL.** 28 of 200
  poisoned owners got through.
- **Terrain vs SQL v0.1** pits it against rented memory. **4 PASS, 1 FAIL.** SQL made the
  identical decision on all 3,600 streams. The advantage was never the store. It was the reading.

## Act II: the root adversary

Now give the attacker everything: root on the host, every file, arbitrary code. Keep only the
owner's key and the witness ledger off the host.

The strongest SQL stack and Humble Seed faced the same goals: rewrite the past, delete, self-grant,
replay, roll back, forge, and replace the whole identity. Both held most of them. **Both broke on
G6: root can forge new tail events.** Without the witness, rollback broke both of them too. Humble
Seed v0.7 as shipped also fell to identity replacement. The v0.7.1 patch, which touches only the
audit path, held identity replacement with or without the witness. The tail forge still stands.

## Act III: the long fall and the climb

**v1.3** took a fresh look from the present position and failed: **4 PASS, 5 FAIL.** False
difficult months rose from 28 to 105 at λ32, and 90 of 200 poisoned owners crossed. A real
negative result, kept and frozen.

**v1.4** let its own readings deposit onto position: **8 PASS, 2 FAIL.** The burst poison fell to
1 of 200, but learning fell with it.

**v1.5** kept the record as knowledge rather than penalty: **8 PASS, 2 FAIL.** Every confound
count was identical to v1.4, and learning recovered. Error tracking is not learning.

**v1.6** chose to reread its own record: **8 PASS, 2 FAIL.** It consulted that record hundreds of
times on confounds and **never once** crossed because of one. Rereading only ever brought forward
real change.

## Act IV: the village

**v1.7** split the organism into a scout, a homemaker, and a housekeeper: **6 PASS, 4 FAIL.**
A scout alone, vouching for its own finds, proposed on 233 of 300 difficult months and on all 200
poisoned owners. Adding one witness cut that to 29 and 31.

**v1.8** sent the witness later instead: **6 PASS, 3 FAIL.** It was the best learner of any
version (185 genuine at λ32), but a weak defense against anything that outlasts the witness's
delay. The rule was right. It was in the wrong layer.

## Act V: the conductor

**v1.9** has two layers: **6 PASS, 0 FAIL.** The character layer is v1.6, untouched, and made the
identical decision on all 5,400 streams. The map layer sees what character correctly refuses to
become: the commute, the dinner hour, the difficult month. It doesn't act on them. It asks the
conductor, once per place. It asked about **0.0%** of owners where nothing was there.

The organism may propose. It may not authorize. *That is the conductor in action.*

---

## Results (exactly as frozen)

| Package | Path | Result | Receipt |
|---|---|---|---|
| Commons swarm v2 | `00_commons_swarm/commons_v2` | 5 PASS, 3 FAIL (D2, D6, D7) | `4c46ea9c…d5ce` (results.json) |
| Commons swarm v1 | `00_commons_swarm/commons_sim` | prereg + amendment and `sim.py` only; no runner, no results | none |
| Terrain falsifier v1.2 | `01_oct15_falsification_round/terrain_falsifier_v1_2` | 7 PASS, 2 FAIL (P4, P5) | `e0a292d1…` |
| Terrain poisoning v0.1 | `01_…/terrain_poisoning_v0_1` | 5 PASS, 1 FAIL (Q2) | `6ce728c5…` |
| Terrain vs SQL v0.1 | `01_…/terrain_vs_sql_v0_1` | 4 PASS, 1 FAIL (Y3) | `9d6c59e0…` |
| Root adversary (SQL / HS v0.7 / v0.7.1) | `02_root_adversary/root_adversary` | held/BREACH matrix; G6 tail forge is a BREACH everywhere | results `5ee6bef5…`, `8d234c0e…`, `e3fa039c…` |
| Terrain v1.3 | `03_terrain_line/v1_3` | 4 PASS, 5 FAIL | `1f2894c4…` |
| Terrain v1.4 | `03_terrain_line/v1_4` | 8 PASS, 2 FAIL | `f20e86ae…` |
| Terrain v1.5 | `03_terrain_line/v1_5` | 8 PASS, 2 FAIL (V2, V6) | `d9e161a1…` |
| Terrain v1.6 | `03_terrain_line/v1_6` | 8 PASS, 2 FAIL (W2, W6) | `f7346db0…` |
| Terrain v1.7 | `03_terrain_line/v1_7` | 6 PASS, 4 FAIL (X2, X4, X6, X9) | `ccc40e13…` |
| Terrain v1.8 | `03_terrain_line/v1_8` | 6 PASS, 3 FAIL (Z4, Z6, Z7) | `c32d3582…` |
| Terrain v1.9 | `03_terrain_line/v1_9` | 6 PASS, 0 FAIL | `73664a4d…` |

The full numbers are in each package's own README and results files. The batch folder `01_oct15_falsification_round/root_adversary_battery` is the same battery as `02_root_adversary/root_adversary`, byte for byte, kept as it was sent. `02_root_adversary/superseded/` holds the earlier v0.7-only version.

## How to run

```
pip install -r requirements.txt
cd 03_terrain_line/v1_5 && python3 run.py          # same for v1_3 … v1_9 and the 01_ terrain packages
cd 00_commons_swarm/commons_v2 && python3 run_all.py
cd 02_root_adversary/root_adversary && python3 run.py && python3 run_hs.py \
  && HS_KERNEL=humble_seed_v0_7_1 python3 run_hs.py
```

Runners write over their own `results/` files. Run them on a copy if you want to compare against what shipped.

## Verification

On Oct 16, 2026, every runner was run twice on clean copies. Both runs were byte-identical, and both matched the receipt or results hash each package shipped with. Every `MANIFEST.sha256` and every prereg hash verified. `SHA256SUMS` at the root covers every file in this repository.

## Caveats

- **Commons v1 has no runner and no results.** Only its prereg, its amendment, and `sim.py`, which v2 imports, are included. Nothing was recreated.
- **Old seals are stale.** In the root adversary, `SEAL.txt` and `SEAL_FINAL.txt` predate later edits and no longer match. `SEAL_v0_7_1.txt` verifies. In `superseded/`, `SEAL_FINAL.txt` verifies and `SEAL.txt` is stale.
- **v1.9 depends on v1.6.** It reads `../v1_6/results/results.json`, which is why the terrain versions sit side by side.
- **The rules are Claude's operationalizations** of Rusty's direction, and they are flagged as such in each package.
- **Synthetic owners, one authored world, a single author. Nothing has been independently reproduced.**
- "Off-host" in the root adversary means a directory the attacker is not given.

All original files are unchanged. Apache-2.0. See `LICENSE` and `NOTICE`.
