# terrain v1.9: two layers, and the conductor in action

Soulshine · 2026-10-15 · built by Claude at Rusty McMurray's direction.
PREREG.json sha256 924d5225…e6fe, frozen 15:38:44Z, before any v1.9 code existed.

Direction (Rusty): whether a local, momentary behaviour is a correct action is not the
organism's decision. It simply asks the conductor / creator. That is the conductor in action.

- **Character layer:** v1.6, untouched. It proposes character change for the owner's signature.
- **Map layer** (Claude's operationalization, flagged): a LOCAL scout finds a region running
  hot on the frontier. A different member arrives one block later and checks the same region
  on new data. Unconfirmed finds lapse with no penalty. Confirmed finds that are not character
  become ONE ask to the conductor. The housekeeper never asks about the same place twice. The
  conductor's answer is not simulated; this version measures the asking.

## Result as frozen: 6 PASS, 0 FAIL

| λ128 | owners asked | asks per owner | asked regions in the right place | character proposals |
|---|---|---|---|---|
| COMMUTE | **99.3%** | 1.11 | **86% commute hours** | 3 |
| DINNER | **100%** | 1.12 | **85% dinner hours** | 0 |
| WINDOW (difficult month) | 95.7% | 1.39 | spread (as it is) | 25 |
| GENUINE | 97.7% | 2.40 | spread (as it is) | 300 |
| NULL (nothing there) | **0.0%** | 0.00 | — | 0 |

At λ32: commute 99.7% asked (75% commute hours), dinner 99.7% (74% dinner hours), NULL 0.3%.

- AA1: the character layer made the identical decision to v1.6 on all 5,400 streams. The
  map never touches who the organism is.
- First asks arrive around day 78–82, about four weeks after the change began, and before
  the character layer would cross.

## What it means
The two layers do different work and neither breaks the other.
- The map sees everything real that the character layer correctly refuses to become: the
  commute, the dinner hour, the difficult month. It names the place and the time and asks
  the one who can answer: "Brief at weekday mornings — is that you?" It never asks about
  nothing.
- Character stays slow, global and signed, with the best safety profile in the program.

This also answers ChatGPT's open point 5 (context-specific genuine preferences) without
the organism having to decide it. The question goes to the conductor.

## Not yet tested
What the conductor's answers do: whether a "yes, that's me at commute time" becomes
inherited ground, and whether answers make later asks rarer. That needs the conductor's
answer policy, which is Rusty's.

## Bounds
Synthetic owners, one authored world, single author. Full-sight world. The scouts' value under
limited sight is still untested.
