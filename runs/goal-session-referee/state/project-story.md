# Project story so far

Tapeology is a research app with three screens — a live-tape Cockpit, a Structure page that maps where a stock tends to bounce or stall, and a Desk that scans for chart setups and logs every signal it sees, honestly, without ever placing a real trade.

## How it has grown

This chapter, "The Referee," teaches the product to check its own homework — telling a pattern noticed by eye apart from one imagined in noise. It built the checking machinery behind the scenes first: a shared evidence record, a statistics engine for judging whether a pattern is real, matched "nothing happened" comparisons, a permanent notebook that locks in a question's start date forever, and a judge that turns a question into one permanent verdict no later check can change — closing two soft spots (a false answer slipping past a failed self-check, a damaged record vanishing silently) the same rounds they were found.

The Desk page then got its first real Referee screen, "Referee Registry," where a person reviews candidate research questions with live evidence counts and registers one for real — and soon after, its first hard rule: the core trading strategy can never be swapped for a new one without a genuine certificate from the fact-checking system, proven by trying every way to sneak past it and watching each attempt get honestly refused. One gap stayed open: the certificate named which strategy it was for, but nothing checked its evidence truly came from that strategy.

This latest round finished the job. The Desk page gained its last two Referee sections: "Referee Adjudications," showing every registered question's plain verdict word plus its full evidence trail, and "Referee Runs," letting a person start a check, watch it run live, cancel it, and see a history of every run. The open evidence gap was closed too — a certificate can no longer be stamped with a strategy's name unless its evidence genuinely belongs to that strategy — and the Claude assistant connector grew from 20 to 22 read-only tools. Seven older parts of the product still need a fresh re-check before this chapter is finished; that is next.

## What it can do today

The product lets users watch the live tape on the Cockpit, look up a stock's price map on the Structure page, and scan chart setups on the Desk. On the Desk page, users can open "Referee Registry" to review and register a research question, "Referee Adjudications" to see each question's plain verdict and evidence trail, and "Referee Runs" to start a check and watch its progress and history. The core trading strategy is protected — it cannot be replaced unless a genuine, matched certificate backs the replacement.

_Last updated: 2026-08-15 after iteration 10._
