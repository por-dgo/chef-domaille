"""Validation for Domaille recipe bundles and machine profiles."""

from __future__ import annotations

from dataclasses import dataclass

from recipe_store import RecipeBundle


PROFILE_5316_5320 = {
    "name": "5316_5320",
    "max_pressure": 16.0,
    "max_qty": 32,
    "max_fci": 99,
    "max_ramp_seconds": 60,
}


@dataclass
class ValidationResult:
    errors: list[str]
    warnings: list[str]

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0


REQUIRED_RECIPE_KEYS = [
    "strRecipeDescription",
    "intRecipeNoOfSteps",
    "intRecipeQty",
    "intRecipeReworkStep",
]

REQUIRED_STEP_KEYS = [
    "rRecipeStepTime",
    "rRecipeStepSpeed",
    "rRecipeStepSpeedRamp",
    "rRecipeStepPressure",
    "rRecipeStepPressureRamp",
    "rRecipeStepLowerSpeedLimit",
    "rRecipeStepUpperSpeedLimit",
    "rRecipeStepLowerPressureLimit",
    "rRecipeStepUpperPressureLimit",
    "rRecipeStepFixtureWeight",
    "strRecipeStepFilm",
    "strRecipeStepLubricant",
    "strRecipeStepPad",
    "rRecipeStepSpeedRampDn",
    "rRecipeStepPressureRampDn",
]

OPTIONAL_STEP_KEYS = [
    "rRecipeStepFCI",
    "intRecipeStepOpCode",
    "strRecipeStepDescription1",
    "strRecipeStepDescription2",
]


def _as_int(data: dict[str, str], key: str, errors: list[str]) -> int | None:
    try:
        return int(data[key])
    except Exception:
        errors.append(f"{key} must be an integer")
        return None


def _as_float(data: dict[str, str], key: str, errors: list[str]) -> float | None:
    try:
        return float(data[key])
    except Exception:
        errors.append(f"{key} must be a number")
        return None


def validate_bundle(bundle: RecipeBundle, profile: dict | None = None) -> ValidationResult:
    profile = profile or PROFILE_5316_5320
    errors: list[str] = []
    warnings: list[str] = []

    for key in REQUIRED_RECIPE_KEYS:
        if key not in bundle.recipe_data:
            errors.append(f"Missing recipe key: {key}")

    if errors:
        return ValidationResult(errors=errors, warnings=warnings)

    step_count = _as_int(bundle.recipe_data, "intRecipeNoOfSteps", errors)
    qty = _as_int(bundle.recipe_data, "intRecipeQty", errors)
    rework = _as_int(bundle.recipe_data, "intRecipeReworkStep", errors)

    if step_count is not None and step_count != len(bundle.steps):
        errors.append(
            f"Recipe step count mismatch: intRecipeNoOfSteps={step_count}, files={len(bundle.steps)}"
        )

    if qty is not None and not (2 <= qty <= profile["max_qty"]):
        errors.append(f"intRecipeQty must be between 2 and {profile['max_qty']}")

    if step_count is not None and rework is not None and not (1 <= rework <= step_count):
        errors.append("intRecipeReworkStep must be between 1 and intRecipeNoOfSteps")

    for idx, step in enumerate(bundle.steps, start=1):
        for key in REQUIRED_STEP_KEYS:
            if key not in step:
                errors.append(f"Step {idx}: Missing key {key}")

        time_value = _as_float(step, "rRecipeStepTime", errors) if "rRecipeStepTime" in step else None
        pressure = _as_float(step, "rRecipeStepPressure", errors) if "rRecipeStepPressure" in step else None

        if time_value is not None and not (10 <= time_value <= 300):
            errors.append(f"Step {idx}: rRecipeStepTime must be between 10 and 300")

        if pressure is not None and not (0 <= pressure <= profile["max_pressure"]):
            errors.append(
                f"Step {idx}: rRecipeStepPressure must be between 0 and {profile['max_pressure']}"
            )

        for ramp_key in ("rRecipeStepSpeedRamp", "rRecipeStepPressureRamp", "rRecipeStepSpeedRampDn", "rRecipeStepPressureRampDn"):
            if ramp_key in step:
                ramp_val = _as_float(step, ramp_key, errors)
                if ramp_val is not None and not (0 <= ramp_val <= profile["max_ramp_seconds"]):
                    errors.append(
                        f"Step {idx}: {ramp_key} must be between 0 and {profile['max_ramp_seconds']}"
                    )

        if "rRecipeStepFCI" in step:
            fci = _as_int(step, "rRecipeStepFCI", errors)
            if fci is not None and not (0 <= fci <= profile["max_fci"]):
                errors.append(f"Step {idx}: rRecipeStepFCI must be between 0 and {profile['max_fci']}")
        else:
            warnings.append(f"Step {idx}: rRecipeStepFCI is missing (allowed)")

    return ValidationResult(errors=errors, warnings=warnings)
