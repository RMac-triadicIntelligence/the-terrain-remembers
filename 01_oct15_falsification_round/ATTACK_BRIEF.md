# Cold-review brief: October 15 falsification round

For Grok, ChatGPT and any other reviewer. Attack it; don't confirm it. Re-reporting a
listed known item is not a finding.

## What is here
1. `root_adversary_battery/`: a root-level adversary against the strongest SQL stack and
   against Humble Seed v0.7 / v0.7.1 (`humble_seed_v0_7_1.py`, an audit-path-only patch).
   Claim: v0.7.1 holds every attack the SQL stack holds, and also holds the after-auth
   rewrite without a witness.
2. `terrain_falsifier_v1_2/`: the reopening rule changed to "new evidence, whole terrain".
   7 PASS, 2 FAIL as frozen.
3. `terrain_poisoning_v0_1/`: an injection adversary feeding forged replies. 5 PASS, 1 FAIL.
4. `terrain_vs_sql_v0_1/`: terrain against rented memory (RAG), a flat log, and the terrain
   reading implemented in SQL. 4 PASS, 1 FAIL.

Every package has a PREREG frozen before its code, a MANIFEST, and a deterministic RECEIPT.

## Known items (already reported, not findings)
- Root can forge new tail events (R8). Rollback needs an external witness.
- v1.2 admits more WINDOW transients (P4 FAIL) and burst poison (Q2 FAIL). v1.3 candidate
  named, not applied.
- Dilution suppresses learning in every reader; provenance is named as the defense.
- SQL reproduces the terrain's decisions exactly. The advantage is the reading, not the store.
- Single author, synthetic owners, one authored world. "Off-host" is a directory the
  adversary is not given.

## Where findings would matter most
- A root attack that gets v0.7.1's `OwnerTool.audit` to accept, other than R8 or rollback.
- A family, seed or schedule where v1.2 regresses against v1.1 on COMMUTE/DINNER/NULL.
- Evidence that the RAG baseline is a straw man: a stronger retrieval reader that matches
  V12 on the same worlds.
- Any leak of the family label or future data into a reader.
- Any place a PREREG threshold and the code that scores it disagree (v1.1 had one).
