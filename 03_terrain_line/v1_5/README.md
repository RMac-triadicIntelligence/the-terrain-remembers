# terrain falsifier v1.5: the record is knowledge, not a penalty

Soulshine · 2026-10-15 · built by Claude at Rusty McMurray's direction.
PREREG.json sha256 9c604ed2…debb, frozen 14:52:27Z, before any v1.5 code existed.

Direction (Rusty): "record of wrongs" is error tracking, not learning. There is no penalty for
past error, but the knowledge of it is kept, for future consideration and growth when needed.

Rule: a fresh full look at every need, and every reading kept in the question's record
forever. Only readings of the PRESENT terrain (taken within the look's own 42-day span) weigh
on the crossing. Older readings stay in the record and carry no weight. No new parameter.
Claude's operationalization, flagged.

## Result as frozen: 8 PASS, 2 FAIL

| proposals /300 | v1.2 | v1.4 | **v1.5** |
|---|---|---|---|
| GENUINE λ32 / λ128 | 173 / 299 | 95 / 296 | **150 / 300** |
| WINDOW false λ32 / λ128 | 28 / 78 | 12 / 25 | **12 / 25** |
| COMMUTE false λ32 / λ128 | 0 / 4 | 1 / 3 | 1 / 3 |
| Burst poison b=8, false /200 | 28 | 1 | **1** |
| Macro accuracy λ32 | **.852** | .825 | .837 |
| Macro accuracy λ128 | .884 | .883 | **.889** (best of any version) |

- V2 FAIL: GENUINE 150 at λ32 against the ≥173 prediction.
- V6 FAIL at λ32 (.837 against .852). It passes at λ128.
- V10 PASS: learning recovered from 95 to 150.

## What it means
Removing the penalty changed learning and nothing else. Every confound and adversary count is
IDENTICAL to v1.4: same 12/25 difficult-month false proposals, same 1/200 burst. The
resistance to re-rolling came entirely from the present readings agreeing. Weighing the past
against the present added nothing to safety and only cost growth. That is Rusty's principle,
measured: error tracking is not learning.

At high traffic v1.5 is the best version in the program on every axis. At λ32 it trades 23
genuine preferences (150 against 173) for 16 fewer false difficult months and 27 fewer
poisoned crossings out of 200.

## Still open
The record is kept but never consulted. "Knowledge of the error ... when needed" is not yet
implemented. That is where the remaining growth would come from, and its shape is Rusty's to
define. Low traffic (λ8) is still weak in every version.

## Bounds
Synthetic owners, one authored world, single author, no independent reproduction yet.
