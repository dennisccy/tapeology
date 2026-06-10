"""The research evolution package (capabilities 20-34), layered strictly on top of the engine.

This iteration builds the keystone subset: the taxonomy (the single backend owner of every
research label), a journal-scoped SQLite store, the research monitor (attached via the engine's
observer seam, read-only over the engine), and the ``/research/*`` REST namespace for declaring a
thesis and reading its projection. The verdict stays honestly ``pending`` — the verdict-transition
engine arrives next iteration.

The package is observer-only: it NEVER mutates engine / classifier / feature state, so the same
event stream yields byte-identical engine outputs with or without an active thesis (equivalence
anti-goal). Nothing here imports from ``app.engine`` except read-only snapshot types.
"""
