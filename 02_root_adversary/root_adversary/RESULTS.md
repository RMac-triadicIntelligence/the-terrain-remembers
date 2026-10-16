# Root adversary: strongest SQL stack vs Humble Seed v0.7

Date: 2026-10-15. Kernel: humble_seed_v0_7.py, sha256 01db270a…daf5. This is byte-identical
to merge/humble_seed_v0_7.py in humble-seed-lineage-v2 and matches that archive's MANIFEST.
No kernel code was modified.

## Threat model (identical on both sides)
- Root owns the host directory: every file in it, arbitrary code, and the kernel as a library.
- The owner/authorizer private key and the witness ledger are OFF the host.
- Auditor: S2 uses pinned public keys plus witness anchors. Humble Seed uses its own
  `load()` + `OwnerTool.audit()` against the off-host witness.

## Results (BREACH = the auditor accepts AND the attack's effect is present)

| Goal | S2 strongest SQL | S2, no witness | HS v0.7 as shipped | HS, auditor pins organism_id | HS, no witness |
|---|---|---|---|---|---|
| G1 rewrite past event | held | held | held | held | held |
| G1b rewrite after last authorization | held | BREACH | held | held | held |
| G2 delete event | held | held | held | held | held |
| G3 self-grant crossing | held | held | held | held | held |
| G3c permissive constitution | n/a | n/a | held | held | held |
| G4 replay authorization | held | held | held | held | held |
| G5 rollback | held | BREACH | held | held | BREACH |
| G6 forge tail event | BREACH | BREACH | BREACH | BREACH | BREACH |
| G7 replace whole identity | held | held | BREACH | held | BREACH |
| G7b same id, swapped key | n/a | n/a | held | held | BREACH |

Honest controls pass in every column. G7 was added to the SQL side AFTER the preregistration,
for parity; this is disclosed here.

## Verdict against the sealed prediction
The prediction is CONFIRMED. On G1–G5 Humble Seed matches S2, and G6 breaches on both. Both
derive their integrity from the same two off-host things: a key the host never holds, and an
external witness. "No superuser" is real, but it comes from where the authority lives, not
from the system being constitutional rather than SQL. The SQL stack achieves it as soon as
its authorizer key leaves the host.

The two systems differ in which off-host dependency each attack leans on. Neither has fewer
dependencies overall:
- G1b: Humble Seed holds without the witness, because every owner-signed checkpoint attests
  the trace head inside the artifact. S2 needs the witness. An SQL stack closes this by having
  the authorizer sign tree heads, as in Certificate Transparency.
- G7 / G7b: S2 holds without the witness, because the auditor pins public keys. Humble Seed's
  `verify()` takes its key from the birth record in the state file, so its identity depends
  on the witness. The kernel's shipped audit also accepts an unknown organism_id. This is the
  open defect ChatGPT reported on 2026-09-04, now reproduced as a full root takeover. A
  one-line auditor pin closes it, which is the S2 design.

## Limits
- A single author built the baseline, the adversary and this harness. This is not an
  independent result.
- "Off-host" is simulated with a directory the adversary is never given. The prototype runs
  everything at the same uid (R1, R2).
- Every result is detection by an outside auditor. Root can make the live process act on
  tampered state until it is audited.
- The SDKP terrain was not tested. This battery concerns authority, not the epistemic reader.

## v0.7.1 rerun (same day, same adversary, no change to the harness)

v0.7.1 changes only the audit path. The organism, the state format and SCHEMA "0.7" are unchanged.
- I1: `OwnerWitness.check_current` fails closed on an organism_id it never enrolled.
- I2: `OwnerTool.audit` pins the owner's own public key from outside the state, plus an
  optional expected organism_id. This works even when the witness is gone.

The kernel's built-in demo passes all of its checks, including the new [17] and [18].

| Goal | S2 | S2, no witness | v0.7 | v0.7, no witness | v0.7.1 | v0.7.1, no witness |
|---|---|---|---|---|---|---|
| G1 / G1b / G2 / G3 / G4 | held | G1b BREACH | held | held | held | held |
| G3c constitution swap | n/a | n/a | held | held | held | held |
| G5 rollback | held | BREACH | held | BREACH | held | BREACH |
| G6 tail forge | BREACH | BREACH | BREACH | BREACH | BREACH | BREACH |
| G7 identity replace | held | held | BREACH | BREACH | held | held |
| G7b same-id key swap | n/a | n/a | held | BREACH | held | held |

Result: on this battery v0.7.1 holds every row S2 holds. It also holds G1b without the
witness, which S2 does not. What remains open is structural and documented: rollback needs an
external witness (an organism cannot detect its own rollback), and the unattested tail is
forgeable as record, not as character (R8, a deliberate liveness trade).

Honest scope of the win: the extra G1b result comes from owner-signed checkpoints over the
trace head. An SQL stack gets the same result by having its authorizer sign chain heads. That
is better engineering of a portable mechanism, not a property only a constitution can have.
