# Project story so far

Tapeology's newest research chapter, the Hypothesis Foundry, aims to turn every already-approved trading idea sitting in the research notes into one fair, no-cheating test — automatically, without a person picking winners along the way.

## How it has grown

This chapter opened by first taking stock, before writing a single line of new code. The very first check confirmed the handover from the previous research chapter (the Rapid Microscope) was done correctly: that chapter's records are safely archived and untouched, a dated note marks exactly when the new chapter began, and the old "keep researching forever" auto-loop has been switched off, exactly as this new, deliberately finite chapter requires. That first check also turned up one practical snag: the tool that takes proof screenshots couldn't run at all, because a small setup script for its practice sandbox forgot to label one of its numbers.

The second round fixed that snag properly — the setup script now labels the number it was missing, and the safety check that caught the problem in the first place was left completely alone, exactly as it should be. With the screenshot tool working again, two real pieces of work then went in. First, the Desk page gained a new "Hypothesis Foundry" section: opened up, it correctly announces which research chapter is active (the previous one closed, this one open). It's also meant to show the frozen starting numbers the whole chapter will be measured against, but that part read "not recorded yet" in this round's testing, so it isn't confirmed working for a real user yet — the numbers themselves are genuine and were double-checked, they just aren't visible to the practice copy of the site yet. Second, and entirely behind the scenes so far, the actual rulebook for turning an approved research idea into a fair, testable specification was built and proven against seven practice examples covering every kind of idea the rulebook needs to handle — a clean case, two legal variants of the same idea, a vague idea, a proxy-only idea, an unsupported idea, and an idea with no clear direction. All seven were handled correctly, and nothing about the trading decisions Tapeology already makes was touched.

Nothing about the rest of the product changed. The full underlying health check suite still passes cleanly, and the Desk, Cockpit, and Structure Map from earlier chapters work exactly as they did before.

## What it can do today

Nothing from this chapter is confirmed working for a user yet. The product has a new "Hypothesis Foundry" section on the Desk page that correctly shows which research chapter is open, with its starting-numbers display still unproven in testing. The rulebook that will turn approved research ideas into fair tests is built and privately verified, but not yet visible anywhere a user can see it. The rest of Tapeology (the Desk, Cockpit, Structure Map, and everything shipped in earlier chapters) is untouched and works as before.

_Last updated: 2026-08-26 after iteration 1._
