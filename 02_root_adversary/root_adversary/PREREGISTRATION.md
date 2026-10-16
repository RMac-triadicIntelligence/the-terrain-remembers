# Pre-registration — constitutional side (written before seeing the kernel)

Date: 2026-10-15. The SQL-side results are in results_sql.json.

Prediction: on G1–G5 the Humble Seed v0.7 kernel will MATCH S2, not beat it.
Reason: both derive integrity from the same two off-host things, the owner/
authorizer key and the witness. G6 (forge new tail event) will BREACH, as it
did in S2. This matches the documented residual (unattested trace tail).

The "no superuser" advantage is SUPPORTED only if the kernel holds on some goal
where S2 breaches, or holds S2's results with fewer off-host dependencies.
It is REFUTED as a constitutional property if the kernel's results equal S2's
and are produced by the same mechanism (external key plus witness).

The same adversary module is used. The only changes allowed are adapters that
give root the kernel's files. The auditor is the kernel's own public verify/
audit path, with pinned keys and the witness kept off-host.
