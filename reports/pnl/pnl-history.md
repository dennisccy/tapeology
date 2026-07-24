# PnL History — the append-only enhancement ledger

> simulated — assumed fees/slippage — not indicative of live results

A pure render of the stored PnL-ledger rows — `GET /research/pnl/ledger` serves the same
rows verbatim (Data Contract row 32). Every figure is a simulated measurement of recorded
historical tape under the disclosed fee/slippage assumptions — never live results, never
a forecast, and not a profitability claim. Train and hold-out figures are separate and
never pooled. A split whose n is below the configured minimum (5) carries an
explicit insufficient-sample label, with its n still shown.

## 1. founding baseline — strategy v1 on default

- Enhancement id: `founding-baseline-strategy-v1-default`
- Appended (UTC): 03-07-2026
- Strategy `v1` · profile `default` · config fingerprint `4d665603569b9dbf`
- Founding row — no prior incumbent: the baseline side is explicitly absent (`null`), never fabricated zeros.

| side | split | net R | net $ | n | sample |
|------|-------|------:|------:|--:|--------|
| candidate | train | -0.16000000000001136 | -16.000000000001137 | 1 | insufficient sample (n < 5) |
| candidate | holdout | 0.3334000000001356 | 33.34000000001356 | 1 | insufficient sample (n < 5) |

- Provenance (train): backtest `b6d9a90d3a29447a93d73e6016e22b7f` · dataset `9396fd5816394236b365f3da51a0bbe1` · checksum `dcf14dbd91b04c60b9f0cce6cd9dcc4e36122ed4cc2af416f69829d07697f71c`
- Provenance (holdout): backtest `318028528e594ab0a4974aba84505ab3` · dataset `aa749b668553473294e7ca5a9caa69d6` · checksum `c6b34adec8ba2b6623026120cb51e86f98c40efda9169f9cc388336b2ef4f8af`

## 2. founding baseline — strategy v1 on default (post-clean-slate epoch)

- Enhancement id: `founding-baseline-strategy-v1-default-clean-slate`
- Appended (UTC): 24-07-2026
- Strategy `v1` · profile `default` · config fingerprint `08e471b10130e1e2`
- Founding row — no prior incumbent: the baseline side is explicitly absent (`null`), never fabricated zeros.

| side | split | net R | net $ | n | sample |
|------|-------|------:|------:|--:|--------|
| candidate | train | -0.16000000000001136 | -16.000000000001137 | 1 | insufficient sample (n < 5) |
| candidate | holdout | 0.3334000000001356 | 33.34000000001356 | 1 | insufficient sample (n < 5) |

- Provenance (train): backtest `7ac14a512289427c8cb9d73618940fe2` · dataset `9396fd5816394236b365f3da51a0bbe1` · checksum `dcf14dbd91b04c60b9f0cce6cd9dcc4e36122ed4cc2af416f69829d07697f71c`
- Provenance (holdout): backtest `9e134e5604ad4ab1ad5291cac61e8882` · dataset `aa749b668553473294e7ca5a9caa69d6` · checksum `c6b34adec8ba2b6623026120cb51e86f98c40efda9169f9cc388336b2ef4f8af`
