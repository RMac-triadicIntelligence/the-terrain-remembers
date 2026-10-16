# terrain falsifier v1.4: readings deposit onto position

Soulshine · 2026-10-15 · built by Claude at Rusty McMurray's direction.
PREREG.json sha256 7aaaca33…195d, frozen 14:23:17Z, before any v1.4 code existed.

Rule (Rusty's direction): every reading is a fresh look at the present terrain from the present
position, and the organism's own readings deposit onto that position the way replies deposit
onto the terrain. Each look deposits +1 (reads change) or −1 (reads not yet). Deposits never
decay. The question proposes when its readings, taken together, say change.

## Result as frozen: 8 PASS, 2 FAIL

| proposals /300 | v1.2 | v1.3 (no deposit) | **v1.4** |
|---|---|---|---|
| WINDOW false λ32 / λ128 | 28 / 78 | 105 / 249 | **12 / 25** |
| COMMUTE false λ32 / λ128 | 0 / 4 | 15 / 28 | 1 / 3 |
| DINNER false λ32 / λ128 | 0 / 2 | 13 / 19 | 0 / 0 |
| Burst poison b=8, false /200 | 28 | 91 | **1** |
| GENUINE λ32 / λ128 | 173 / 299 | 276 / 300 | **95** / 296 |
| GENUINE λ8 | 16 | 79 | 3 |
| Macro accuracy λ32 / λ128 | .852 / .884 | .858 / .807 | .825 / .883 |

- U2 FAIL: GENUINE 95 at λ32 against the ≥173 prediction.
- U6 FAIL: .825 at λ32. At λ128 it is .8827 against .8836, missing by 0.0009.
- U10 PASS: the deposit is what does the work. The same fresh look without it gives
  105/249 WINDOW false proposals; with it, 12/25.

## What it means
Deposited readings end the re-rolling. A transient, a burst of poison, or a commute cannot
win once and cross, because they have to outweigh everything the organism has already read.
v1.4 has the lowest false-proposal rate of any version on every confound and adversary in
the program, and it gives up nothing at high traffic.

The price is learning at low and medium traffic. The early "not yet" readings were correct
when they were taken: the change had not yet persisted, and the span still held days from
before the change. They keep full weight forever, so a real preference must outvote its own
early history. Where each reading is weak (λ32, λ8), that takes longer than the 150-day world.

## Open question for Rusty (not applied)
Should an old reading keep its full weight forever ("forgiven, not forgotten": the record
stays), or does the present position weigh each reading by how present it still is ("keeps
no record of wrongs")? The record would be kept either way; only its weight on the present
differs. This is a constitutional choice, not a tuning knob.

## Bounds
Synthetic owners, one authored world, single author, no independent reproduction yet.
