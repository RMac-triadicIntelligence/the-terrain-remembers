# terrain falsifier v1.7: scout, homemaker, housekeeper

Soulshine · 2026-10-15 · built by Claude at Rusty McMurray's direction.
PREREG.json sha256 93258649…f8fb4, frozen 15:29:40Z, before any v1.7 code existed.

Direction (Rusty): the scout / home-keeping model on the choice decision. Some members scout,
homemakers confirm, a housekeeper keeps the record. From the village: nothing goes on the
family map without a witness.

Roles (Claude's operationalization, flagged): the scout reads only the frontier (newest 14
days). The homemaker confirms a scout's up-regions on the established ground the scout did
not read (the prior four weeks). The housekeeper keeps the family record (confirmed +1,
unconfirmed −1, present span weighs). Ablation: the scout alone, vouching for its own finds.

## Result as frozen: 6 PASS, 4 FAIL

| proposals /300 | scout alone | **family v1.7** | v1.6 (single organism) | v1.2 |
|---|---|---|---|---|
| WINDOW false λ32 / λ128 | 233 / 297 | 29 / 109 | **12 / 25** | 28 / 78 |
| COMMUTE false λ32 / λ128 | 38 / 35 | 0 / 4 | 1 / 3 | 0 / 4 |
| Burst poison b=8, false /200 | 200 | 31 | **1** | 28 |
| GENUINE λ32 / λ128 | 292 / 300 | 109 / 298 | **158 / 300** | 173 / 299 |
| Macro accuracy λ32 / λ128 | .791 / .784 | .822 / .866 | .839 / **.889** | .852 / .884 |

FAIL: X2 (GENUINE 109 at λ32), X4 (WINDOW 29 / 109), X6 (accuracy), X9 (burst 31).
PASS: X10. The witness is load-bearing.

## Two findings
1. **Nothing vouches for itself, measured.** The same scout with the same eyes, allowed to
   vouch for its own finds, proposes on 233 of 300 difficult months and on every one of 200
   poisoned owners. Adding one witness reading different ground cuts that to 29 and 31. The
   village rule is the single largest safety effect in this program after position itself.
2. **This division of labor is weaker than one organism reading its whole span.** The
   homemaker's established ground overlaps a 30-day transient or a 21-day burst, so the
   witness confirms what is really there for a while. v1.6's single organism requires the
   change in all three blocks plus agreement among its present readings, and stays the
   best frozen version.

## Why scouts did not pay off here
In the village, scouts earned 80% more food because there was unknown ground: no member could
see the whole landscape. In this world every member reads every region at every look. There
is no unknown ground, so a scout has nothing to find that the organism does not already see.
The scout's value needs a world where reading is limited: each look can afford only part of
the terrain. That is also Rusty's edge / legacy-hardware goal. That is the world to build for
scouts.

## Bounds
Synthetic owners, one authored world, single author. Role definitions are Claude's.
