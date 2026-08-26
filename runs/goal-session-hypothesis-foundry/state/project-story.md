# Project story so far

Tapeology's newest research chapter, the Hypothesis Foundry, aims to turn every already-approved trading idea sitting in the research notes into one fair, no-cheating test — automatically, without a person picking winners along the way.

## How it has grown

This chapter opened by taking stock before writing any new code: the previous chapter (the Rapid Microscope) was confirmed safely archived, its old "keep researching forever" auto-loop switched off, and a dated handover note recorded — though a small setup snag briefly stopped proof screenshots from being taken.

The second round fixed that snag honestly, without touching the safety check that caught it. The Desk page gained a new "Hypothesis Foundry" section correctly naming the active research chapter, though its starting-numbers display still needed a visibility fix. Behind the scenes, the rulebook for turning an approved idea into a fair, testable specification was built and proven on seven practice examples.

The third round closed that visibility gap — the Foundry section now genuinely shows its real starting numbers, completing the chapter's first milestone — and built five more behind-the-scenes pieces: a reader that reaches the same yes/no decision as Tapeology's existing statistical check, a piece that limits how many variants of one idea are allowed, a piece that locks the whole set of ideas down before any result is seen, and a permanent, separate record-keeper for every trial.

The fourth round put all of that machinery through one combined practice run containing every possible outcome at once — a blocked idea, an excluded idea, an aliased idea, and seven candidates ending in every different way the system can reject or accept a candidate — and every one landed correctly, in the right order, with matching paperwork. The round also proved the system survives a mid-run crash without losing or duplicating work, and correctly refuses to invent a result when a practice run tries to touch off-limits data. Two loose ends from earlier rounds were tied up: resuming an already-finished trial now double-checks its numbers before handing back a result, and every source idea's record now carries a tamper-proof fingerprint plus a note of any legal alternate version. Nothing new appeared on screen this round — the proof lives entirely in automated tests — so the next round is expected to build the one Foundry screen that finally lets a person see all of this proven work.

## What it can do today

The product lets users open the Desk page and see, in the "Hypothesis Foundry" section, that this is a new, self-contained research chapter with the old chapter safely closed off, plus the real starting numbers this chapter will be measured against. The rulebook and machinery that will turn approved research ideas into fair, automatic tests are built and privately verified end-to-end, but have no on-screen view of their own yet. The rest of Tapeology (the Desk, Cockpit, and Structure Map) is untouched and works exactly as before.

_Last updated: 2026-08-27 after iteration 3._
