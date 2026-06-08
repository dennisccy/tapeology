# Test Failure Digest

**Runner detected:** `pytest`
**Summary:** 228 passed, 3 failed
**Source log:** `reports/qa/goal-i_will_be_super_rich-iter-12-test.log`

## Failing Tests (3 shown)

### 1. `test_adapter_applies_real_http_timeout_to_sdk_session`
- **Location:** `tests/test_vendor_responsiveness.py:121`

**Error:**
```
ModuleNotFoundError: No module named 'alpaca'
```

<details><summary>Traceback excerpt</summary>

```
def test_adapter_applies_real_http_timeout_to_sdk_session():
        # The real call-level bound is set at the SDK client's requests.Session layer: a constructed
        # client's session.request injects timeout=CONFIG.vendor_http_timeout_seconds by default. This
        # is what cuts a slow/large response off at the vendor call (distinct from the outer wrapper).
>       from alpaca.data.historical import StockHistoricalDataClient
E       ModuleNotFoundError: No module named 'alpaca'

tests/test_vendor_responsiveness.py:121: ModuleNotFoundError
```

</details>

### 2. `test_with_http_timeout_is_idempotent_and_defensive`
- **Location:** `tests/test_vendor_responsiveness.py:144`

**Error:**
```
ModuleNotFoundError: No module named 'alpaca'
```

<details><summary>Traceback excerpt</summary>

```
def test_with_http_timeout_is_idempotent_and_defensive():
        # Wrapping twice does not double-wrap (idempotent); a client without a usable session is left
        # unchanged (the outer wrapper still bounds the call) rather than guessed at.
>       from alpaca.data.historical import StockHistoricalDataClient
E       ModuleNotFoundError: No module named 'alpaca'

tests/test_vendor_responsiveness.py:144: ModuleNotFoundError
```

</details>

### 3. `test_real_adapter_empty_result_consults_get_asset_to_classify`
- **Location:** `tests/test_vendor_responsiveness.py:329`

**Error:**
```
ModuleNotFoundError: No module named 'alpaca'
```

<details><summary>Traceback excerpt</summary>

```
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x72fe28316030>
with_creds = <_pytest.monkeypatch.MonkeyPatch object at 0x72fe28316030>

    def test_real_adapter_empty_result_consults_get_asset_to_classify(monkeypatch, with_creds):
        # The folded determination: on an EMPTY data result the adapter consults get_asset ONCE to
        # decide unknown-symbol vs empty-window. A tradable asset -> NoDataForWindow; a 404 ->
        # SymbolNotTradable. This proves the second round-trip is paid ONLY on the empty path.
>       import alpaca.common.exceptions as exc_mod
E       ModuleNotFoundError: No module named 'alpaca'

tests/test_vendor_responsiveness.py:329: ModuleNotFoundError
=========================== short test summary info ============================
FAILED tests/test_vendor_responsiveness.py::test_adapter_applies_real_http_timeout_to_sdk_session
FAILED tests/test_vendor_responsiveness.py::test_with_http_timeout_is_idempotent_and_defensive
FAILED tests/test_vendor_responsiveness.py::test_real_adapter_empty_result_consults_get_asset_to_classify
ERROR tests/test_vendor_responsiveness.py::test_trades_and_quotes_are_fetched_concurrently
ERROR tests/test_vendor_responsiveness.py::test_successful_fetch_makes_one_round_trip_no_preflight
ERROR tests/test_vendor_responsiveness.py::test_window_cache_hit_skips_vendor_and_replays_same_real_window
ERROR tests/test_vendor_responsiveness.py::test_window_cache_is_keyed_by_window_and_misses_on_a_different_range
ERROR tests/test_vendor_responsiveness.py::test_window_cache_respects_ttl - M...
```

</details>

## Recently modified files (likely in scope)

- `apps/backend/app/config.py`
- `apps/backend/app/engine/snapshot.py`
- `apps/backend/app/engine/tape_engine.py`
- `apps/backend/app/main.py`
- `apps/backend/app/providers/historical.py`
- `apps/backend/app/providers/live.py`
- `apps/backend/app/providers/simulated.py`
- `apps/backend/app/serializers.py`
- `apps/backend/app/watch_manager.py`
- `apps/backend/tests/test_history_api.py`

## Suggested next reads (for the dev agent)

1. `tests/test_vendor_responsiveness.py:121` — failing test
2. `tests/test_vendor_responsiveness.py:144` — failing test
3. `tests/test_vendor_responsiveness.py:329` — failing test
4. `apps/backend/app/config.py` — recently modified
5. `apps/backend/app/engine/snapshot.py` — recently modified
6. `apps/backend/app/engine/tape_engine.py` — recently modified
