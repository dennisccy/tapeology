# Project story so far

Tapeology's newest research chapter, the Hypothesis Foundry, aims to turn every already-approved trading idea sitting in the research notes into one fair, no-cheating test — automatically, without a person picking winners along the way.

## How it has grown

This chapter opened by taking stock before writing any new code. The first check confirmed the handover from the previous chapter (the Rapid Microscope) was done correctly: its records are safely archived and untouched, a dated note marks when the new chapter began, and the old "keep researching forever" auto-loop was switched off. That check also found one snag — the tool that takes proof screenshots couldn't run, because a small setup script forgot to label one of its numbers.

The second round fixed that snag the honest way, leaving the safety check that caught it completely alone. The Desk page then gained a new "Hypothesis Foundry" section that correctly announces which research chapter is active, though its "starting numbers" display still read "not recorded yet" in testing — the real numbers were genuine, just not yet visible to the test copy of the site. Behind the scenes, the rulebook for turning an approved research idea into a fair, testable specification was built and proven against seven practice examples covering every kind of idea it needs to handle.

The third round closed that visibility gap the honest way: the test copy of the site was given a read-only look at the same real recorded numbers, each one double-checked against the underlying files before being trusted. The "Hypothesis Foundry" section on the Desk page now genuinely shows its real starting numbers, completing this chapter's very first milestone. At the same time, five more behind-the-scenes pieces were built and proven: a reader that turns one approved idea into the same fair yes/no decision Tapeology's existing statistical check already makes (proven to give the identical answer on every practice case tried), a piece that limits how many variants of one idea are allowed and refuses late additions, a piece that locks the whole set of ideas down before any result is looked at, and a permanent record-keeper for every trial that never mixes with Tapeology's existing decision records. One loose end was found and flagged for the next round: if the process is interrupted and resumed, it can currently hand back an old answer instead of double-checking the idea hasn't changed since.

## What it can do today

The product lets users open the Desk page and see, in the "Hypothesis Foundry" section, that this is a new, self-contained research chapter with the old chapter safely closed off, plus the real starting numbers this chapter will be measured against. The rulebook that will turn approved research ideas into fair, automatic tests is built and privately verified, but has no on-screen view of its own yet. The rest of Tapeology (the Desk, Cockpit, and Structure Map) is untouched and works exactly as before.

_Last updated: 2026-08-26 after iteration 2._
