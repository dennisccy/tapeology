"""Test-owned durable caches for the REAL-corpus tests — one namespace, one place.

WHY THIS EXISTS
---------------
Three test files assert against the ACTUAL committed tick corpus at
``apps/backend/.data/datasets`` rather than a fixture, because the acceptance they carry is
"the real corpus still produces this answer" and a fixture cannot stand in for that. Built
naively, each of them re-parsed and re-checksummed the whole ~26 GB store on EVERY pytest
invocation: ``test_micro_readiness.py`` took 14m38s, ``test_micro_join.py`` 27m57s, and
``test_micro_snapshots.py`` alone carried ~80% of the entire suite's wall clock.

iter-28 fixed the first two by handing them the production durable-cache primitives
(``DatasetStore(index_db_path=...)`` + ``MicroReadinessCache``) instead of a throwaway
``tmp_path`` — the same ones ``routes.py``'s ``get_dataset_store()`` already wires for the live
backend. That was the right mechanism pointed at the wrong FILES: it resolved to the operator
backend's own ``.data/dataset_index.db`` and ``.data/micro_readiness_cache.db``, so a test run
and a running backend became two writers of one SQLite file for no benefit (iter-28 audit; owner
ruling 2026-08-24, task A2).

This module is the fix and the single place the decision lives:

* the SAME production cache classes and the SAME key semantics — nothing here re-implements a
  cache, and no production module is imported for anything but its real primitive;
* PERSISTENT across pytest invocations (that is the whole point — one cold warm-up, then warm);
* ISOLATED from the live backend: everything lands under a dedicated ``test-cache/`` sibling of
  the dataset store, never the store's own ``.data/`` root;
* SAFE TO DELETE at any moment. Both caches are derived, stat/content-keyed projections that own
  no research truth (``dataset_index.py``: "losing or deleting this DB file loses nothing and
  fabricates nothing"; ``MicroReadinessCache``: "rebuildable result only, owns nothing"). Deleting
  ``.data/test-cache/`` costs exactly one slow run and changes no answer;
* raw dataset files are NEVER touched — these are read paths with a metadata sidecar.

Deliberately NOT read here: ``TAPEOLOGY_DATASET_INDEX_DB`` and
``TAPEOLOGY_MICRO_READINESS_CACHE_DB``. Those env vars are how an OPERATOR points the running
backend at its cache DBs; honouring them here is precisely how the test path ended up on the live
files. ``TAPEOLOGY_TEST_CACHE_DIR`` is this namespace's own override, and
``test_real_corpus_cache_scope.py`` is the guard that proves the two never coincide.
"""

from __future__ import annotations

import os
from pathlib import Path

from app.research.datasets import DatasetStore
from app.research.micro_readiness import MicroReadinessCache

# This namespace's own override (CI, or an operator who wants the test caches elsewhere).
TEST_CACHE_DIR_ENV = "TAPEOLOGY_TEST_CACHE_DIR"

# The dedicated sibling directory. A directory, not a filename prefix, so `rm -rf` is the whole
# reset procedure and no live file can ever be caught by it.
TEST_CACHE_DIRNAME = "test-cache"

# The two derived cache files, named exactly as their live counterparts so the ONLY difference
# between a test cache and a live cache is which directory it sits in — the property the scope
# guard asserts, and the one that is easy to eyeball on disk.
DATASET_INDEX_DB_NAME = "dataset_index.db"
MICRO_READINESS_CACHE_DB_NAME = "micro_readiness_cache.db"

# The operator env vars this module must never follow (asserted by the scope guard).
LIVE_CACHE_ENV_VARS = ("TAPEOLOGY_DATASET_INDEX_DB", "TAPEOLOGY_MICRO_READINESS_CACHE_DB")


def live_cache_dir(dataset_dir: str | Path) -> Path:
    """Where the LIVE backend keeps its derived cache DBs: the dataset store's own parent, the
    ``resolve_micro_readiness_cache_db_path`` / ``get_dataset_store()`` env-else-sibling shape
    (e.g. ``.data/datasets`` -> ``.data``)."""
    return Path(dataset_dir).resolve().parent


def test_cache_dir(dataset_dir: str | Path) -> Path:
    """Where the TEST suite keeps its own copies of those DBs."""
    override = os.environ.get(TEST_CACHE_DIR_ENV)
    if override:
        return Path(override).expanduser().resolve()
    return live_cache_dir(dataset_dir) / TEST_CACHE_DIRNAME


def live_dataset_index_db_path(dataset_dir: str | Path) -> str:
    """The live backend's ``dataset_index.db`` — the sibling default, deliberately ignoring
    ``TAPEOLOGY_DATASET_INDEX_DB``. Used only by the scope guard, to have something concrete to
    prove the test path differs from."""
    return str(live_cache_dir(dataset_dir) / DATASET_INDEX_DB_NAME)


def live_micro_readiness_cache_db_path(dataset_dir: str | Path) -> str:
    """The live backend's ``micro_readiness_cache.db`` (sibling default). Guard use only."""
    return str(live_cache_dir(dataset_dir) / MICRO_READINESS_CACHE_DB_NAME)


def test_dataset_index_db_path(dataset_dir: str | Path) -> str:
    return str(test_cache_dir(dataset_dir) / DATASET_INDEX_DB_NAME)


def test_micro_readiness_cache_db_path(dataset_dir: str | Path) -> str:
    return str(test_cache_dir(dataset_dir) / MICRO_READINESS_CACHE_DB_NAME)


def real_corpus_dataset_store(dataset_dir: str | Path) -> DatasetStore:
    """A ``DatasetStore`` over the real corpus, wired with the production durable
    ``index_db_path=`` primitive pointed at this suite's OWN index DB.

    The index is a stat-keyed (``path``, ``size``, ``mtime_ns``) metadata projection: a hit is
    metadata ``DatasetStore._load`` itself already checksum-verified, and any stat difference is a
    miss that re-verifies in full. Dataset CONTENT is never cached at either layer, and
    ``load_events``/``replay`` bypass the cache entirely on every call — so this changes only how
    often the same verified answer is recomputed, never what any test can observe.
    """
    return DatasetStore(dataset_dir, index_db_path=test_dataset_index_db_path(dataset_dir))


def real_corpus_readiness_cache(dataset_dir: str | Path) -> MicroReadinessCache:
    """A ``MicroReadinessCache`` on this suite's OWN DB. Keyed by dataset content ``checksum``,
    so a row can only ever be reused for byte-identical content — sharing the namespace across
    test files is safe by construction, and a miss never computes."""
    return MicroReadinessCache(test_micro_readiness_cache_db_path(dataset_dir))
