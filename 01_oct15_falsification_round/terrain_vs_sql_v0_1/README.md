# Terrain vs SQL v0.1: is the advantage the store or the reading?

Soulshine · 2026-10-15 · built by Claude at Rusty McMurray's direction.
PREREG.json sha256 50038f0e…513e, frozen 13:13:41Z, before any code existed.

Four readers, identical worlds (6 families × 300 owners × λ32/λ128):
- **V12**: the terrain organism (v1.2), storing only per-(day, region) counts.
- **RAG**: the standard rented-memory pattern. Every reply is kept as a row; at each encounter
  it retrieves similar-context rows, applies the same persistence rigor, and is stateless.
- **FLAT**: V12 with position removed. Same discipline, flat log.
- **SQLT**: V12 with every data access done as SQL GROUP BY queries over a rows table.

## Result as frozen: 4 PASS, 1 FAIL

| | V12 | RAG | FLAT | SQLT |
|---|---|---|---|---|
| Macro action accuracy, λ32 | **.852** | .762 | .647 | **.852** |
| Macro action accuracy, λ128 | **.884** | .756 | .620 | **.884** |
| COMMUTE encounters acted brief, λ32 | 0.0% | 9.6% | 59.1% | 0.0% |
| GENUINE encounters acted brief, λ32 | 32.5% | 1.7% | 58.6% | 32.5% |

- Y1 PASS: the terrain's reading beats rented memory at both traffic levels. Caveat: most of
  RAG's deficit is failing to learn real preferences. Its narrow context windows hold too
  few replies to clear the persistence test. A higher-powered retrieval baseline would
  narrow the gap. The confound side holds regardless.
- Y2 PASS: position is load-bearing. Without it the same discipline acts brief on 59% of
  commute encounters.
- Y3 FAIL, narrowly: RAG acted brief on 9.6% of commute encounters against a ≥10% prediction.
- **Y4 PASS: SQLT made the identical decision to V12 on all 3,600 streams.** The advantage
  is the READING DISCIPLINE: position against the owner's own history, persistence,
  holding on need, and reconsidering on new evidence. Standard SQL expresses all of it.
- Y5 PASS: the terrain store is 30% of the row store at λ32 and 8.5% at λ128. It is fixed in
  size (days × regions) while rows grow with every reply, and no individual reply is kept.

## Answer to "is it substantially better than SQL?"
Not as a database. As a way of reading memory, yes: it beats the rented-memory pattern by
9–13 accuracy points, and position alone is worth 20–26 points. But the reading can be run
on SQL with bit-identical decisions. What is genuinely the terrain's own:
- constant-size memory that does not retain individual events (size and privacy), and
- the coordinate basis it reads in, which in Raised, Not Rented is a parental choice. This
  battery used one authored basis for every owner and so did not test that.

## Bounds
Synthetic owners in one authored world; single author. RAG is one reasonable instance of the
pattern, not its strongest form. The world's labels treat commute brevity as wrong, which is
ChatGPT's open point about context-specific genuine preferences.
