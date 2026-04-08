# Domaille Field Mapping (A4)

## Scope

- Primary machine context: APM-HDC-5320 and APM-HDC-5316 (same workflow, 5316 max pressure 16 lbs)
- Secondary/supporting reference: APM-HDC-5400 manual
- Goal: map manual terminology and operator concepts to current recipe file keys used by this project

## Source Manuals

- `docs/APM-HDC-5320-Polishing-Machine-User-Manual.pdf`
- `docs/APM-HDC-5400-Polishing-Machine-User-Manual.pdf`
- 5400 source URL: https://www.domailleengineering.com/wp-content/uploads/2023/03/APM-HDC-5400-Polishing-Machine-User-Manual.pdf
- Retrieval date recorded for this mapping: 2026-04-08

## Project Baseline

This mapping is based on the currently implemented file format in `recipe.py` and generated files under:

- `Domaille/Processes/<recipe_name>`
- `Domaille/Processes/Steps/<recipe_name>.NNN`

## Manual Concept -> Recipe Key Crosswalk

| Manual concept (operator view) | Recipe key(s) in files | Current project behavior | Notes |
|---|---|---|---|
| Recipe description/name | `strRecipeDescription` | Stored in process file; defaults to recipe name in new recipe flow | Machine UI label may differ in wording; behavior aligns |
| Number of steps | `intRecipeNoOfSteps` | User enters 1-9 in current CLI | Current script enforces 1-9 even though file naming can support more |
| Contact quantity / max quantity | `intRecipeQty` and `Settings.txt: Max Quantity` | `intRecipeQty` currently validated 2-72; practical fixture max should be 32 contacts | For 5320/5316 operations, set project max to 32 contacts in future validation update |
| Rework step | `intRecipeReworkStep` | Usually keep default as `1` (optionally `2`) | Defines which step machine jumps to when operator presses Rework; low-priority feature for this team |
| Step duration | `rRecipeStepTime` | Validated 10-300 seconds in current CLI | Confirm manual-recommended range by recipe type |
| Platen/head speed | `rRecipeStepSpeed` | Defaults to 110 in current generated files | Speed in RPM per manual. Zero is valid when "Zero Speed" system config option is enabled. |
| Speed ramp up | `rRecipeStepSpeedRamp` | Defaults to 1 | Seconds to ramp from 0 RPM to programmed speed at step start. Max 60 seconds per manual. |
| Pressure (total load) | `rRecipeStepPressure` | Validated 0-16 lbs in current CLI | Keep 16 lbs max for 5320/5316 usage (approximately 0.5 lbs/contact at 32 contacts) |
| Pressure ramp up | `rRecipeStepPressureRamp` | Defaults to 1 | Seconds to ramp from 0 to programmed pressure at step start. Max 60 seconds per manual. |
| FCI parameter | `rRecipeStepFCI` | Default currently set in script but should be non-user-facing | FCI = Film Change Interval; machine tracks film uses and stops next step when count reached. Max 99. In practice, operators at DGO change film by visual inspection, so this is non-user-facing in our UI. |
| Speed tolerance limits | `rRecipeStepLowerSpeedLimit`, `rRecipeStepUpperSpeedLimit` | Defaults 10 and 10 | Limit interpretation needs manual confirmation |
| Pressure tolerance limits | `rRecipeStepLowerPressureLimit`, `rRecipeStepUpperPressureLimit` | Defaults 0.5 and 0.5 | Units and pass/fail behavior need confirmation |
| Fixture weight | `rRecipeStepFixtureWeight` | Defaults to 0 | May be optional or machine-dependent |
| Operation code | `intRecipeStepOpCode` | Defaults to 300 in current files | Used only with DE DataLink® data collection accessory. Any integer valid. No impact on polishing behavior. |
| Consumable: film | `strRecipeStepFilm`, `Settings.txt: Film` | Selected from configured film list | Keep exact string values for compatibility |
| Consumable: lubricant | `strRecipeStepLubricant`, `Settings.txt: Lubricant` | Default DI Water | Keep exact string values for compatibility |
| Consumable: pad | `strRecipeStepPad`, `Settings.txt: Pad` | Default 70 Duro Violet | Keep exact string values for compatibility |
| Step description fields | `strRecipeStepDescription1`, `strRecipeStepDescription2` | Optional descriptive text for operator context | Secondary description not always present |
| Speed ramp down | `rRecipeStepSpeedRampDn` | Defaults to 1 | Seconds to ramp from max speed to stopped at step end. |
| Pressure ramp down | `rRecipeStepPressureRampDn` | Defaults to 1 | Seconds to ramp from max pressure to zero at step end. |

## Known Unknowns (Flagged)

- `intRecipeStepOpCode`: used exclusively with DE DataLink® data collection system accessory; no polishing impact. Any integer is valid. Project uses 300 as a safe default.
- `rRecipeStepFCI` when set to 0: assumed to disable film tracking. Exact machine behavior when field is missing (vs 0) is unconfirmed.
- Speed/pressure limit fields (`Lower/Upper*Limit`): exact machine behavior (alarm threshold, tolerance band, or control loop bound).
- Ramp fields (`*Ramp`, `*RampDn`): exact units may vary by machine software/firmware version; unsupported fields may be ignored by some machines.

## Discrepancies / Model Notes

- Current project validation uses max pressure 16 lbs (`rRecipeStepPressure <= 16`), which matches current 5320/5316 usage target.
- Working operational assumption: max fixture contacts should be 32, with approximately 0.5 lbs/contact as practical upper rule.
- 5400 manual may describe higher allowable pressure (commonly 20 lbs class). Treat 5400 values as supplemental reference only unless fleet changes.
- If future support for 5400 pressure ranges is required, model-aware validation should be introduced instead of changing 5320/5316 defaults globally.

## Project Defaults (Current Direction)

- `intRecipeReworkStep`: default to `1` (option to consider `2` if process owner prefers).
- `intRecipeStepOpCode`: keep at `300` until official mapping is available.
- `rRecipeStepFCI`: do not expose as user-editable in UI for initial release.
- Ramp fields: keep in file format for compatibility, but treat advanced ramp tuning as optional/non-core UI initially.
- Pressure validation profile: 0 to 16 lbs for 5316/5320 deployments.
- Contact quantity validation target: 2 to 32 for production usage profile.

## Compatibility Behavior Note

- Ramp capability appears to depend on machine software/firmware version.
- Operational observation: unrecognized fields are typically ignored by machine software.
- Therefore, preserve ramp fields in saved files for forward/backward compatibility, even when specific machines do not apply them.

## Next Validation Tasks

1. Validate `intRecipeStepOpCode` meaning and any non-300 values with hardware/process owner.
2. Verify machine behavior when `rRecipeStepFCI` is set to 0 or omitted.
3. Confirm and implement production profile limits: pressure <= 16 and quantity <= 32.
4. Confirm whether step-count limit should remain 1-9 or be extended.
5. Document any model-specific validation profile (5316/5320 vs 5400) before GUI rollout.
