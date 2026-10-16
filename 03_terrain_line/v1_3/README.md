# terrain falsifier v1.3: a fresh look from the present position

Soulshine · 2026-10-15 · built by Claude at Rusty McMurray's direction.
PREREG.json sha256 f596d0e0…dd20, frozen 13:49:56Z, before any v1.3 code existed.

Direction (Rusty): every reading is a fresh look at the present terrain from the present
position. Position = the whole accumulated terrain (A) AND basin occupancy (B).
- A: the hold anchor is gone. Held questions get the full look at every need.
- B: Claude's operationalization, flagged. A held question also needs the change to have
  persisted through every complete block since it was first held.

## Result as frozen: 4 PASS, 5 FAIL. A real negative result.

| proposals /300 | v1.2 | v1.3 | v1.3 A only |
|---|---|---|---|
| GENUINE λ32 / λ128 | 173 / 299 | **270 / 300** | 276 / 300 |
| COMMUTE λ32 / λ128 | 0 / 4 | **15 / 28** | 15 / 28 |
| DINNER λ32 / λ128 | 0 / 2 | 13 / 19 | 13 / 19 |
| WINDOW λ32 / λ128 | 28 / 78 | **105 / 249** | 105 / 249 |
| Macro accuracy λ32 / λ128 | .852 / .884 | .855 / **.807** | .858 / .807 |
| Burst poison b=8, false /200 | 28 | **90** | 91 |

## What failed and why
1. Fresh looks at every need became repeated asking. A held commute question was looked at
   about 22 times. Each look is an independent pass/fail test, so 22 chances turn a rare
   false pass into a 5% false proposal. The organism keeps asking until a reading says yes.
   That is the persistence pattern from the October note, reproduced in the organism.
2. A running transient is read as real. At the moment of need, a difficult month that is
   still running looks like lasting change. A fresh look at that moment sees it, and
   WINDOW false proposals rise to 249/300 at high traffic. This was predicted in the
   PREREG. Only duration separates the two.
3. B as operationalized did nothing useful (T9 FAIL: 249 = 249). It vetoed only genuine
   and colocated streams, never a confound. "Persisted since first hold" is satisfied by
   any transient that is still running.

## What it points to (not applied)
The present position has to include the organism's OWN PAST READINGS. If each look is a
fresh verdict with no memory of earlier looks, re-reading is re-rolling. If every "not
yet" reading deposits onto the organism's position, the way replies deposit onto the
terrain, then the basin deepens with each held reading. A change has to outweigh what the
organism has already seen, not just win once. That is occupancy as accumulated
contemplation rather than a block test, and it needs Rusty's definition before it is built.

Real gain to keep: the fresh look learns far more at low and medium traffic (GENUINE 270
against 173 at λ32; 75 against 16 at λ8). The problem is false proposals, not learning.

## Bounds
Synthetic owners, one authored world, single author. v1.2 remains the best-performing
frozen version.
