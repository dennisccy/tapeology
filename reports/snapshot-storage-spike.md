# Storage design spike (r14, §13) — measured, not estimated

**Scope**: benchmark only. **No `SNAPSHOT_FORMAT_VERSION` bump, no format shipped, no production
path changed, no recording performed.** Every measurement is over the **18 EXPOSED datasets**; the
spike's own `_exposed_records` filters through `micro_snapshots.withheld_dataset_ids_for_store`, so
no withheld or sealed member was read.

Reproduce: `.venv/bin/python -m scripts.micro_snapshot_storage_spike --json out.json`

---

## Measured — the whole exposed corpus

| quantity | value |
|---|---|
| datasets benchmarked | 18 |
| source trades | 3 815 915 |
| scientific anchors | 3 815 933 (one row per trade, +1 header per dataset) |
| **v1 snapshot bytes** | **6.379 GB** |
| **v1 bytes per source trade** | **1 671.6** |
| **v1 bytes per scientific anchor** | **1 671.6** |
| v1 full read time | 62.1 s (≈103 MB/s) |
| checkpoint store | 2 080 files, 23.4 GB |

## Option A — snapshot v1 as it stands

The observer row is verbose JSONL: every key repeated on every one of ~3.8 M rows, plus a `deferred`
array measured at **31 % of file bytes** on the PG fixture. It is the format the whole pipeline
reads today and it is correct; it is simply ~7× larger than what any consumer uses.

## Option B — the candidate v2 anchor projection

A fixed-width little-endian record per anchor carrying **only the columns a Scout screen or a
walk-forward fold consumes**, derived from the production tables rather than hand-listed (so adding
a feature to `FEATURE_FAMILY_OF` grows the projection automatically):

| column group | count | encoding |
|---|---|---|
| screenable features (`scout.FEATURE_FAMILY_OF`) | 19 | float64 |
| realized outcomes (`scout.HORIZON_KEYS`) | 7 | float64 |
| scalars (`anchor_at`, `mid`, `spread`, both `fallback_frac`) | 5 | float64 |
| `tod_bucket`, `close_out` | 2 | uint8 |
| **total** | | **250 bytes/anchor** |

| | v1 | v2 | factor |
|---|---|---|---|
| whole exposed corpus | 6.379 GB | **0.954 GB** | **6.69×** |
| per anchor | 1 671.6 B | 250 B | 6.69× |
| build/projection time | — | 12.5 s for 3.8 M anchors (≈305 k anchors/s) | |

### Corpus projection, 8-symbol panel

| session dates | symbol-days | v1 snapshots | **v2 snapshots** | raw tape (unchanged) |
|---|---|---|---|---|
| **105** (minimum) | 840 | 907 GB | **136 GB** | ~280 GB |
| 125 | 1 000 | 1 080 GB | 161 GB | ~330 GB |
| **138** (target) | 1 104 | 1 192 GB | **178 GB** | ~370 GB |

**A further lever, not taken here.** Most of the 250 bytes is float64 where the quantity does not
need it: a bps return, a fallback fraction and a normalized feature are all fine in float32, while
`mid`/`spread` are not. A mixed-precision row lands near ~140 B and would roughly halve the v2
column again. That is a design decision for the named revision, not something to guess at now.

## Option C — checkpoint compaction

`RecorderCheckpointStore` holds one raw-fetch cache per 900 s chunk: **23.4 GB across 2 080 files**
for the 80-symbol-day tranche, ≈11.3 MB/chunk. It is a **resume aid, not evidence** — its content
is already inside the finalized `DatasetStore` record, whose checksum verifies independently.

Safe compaction rule: a chunk's checkpoint is deletable once its symbol-day has been finalized into
`DatasetStore` **and** that record's checksum verifies. Projected peak if not compacted: **~250 GB
at 105 sessions, ~320 GB at 138**. Compacting per symbol-day holds the transient cost at roughly one
day's chunks (~300 MB) instead.

This is the cheapest of the three and the only one requiring no format work. It does not solve the
problem on its own.

---

## What the v2 candidate would have to PROVE before it ships

The spike measures size and speed. It does **not** discharge the correctness burden, and that burden
is the whole reason `SNAPSHOT_FORMAT_VERSION` is not bumped here:

1. identical canonical feature/outcome values at every anchor the current Scout and pilot paths use;
2. identical `available_at` / lookahead semantics — the projection stores realized outcomes, so the
   no-lookahead proof has to move with it, not be assumed;
3. identical `screen_candidate` results on the exposed corpus, compared on the served
   `screen_result`, not on intermediate floats;
4. deterministic rebuild from the same dataset bytes;
5. completeness refusal when an expected projection is missing — never an honest skip;
6. no sealed or unexposed member read at any point.

Items 1–3 are the expensive ones and are exactly where a "6.7× smaller and identical" claim would
fail if it were going to fail.

---

## OWNER DECISION

### **PROVISION_STORAGE** — and land v2 only if the storage answer is "no".

Reasoning, in order:

1. **v2 does not remove the need.** At the 105-date minimum, v2 still needs **136 GB of snapshots on
   top of ~280 GB of raw tape ≈ 416 GB**, against **116 GB free**. It turns a ~10× shortfall into a
   ~3.6× shortfall. That is a large improvement and still not a solution.
2. **The raw tape is primary evidence and is not compressible by this route.** ~280 GB at 105 dates
   is irreducible without changing what gets recorded, which would change the corpus rather than its
   encoding.
3. **v2 is a named revision with a real correctness burden** (six items above). Landing it *on the
   critical path of an acquisition* means the campaign waits on a format migration and its proofs,
   and any defect in it silently corrupts every downstream fold. Storage is the cheaper and far
   lower-risk purchase.
4. **The snapshot is rebuildable; the tape is not.** If disk pressure appears mid-campaign, snapshots
   can be rebuilt from tape at ~9 000 trades/s. That asymmetry is the safety margin, and it argues
   for spending the money on capacity rather than on a format that must be right the first time.

**Recommended provisioning**: **~1.6 TB** working / **~1.2 TB** steady at the 105-date minimum with
v1 snapshots, plus **~320 GB** transient checkpoint headroom unless option C is applied per
symbol-day (which costs nothing and should be applied regardless).

**Revisit and land v2 if** the storage decision comes back "no", **or** if a second corpus era is
planned — at which point the 6.69× applies to every future era and the correctness work amortizes
across all of them instead of one.
