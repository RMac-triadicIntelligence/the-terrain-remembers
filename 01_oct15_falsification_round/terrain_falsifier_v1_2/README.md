# terrain falsifier v1.2: reconsider on new evidence

Soulshine (Tulsa, OK) · 2026-10-15 · built by Claude at Rusty McMurray's direction.
v1.1 is preserved and was reproduced bit-identically before this work (receipt fc6b84da…4b50).

Only one thing changes from v1.1: the reopening rule. A HELD item is now reconsidered
only on evidence that arrived AFTER the hold (at least 14 days of it), read across the
whole terrain against the baseline the hold was judged on. The check requires both
positional spread and persistence, so pressure alone never reopens. The footprint is
recorded but no longer gates anything.

PREREG.json sha256 3c1e46ee…d48b, frozen 2026-10-15T13:08:36Z, before any v1.2 code existed.

## Result as frozen: 7 PASS, 2 FAIL

| | v1 | v1.1 | v1.2 |
|---|---|---|---|
| Lockout probe | — | HELD, 87 checks, 0 reopens | **PROPOSED day 90** |
| GENUINE learned, λ32 | 120 | 160 | **173** |
| GENUINE learned, λ128 | 295 | 153 | **299** |
| COMMUTE / DINNER false, λ32 | 0 / 0 | 4 / 2 | 0 / 0 |
| COMMUTE / DINNER false, λ128 | 0 / 0 | 10 / 5 | 4 / 2 |
| WINDOW false, λ32 | 20 | 20 | **28 (P4 FAIL)** |
| WINDOW false, λ128 | 112 | 54 | **78 (P4 FAIL)** |
| Macro action accuracy, λ32 | .8375 | .8478 | .8516 |
| Macro action accuracy, λ128 | .8738 | .8302 | **.8836** |

- P5 FAIL, narrowly. Held-confound reopen shares were 0.050 / 0.054 / 0.057 / 0.040
  against a ≤ 0.05 bar. At λ32 none of the 31 reopened commute/dinner streams went on to
  propose. At λ128, 4 of 29 did. Confound false proposals are at or below v1.1 at both
  traffic levels.
- The liveness defect is closed. The absorbing hold is gone, and at high traffic v1.2
  learns 299/300 genuine preferences and beats v1 on action accuracy, which v1.1 lost.
- Costs are unchanged in kind: 1.39 full looks per owner against v1's 46.

## The price: the difficult month (P4 FAIL)
Every one of the new WINDOW false proposals came through a reopen, on days 78–92, right at
the end of the 30-day window (days 50–79). Evidence that arrived after the hold sat entirely
inside the difficult month, so it looked broad and persistent. The full look then passed
because its span was dominated by the window. The new-evidence rule cannot tell a long
transient from a lasting change while the transient is still running.

v1.3 candidate, NOT applied: require the most recent block of the new evidence to remain
positive by itself, i.e. the change must still be present now and not just have been
present since the hold.

## Mutation lane
- M1 (pressure alone reopens): every held COMMUTE reopens (share 1.0). Caught by P5.
- M2 (old evidence instead of post-hold evidence): GENUINE drops to 202 and COMMUTE
  reopen share falls to 0.05.
- M3 (polling): 59.7 reads per stream against 18.7. Caught.

## Bounds
Synthetic owners in one authored world; single author; no independent reproduction yet.
COLOCATED stays indistinguishable from GENUINE (|z| ≤ 1.0), as the information limit
requires.
