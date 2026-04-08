# Recipe Format Contract (A1)

## Overview

This document defines the exact file format, fields, data types, ranges, and defaults for Domaille recipes used by this project. It is the source of truth for recipe validation and interoperability.

## System Context

The Domaille firmware (likely Pascal or Modula-2 based on `:=` assignment syntax and Hungarian notation) serializes recipe data directly to disk. This format must be preserved exactly for compatibility.

Recipes are referred to as "Processes" in the machine's own terminology. Each process can have multiple steps. Processes are stored internally and can be transferred to/from USB storage. The USB file format is what this project reads and writes.

## Naming Convention (Hungarian Notation)

Based on field prefixes:
- `int*` = Integer
- `str*` = String
- `r*` = Real (floating-point number)

## Recipe File Format

**Location**: `Domaille/Processes/<recipe_name>`  
**Format**: Plain text, key-value pairs with `:=` delimiter, one pair per line  
**Example content**:
```
strRecipeDescription := default recipe
intRecipeNoOfSteps := 3
intRecipeQty := 30
intRecipeReworkStep := 1
```

### Recipe-Level Keys

| Key | Type | Range | Default | Required | Description |
|---|---|---|---|---|---|
| `strRecipeDescription` | string | any | recipe name | yes | Operator-facing recipe label |
| `intRecipeNoOfSteps` | integer | 1-9 | N/A | yes | Number of polishing steps in recipe |
| `intRecipeQty` | integer | 2-32 | varies | yes | Max contacts per fixture for this recipe |
| `intRecipeReworkStep` | integer | 1-9 | 1 | yes | Which step to jump to when "Rework" pressed. Machine executes that step plus all remaining steps, then returns to step 1. |

## Step File Format

**Location**: `Domaille/Processes/Steps/<recipe_name>.NNN` (NNN is zero-padded step number: 001, 002, ..., 099)  
**Format**: Plain text, key-value pairs with `:=` delimiter, one pair per line  
**Example content**:
```
rRecipeStepTime := 25
rRecipeStepSpeed := 110
rRecipeStepSpeedRamp := 1
rRecipeStepPressure := 15
...
```

### Step-Level Keys

| Key | Type | Range | Default | Required | Description |
|---|---|---|---|---|---|
| `rRecipeStepTime` | real | 10-300 | N/A | yes | Step duration in seconds |
| `rRecipeStepSpeed` | real | 0+ | 110 | yes | Platen speed in RPM. Zero speed is valid when "Zero Speed" system setting is enabled. |
| `rRecipeStepSpeedRamp` | real | 0-60 | 1 | yes | Speed ramp-up in seconds: time to ramp from zero RPM to programmed speed at step start. Max 60 seconds. |
| `rRecipeStepPressure` | real | 0-16 | varies | yes | Total load in lbs for all contacts |
| `rRecipeStepPressureRamp` | real | 0-60 | 1 | yes | Pressure ramp-up in seconds: time to ramp from zero to programmed pressure at step start. Max 60 seconds. |
| `rRecipeStepFCI` | integer | 0-99 | 5 or 3 | no | Film Change Interval: number of cycles before machine prompts film replacement. Machine stops next step if count reached. Set to 0 to disable. Non-user-facing in our initial UI. |
| `rRecipeStepLowerSpeedLimit` | real | 0+ | 10 | yes | Lower tolerance bound for speed |
| `rRecipeStepUpperSpeedLimit` | real | 0+ | 10 | yes | Upper tolerance bound for speed |
| `rRecipeStepLowerPressureLimit` | real | 0+ | 0.5 | yes | Lower tolerance bound for pressure (lbs) |
| `rRecipeStepUpperPressureLimit` | real | 0+ | 0.5 | yes | Upper tolerance bound for pressure (lbs) |
| `rRecipeStepFixtureWeight` | real | 0+ | 0 | no | Optional fixture weight correction |
| `intRecipeStepOpCode` | integer | any | 300 | no | Operation code assigned to the polisher and recipe for use with DE DataLink® data collection system. Not required unless DataLink is in use. |
| `strRecipeStepFilm` | string | from inventory | varies | yes | Film consumable name (exact string match required) |
| `strRecipeStepLubricant` | string | from inventory | DI Water | yes | Lubricant consumable name (exact string match required) |
| `strRecipeStepPad` | string | from inventory | 70 Duro Violet | yes | Pad consumable name (exact string match required) |
| `strRecipeStepDescription1` | string | any | N/A | no | Primary description/notes for step |
| `strRecipeStepDescription2` | string | any | N/A | no | Secondary description/notes for step |
| `rRecipeStepSpeedRampDn` | real | 0-60 | 1 | yes | Speed ramp-down in seconds: time to ramp from max speed to stopped at step end. |
| `rRecipeStepPressureRampDn` | real | 0-60 | 1 | yes | Pressure ramp-down in seconds: time to ramp from max pressure to zero at step end. |

## Settings File Format

**Location**: `Domaille/Settings.txt`  
**Format**: CSV-like, first column is inventory type, subsequent columns are options  
**Example**:
```
Max Quantity,72
Film,<None>,Orange 16um,Brown 5um,Purple 1um,Green 0.1um,Clear FOS-22,White Undercut,White Protrusion
Pad,<None>,60 Duro Blue,65 Duro Dark Blue,70 Duro Violet,75 Duro Brown,80 Duro Green,85 Duro Gray,90 Duro Black
Lubricant,<None>,DI Water
```

### Settings Keys

| Line | Format | Description |
|---|---|---|
| Max Quantity | `Max Quantity,<int>` | System-wide max contacts per fixture (current default: 72) |
| Film | `Film,<option1>,<option2>,...` | Valid film consumable options; first option is usually `<None>` |
| Pad | `Pad,<option1>,<option2>,...` | Valid pad consumable options; first option is usually `<None>` |
| Lubricant | `Lubricant,<option1>,<option2>,...` | Valid lubricant consumable options; first option is usually `<None>` |

## Consumables Inventory (Current Defaults)

### Films
- `<None>`
- `Orange 16um`
- `Brown 5um`
- `Purple 1um`
- `Green 0.1um`
- `Clear FOS-22`
- `White Undercut`
- `White Protrusion`

### Pads
- `<None>`
- `60 Duro Blue`
- `65 Duro Dark Blue`
- `70 Duro Violet`
- `75 Duro Brown`
- `80 Duro Green`
- `85 Duro Gray`
- `90 Duro Black`

### Lubricants
- `<None>`
- `DI Water`

## Validation Rules

### Recipe Level
- `intRecipeNoOfSteps` must be 1-9.
- `intRecipeQty` must be 2-32 (practical work limit for 5316/5320).
- `intRecipeReworkStep` must be an integer between 1 and value of `intRecipeNoOfSteps`.
- All required recipe keys must be present in order.

### Step Level
- Must exist for each step number: 1 through `intRecipeNoOfSteps`.
- File naming must be zero-padded: `<recipe_name>.001`, `<recipe_name>.002`, etc.
- `rRecipeStepTime` must be 10-300 seconds.
- `rRecipeStepPressure` must be 0-16 lbs (5316/5320 operating ceiling).
- All `str*` consumable fields must match an entry from Settings.txt inventory (case-sensitive).
- All required step keys must be present in order.

### Cross-File
- Every step file referenced by `intRecipeNoOfSteps` must exist and be readable.
- No orphaned step files should exist (e.g., step 005 when `intRecipeNoOfSteps` is 3).

## Known Unknowns / TBD

- `rRecipeStepFixtureWeight`: exact role in pressure calculation confirmed as fixture weight for Quantity Adjust pressure compensation; units TBD (lbs assumed).
- `intRecipeStepOpCode` valid value set: any integer; only relevant for DE DataLink® data collection. No functional impact on polishing itself.
- FCI = 0: assumed to disable film tracking (machine will not prompt for film change). Confirm exact behavior on machine.

## Default Recipe Example

When a new project is initialized, the following default recipe is created:

**File**: `Domaille/Processes/default`
```
strRecipeDescription := default recipe
intRecipeNoOfSteps := 3
intRecipeQty := 30
intRecipeReworkStep := 1
```

**File**: `Domaille/Processes/Steps/default.001`
```
rRecipeStepTime := 25
rRecipeStepSpeed := 110
rRecipeStepSpeedRamp := 1
rRecipeStepPressure := 15
rRecipeStepPressureRamp := 1
rRecipeStepFCI := 5
rRecipeStepLowerSpeedLimit := 10
rRecipeStepUpperSpeedLimit := 10
rRecipeStepLowerPressureLimit := 0.5
rRecipeStepUpperPressureLimit := 0.5
rRecipeStepFixtureWeight := 0
intRecipeStepOpCode := 300
strRecipeStepFilm := Brown 5um
strRecipeStepLubricant := DI Water
strRecipeStepPad := 70 Duro Violet
strRecipeStepDescription1 := Rough Polish
strRecipeStepDescription2 := Geometry
rRecipeStepSpeedRampDn := 1
rRecipeStepPressureRampDn := 1
```

**File**: `Domaille/Processes/Steps/default.002`
```
rRecipeStepTime := 35
rRecipeStepSpeed := 110
rRecipeStepSpeedRamp := 1
rRecipeStepPressure := 12
rRecipeStepPressureRamp := 1
rRecipeStepFCI := 5
rRecipeStepLowerSpeedLimit := 10
rRecipeStepUpperSpeedLimit := 10
rRecipeStepLowerPressureLimit := 0.5
rRecipeStepUpperPressureLimit := 0.5
rRecipeStepFixtureWeight := 0
intRecipeStepOpCode := 300
strRecipeStepFilm := Purple 1um
strRecipeStepLubricant := DI Water
strRecipeStepPad := 70 Duro Violet
strRecipeStepDescription1 := Medium Polish
rRecipeStepSpeedRampDn := 1
rRecipeStepPressureRampDn := 1
```

**File**: `Domaille/Processes/Steps/default.003`
```
rRecipeStepTime := 35
rRecipeStepSpeed := 110
rRecipeStepSpeedRamp := 1
rRecipeStepPressure := 12
rRecipeStepPressureRamp := 1
rRecipeStepFCI := 3
rRecipeStepLowerSpeedLimit := 10
rRecipeStepUpperSpeedLimit := 10
rRecipeStepLowerPressureLimit := 0.5
rRecipeStepUpperPressureLimit := 0.5
rRecipeStepFixtureWeight := 0
intRecipeStepOpCode := 300
strRecipeStepFilm := Clear FOS-22
strRecipeStepLubricant := DI Water
strRecipeStepPad := 70 Duro Violet
strRecipeStepDescription1 := Final Polish
rRecipeStepSpeedRampDn := 1
rRecipeStepPressureRampDn := 1
```

## References

- [domaille-field-mapping.md](domaille-field-mapping.md) — Operator/manual terminology to field mapping
- [../recipe.py](../recipe.py) — Current implementation (source of truth for defaults)
