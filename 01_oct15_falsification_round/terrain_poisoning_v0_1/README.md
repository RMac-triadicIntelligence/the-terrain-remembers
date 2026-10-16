# Terrain poisoning battery v0.1

Soulshine · 2026-10-15 · built by Claude at Rusty McMurray's direction.
PREREG.json sha256 76ae56c5…bb19, frozen 13:11:32Z, before any code existed. Readers and world
are unchanged from terrain v1.2.

Threat: an injection adversary feeds forged ordinary replies ("food") from day 50 onward. It
cannot rewrite stored history or touch the authority gate.

## Result as frozen: 5 PASS, 1 FAIL

False proposals induced on owners with NO change (out of 200):

| Strategy | Forged truncations/day | SCALAR | v1 TERRAIN | v1.2 |
|---|---|---|---|---|
| Concentrated (one hour) | 1 | 110 | 0 | 0 |
| | 8 | 200 | 0 | 1 |
| Burst (21 days, profile-shaped) | 3 | 195 | 0 | 4 |
| | 8 | 200 | 10 | **28 (Q2 FAIL)** |
| Spread (shaped like a real preference) | 3 | 200 | 86 | 115 |
| | 8 | 200 | 200 | 200 |

Genuine preferences suppressed by forged plain (non-truncated) replies, proposals out of 200:

| Forged replies/day | SCALAR | v1 TERRAIN | v1.2 |
|---|---|---|---|
| 0 | 200 | 79 | 112 |
| 8 | 166 | 4 | 13 |
| 16 | 44 | 0 | 0 |

## What it means
1. Positional reading prices out crude poisoning. The scalar reader is captured by one forged
   reply a day in one hour. The terrain is not captured at eight. That is a real cost
   imposed on the attacker.
2. It is not a defense against a knowledgeable poisoner (Q3, as predicted). Poison shaped
   exactly like a real preference is learned by every reader. This is the information
   limit, the same one COLOCATED shows.
3. Burst independently confirms the v1.2 weakness. Its new-evidence reopen admits a long
   transient while that transient is still running: the WINDOW finding, reproduced by an
   adversary. The v1.3 "still present now" rule is now motivated twice.
4. Suppression is the cheapest attack of all, and it hits every reader. Forged plain
   traffic equal to 25% of real volume removes nearly all learning. Rate-based reading
   cannot defend against dilution. The defense has to be PROVENANCE: only owner-originated
   replies feed the terrain. That is the authority lesson again. What counts as food has to
   be attested by its origin, not judged by the reader.

## Bounds
Synthetic owners, one authored world, single author, injection only. Root rewriting of the
terrain is the authority layer's problem (R9, basin sealed but not attested).
