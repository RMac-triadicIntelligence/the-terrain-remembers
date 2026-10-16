# terrain falsifier v1.8: the witness comes later, unconfirmed finds lapse

Soulshine · 2026-10-15 · built by Claude at Rusty McMurray's direction, modelled on
commons_swarm_v2. PREREG.json sha256 155419c6…b03d, frozen 15:34:33Z, before any v1.8 code.

Two corrections to v1.7: (1) the homemaker no longer looks backward at older ground. A
different member arrives LATER (one block after the find) and reads the SAME regions on
new data. (2) An unconfirmed find lapses and deposits nothing; v1.7 deposited −1.

## Result as frozen: 6 PASS, 3 FAIL

| proposals /300 | v1.2 | v1.6 | v1.7 | **v1.8** | v1.8 with lapse −1 | scout alone |
|---|---|---|---|---|---|---|
| GENUINE λ32 | 173 | 158 | 109 | **185** (best ever) | 163 | 292 |
| GENUINE λ128 | 299 | 300 | 298 | 299 | 297 | 300 |
| COMMUTE / DINNER λ32 | 0/0 | 1/0 | 0/1 | 0/1 | 0/1 | 38/47 |
| WINDOW λ32 / λ128 | 28/78 | **12/25** | 29/109 | 58/268 | 58/268 | 233/297 |
| Burst b=8 /200 | 28 | **1** | 31 | 153 | 153 | 200 |
| Macro accuracy λ32 / λ128 | .852/.884 | .839/**.889** | .822/.866 | .842/.811 | .832/.810 | .791/.784 |

FAIL: Z4 (difficult month), Z6 (burst), Z7 (accuracy at λ128).
PASS: Z9. A penalty for lapsed finds cost 22 genuine preferences and bought no safety at all
(WINDOW and burst identical). That is the third time today (v1.5, v1.6, v1.8) that the record
of wrongs added nothing to safety.

## What it shows
1. A forward witness is the best learner in the program: 185 genuine at λ32, with commute
   and dinner still clean. A different member, later, the same place, its own eyes, finds
   real change fast.
2. It is a weak defense against anything that lasts longer than the witness delay. The
   witness arrives 14 days after the find. A 21-day burst and a 30-day difficult month are
   both still there when it arrives, so it honestly confirms them. Z10's descriptive
   expectation was right about the month and wrong about the burst (21 days > 14).
3. This is not a flaw in the village rule. It is the wrong LAYER. In the village a confirmed
   find goes on the family MAP: it tells members where to eat NOW, and a month of food is
   worth eating. Here the same rule was used to cross a CHARACTER question, where a month
   should not change who the organism is.

## The architecture this points to (not built)
Two layers:
- **Map (action now):** scouts, a later witness, lapse without penalty. Fast, local,
  reversible: what to do in these places while it holds.
- **Character (who it is):** v1.6's whole-span reading, with present agreement and
  rereading, then the owner's signature. Slow, global, constitutional.
Scoring the map layer needs a decision the world does not yet encode: is being brief during
a commute, or during a difficult month, a correct ACTION even though it is not character?
(ChatGPT's open point 5.)

## Bounds
Synthetic owners, one authored world, single author, roles operationalized by Claude.
