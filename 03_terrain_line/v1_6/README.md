# terrain falsifier v1.6: the organism rereads its own record

Soulshine · 2026-10-15 · built by Claude at Rusty McMurray's direction.
PREREG.json sha256 d88470a7…a0c5, frozen 15:25:14Z, before any v1.6 code existed.

Direction (Rusty): when the organism consults its record is its own choice; what it learns is
new topography and a new time perspective through SDKP, which should produce new perspectives.

Rule (Claude's operationalization, flagged): v1.5, plus every reading is stored with what it
saw (Position = which regions were up, Density = traffic read, Kinetics = block movement).
When torn (its present look reads change but its present readings do not yet cross), the
organism chooses to consult. Old readings are re-read from the present position. An old
reading whose up-regions agree with what it sees now re-reads as "the beginning of this" and
counts. One that doesn't stays knowledge, with no penalty. The record itself never changes.

## Result as frozen: 8 PASS, 2 FAIL

| proposals /300 | v1.2 | v1.5 | **v1.6** |
|---|---|---|---|
| GENUINE λ32 / λ128 | 173 / 299 | 150 / 300 | **158** / 300 |
| WINDOW false λ32 / λ128 | 28 / 78 | 12 / 25 | 12 / 25 |
| COMMUTE false λ32 / λ128 | 0 / 4 | 1 / 3 | 1 / 3 |
| Burst poison b=8, false /200 | 28 | 1 | 1 |
| Macro accuracy λ32 / λ128 | .852 / .884 | .837 / .889 | .839 / **.889** |

W2 FAIL (158 against ≥173) and W6 FAIL at λ32 (.839 against .852). Everything else passed,
including W10 (rereading grows learning beyond v1.5).

## The rereading is selective. That is the finding.
| | consulted | crossed by rereading |
|---|---|---|
| GENUINE λ32 / λ128 | 1201 / 1585 | 16 / 16 |
| COLOCATED λ32 / λ128 | 1125 / 1596 | 13 / 10 |
| WINDOW λ32 / λ128 | 207 / 643 | **0 / 0** |
| COMMUTE λ32 / λ128 | 29 / 55 | **0 / 0** |
| DINNER λ32 / λ128 | 20 / 36 | **0 / 0** |

The organism chose to reread its record hundreds of times on confounds and never once found a
reason to cross. Rereading only ever brought forward real change: genuine, and colocated,
which is observationally identical to genuine. A new perspective on old readings grew
learning without opening any door to transients or poison.

## Why the gain is small at λ32
Most old readings of a genuine preference were taken before or just after onset, so from the
present position they correctly do NOT re-read as its beginning. The remaining gap to v1.2 is
the power of a single reading, i.e. how much the terrain can resolve per look, not the record.
In Rusty's terms (Oct 10): more topographic detail gives more precise information. That
points at the parental SDKP basis (resolution and axes), which is the experiment not yet run.

## Bounds
Synthetic owners, one authored world, single author. Kinetics is stored but not yet used by
the reread rule. Size carries no information by construction.
