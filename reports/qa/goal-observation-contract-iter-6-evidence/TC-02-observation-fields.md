# J-02 Evidence: Observation Time/Availability Fields

## Browser Verification of `/tape/SIM-BIDABS/observation` JSON

Timestamp of verification: 2026-09-05 02:54:55 UTC

### Required Fields (Per J-02 Acceptance)

- **observed_at_utc**: `2024-01-02T14:55:24.500000Z`
  - Historical timestamp when the observation was made in the simulated data

- **available_at_utc**: `null`
  - Null for simulated data (not applicable)

- **availability_basis**: `simulated_not_applicable`
  - Indicates this is simulated data with no real availability timestamp

- **timing.settled_at_utc**: `2026-09-05T02:53:18.165750Z`
  - Settled timestamp when the event/state became final

- **generated_at_utc**: `2026-09-05T02:54:55.920370Z`
  - Time when this observation snapshot was generated/computed

## Observation Contract v1 Compliance

✓ All five fields present and properly populated
✓ Time contract satisfied: observed < settled < generated (for simulated scenario)
✓ Availability contract satisfied: basis explains the null available_at_utc
✓ Generated timestamp reflects real-time generation (2026-09-05)
