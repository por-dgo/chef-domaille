"""Internal recipe store and transfer adapters for Domaille-compatible files."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from zipfile import ZIP_DEFLATED, ZipFile

from recipe_io import get_recipe_path, get_step_path, read_recipe, read_step, write_recipe, write_step
from recipe_settings import RecipeSettings


APP_NAME = "Chef Domaille"
DOMAILLE_DIR_NAME = "Domaille"


@dataclass
class RecipeBundle:
    recipe_name: str
    recipe_data: dict[str, str]
    steps: list[dict[str, str]]


@dataclass
class TransferResult:
    added: list[str]
    updated: list[str]
    skipped: list[str]
    unchanged: list[str]
    settings_added: dict[str, list[str]]

    @property
    def copied(self) -> list[str]:
        """Back-compat: added + updated."""
        return self.added + self.updated


class RecipeStore:
    """AppData-backed store that behaves like machine internal memory."""

    def __init__(self, root: Path | str):
        self.root = Path(root)
        self._bootstrapping = False

    @property
    def domaille_root(self) -> Path:
        return self.root / DOMAILLE_DIR_NAME

    @property
    def processes_dir(self) -> Path:
        return self.domaille_root / "Processes"

    @property
    def steps_dir(self) -> Path:
        return self.processes_dir / "Steps"

    @property
    def settings_path(self) -> Path:
        return self.domaille_root / "Settings.txt"

    @staticmethod
    def default_root() -> Path:
        appdata = os.getenv("APPDATA")
        if appdata:
            return Path(appdata) / APP_NAME
        return Path.home() / "AppData" / "Roaming" / APP_NAME

    def ensure_structure(self) -> None:
        self.steps_dir.mkdir(parents=True, exist_ok=True)
        self._bootstrap_defaults_if_empty()

    def _raw_list_recipes(self) -> list[str]:
        """List recipes without triggering ensure_structure (avoids circular recursion)."""
        if not self.processes_dir.exists():
            return []
        recipes = [
            entry.name
            for entry in self.processes_dir.iterdir()
            if entry.is_file() and entry.name != "Settings.txt"
        ]
        return sorted(recipes)

    def _bootstrap_defaults_if_empty(self) -> None:
        """Load default recipes and settings if store is empty (first run)."""
        if self._bootstrapping:
            return  # Already bootstrapping, prevent re-entry
        
        if self._raw_list_recipes():
            return  # Store already has recipes, skip bootstrap
        
        self._bootstrapping = True
        try:
            # Create default Settings.txt with CSV format
            if not self.settings_path.exists():
                defaults = {
                    "Max Quantity": ["72"],
                    "Film": ["<None>", "Orange 16um", "Brown 5um", "Purple 1um",
                             "Green 0.1um", "Clear FOS-22", "White Undercut",
                             "White Protrusion"],
                    "Pad": ["<None>", "60 Duro Blue", "65 Duro Dark Blue",
                            "70 Duro Violet", "75 Duro Brown", "80 Duro Green",
                            "85 Duro Gray", "90 Duro Black"],
                    "Lubricant": ["<None>", "DI Water"],
                }
                settings = RecipeSettings(self.settings_path)
                settings.write_settings(defaults)
            
            # Create default 3-step recipe matching original recipe.py defaults.
            sample_recipe = RecipeBundle(
                recipe_name="default",
                recipe_data={
                    "strRecipeDescription": "default recipe",
                    "intRecipeNoOfSteps": "3",
                    "intRecipeQty": "30",
                    "intRecipeReworkStep": "1",
                },
                steps=[
                    {
                        "rRecipeStepTime": "25",
                        "rRecipeStepSpeed": "110",
                        "rRecipeStepSpeedRamp": "1",
                        "rRecipeStepPressure": "15",
                        "rRecipeStepPressureRamp": "1",
                        "rRecipeStepFCI": "5",
                        "rRecipeStepLowerSpeedLimit": "10",
                        "rRecipeStepUpperSpeedLimit": "10",
                        "rRecipeStepLowerPressureLimit": "0.5",
                        "rRecipeStepUpperPressureLimit": "0.5",
                        "rRecipeStepFixtureWeight": "0",
                        "intRecipeStepOpCode": "300",
                        "strRecipeStepFilm": "Brown 5um",
                        "strRecipeStepLubricant": "DI Water",
                        "strRecipeStepPad": "70 Duro Violet",
                        "strRecipeStepDescription1": "Rough Polish",
                        "strRecipeStepDescription2": "Geometry",
                        "rRecipeStepSpeedRampDn": "1",
                        "rRecipeStepPressureRampDn": "1",
                    },
                    {
                        "rRecipeStepTime": "35",
                        "rRecipeStepSpeed": "110",
                        "rRecipeStepSpeedRamp": "1",
                        "rRecipeStepPressure": "12",
                        "rRecipeStepPressureRamp": "1",
                        "rRecipeStepFCI": "5",
                        "rRecipeStepLowerSpeedLimit": "10",
                        "rRecipeStepUpperSpeedLimit": "10",
                        "rRecipeStepLowerPressureLimit": "0.5",
                        "rRecipeStepUpperPressureLimit": "0.5",
                        "rRecipeStepFixtureWeight": "0",
                        "intRecipeStepOpCode": "300",
                        "strRecipeStepFilm": "Purple 1um",
                        "strRecipeStepLubricant": "DI Water",
                        "strRecipeStepPad": "70 Duro Violet",
                        "strRecipeStepDescription1": "Medium Polish",
                        "rRecipeStepSpeedRampDn": "1",
                        "rRecipeStepPressureRampDn": "1",
                    },
                    {
                        "rRecipeStepTime": "35",
                        "rRecipeStepSpeed": "110",
                        "rRecipeStepSpeedRamp": "1",
                        "rRecipeStepPressure": "12",
                        "rRecipeStepPressureRamp": "1",
                        "rRecipeStepFCI": "3",
                        "rRecipeStepLowerSpeedLimit": "10",
                        "rRecipeStepUpperSpeedLimit": "10",
                        "rRecipeStepLowerPressureLimit": "0.5",
                        "rRecipeStepUpperPressureLimit": "0.5",
                        "rRecipeStepFixtureWeight": "0",
                        "intRecipeStepOpCode": "300",
                        "strRecipeStepFilm": "Clear FOS-22",
                        "strRecipeStepLubricant": "DI Water",
                        "strRecipeStepPad": "70 Duro Violet",
                        "strRecipeStepDescription1": "Final Polish",
                        "rRecipeStepSpeedRampDn": "1",
                        "rRecipeStepPressureRampDn": "1",
                    },
                ],
            )
            # Direct write without recursion
            write_recipe(str(self.domaille_root), sample_recipe.recipe_name, sample_recipe.recipe_data)
            for index, step_data in enumerate(sample_recipe.steps, start=1):
                write_step(str(self.domaille_root), sample_recipe.recipe_name, index, step_data)
        finally:
            self._bootstrapping = False

    def list_recipes(self) -> list[str]:
        self.ensure_structure()
        recipes = [
            entry.name
            for entry in self.processes_dir.iterdir()
            if entry.is_file() and entry.name != "Settings.txt"
        ]
        return sorted(recipes)

    def load_bundle(self, recipe_name: str) -> RecipeBundle:
        recipe_data = dict(read_recipe(str(self.domaille_root), recipe_name))
        step_count = int(recipe_data["intRecipeNoOfSteps"])
        steps: list[dict[str, str]] = []
        for step_number in range(1, step_count + 1):
            steps.append(dict(read_step(str(self.domaille_root), recipe_name, step_number)))
        return RecipeBundle(recipe_name=recipe_name, recipe_data=recipe_data, steps=steps)

    def save_bundle(self, bundle: RecipeBundle) -> None:
        self.ensure_structure()
        write_recipe(str(self.domaille_root), bundle.recipe_name, bundle.recipe_data)
        for index, step_data in enumerate(bundle.steps, start=1):
            write_step(str(self.domaille_root), bundle.recipe_name, index, step_data)

    def delete_recipe(self, recipe_name: str) -> None:
        recipe_path = get_recipe_path(str(self.domaille_root), recipe_name)
        if recipe_path.exists():
            recipe_path.unlink()
        for step_file in self.steps_dir.glob(f"{recipe_name}.*"):
            step_file.unlink()

    def import_from_domaille_folder(
        self,
        source_domaille_root: Path | str,
        selected_recipes: Iterable[str] | None = None,
        overwrite: bool = False,
    ) -> TransferResult:
        source_root = Path(source_domaille_root)
        source_processes = source_root / "Processes"
        source_steps = source_processes / "Steps"
        if not source_processes.exists() or not source_steps.exists():
            raise FileNotFoundError("Source path is not a valid Domaille folder")

        available = [entry.name for entry in source_processes.iterdir() if entry.is_file()]
        selected = set(selected_recipes or available)

        added: list[str] = []
        updated: list[str] = []
        skipped: list[str] = []
        unchanged: list[str] = []
        existing_recipes = self.list_recipes()

        for recipe_name in sorted(selected):
            if recipe_name not in available:
                skipped.append(recipe_name)
                continue

            recipe_data = dict(read_recipe(str(source_root), recipe_name))
            step_count = int(recipe_data["intRecipeNoOfSteps"])
            steps = [
                dict(read_step(str(source_root), recipe_name, n))
                for n in range(1, step_count + 1)
            ]
            incoming = RecipeBundle(recipe_name, recipe_data, steps)

            # Validate before importing
            from recipe_validation import validate_bundle
            result = validate_bundle(incoming)
            if not result.ok:
                skipped.append(recipe_name)
                continue

            if recipe_name not in existing_recipes:
                self.save_bundle(incoming)
                added.append(recipe_name)
            elif not overwrite:
                skipped.append(recipe_name)
            else:
                # Compare to existing
                existing = self.load_bundle(recipe_name)
                if existing.recipe_data == incoming.recipe_data and existing.steps == incoming.steps:
                    unchanged.append(recipe_name)
                else:
                    self.save_bundle(incoming)
                    updated.append(recipe_name)

        # Merge settings (consumables) from source, case-insensitive dedup
        source_settings_path = source_root / "Settings.txt"
        settings_added: dict[str, list[str]] = {}
        if source_settings_path.exists():
            settings_added = self._merge_settings(source_settings_path)

        return TransferResult(added=added, updated=updated, skipped=skipped, unchanged=unchanged, settings_added=settings_added)

    def _merge_settings(self, source_settings_path: Path) -> dict[str, list[str]]:
        """Merge consumable lists from source into local settings (case-insensitive dedup).
        Returns a dict of category -> list of newly added values."""
        source = RecipeSettings(source_settings_path)
        local = RecipeSettings(self.settings_path)
        source_data = source.read_settings()
        local_data = local.read_settings()

        added: dict[str, list[str]] = {}
        for key in ("Film", "Pad", "Lubricant"):
            incoming = source_data.get(key, [])
            existing = local_data.get(key, [])
            seen = {v.lower() for v in existing}
            merged = list(existing)
            new_values: list[str] = []
            for value in incoming:
                if value.lower() not in seen:
                    seen.add(value.lower())
                    merged.append(value)
                    new_values.append(value)
            local_data[key] = merged
            if new_values:
                added[key] = new_values

        local.write_settings(local_data)
        return added

    def export_to_domaille_folder(
        self,
        destination_domaille_root: Path | str,
        selected_recipes: Iterable[str],
        include_settings: bool = True,
    ) -> TransferResult:
        destination_root = Path(destination_domaille_root)
        destination_steps = destination_root / "Processes" / "Steps"
        destination_steps.mkdir(parents=True, exist_ok=True)

        copied: list[str] = []
        skipped: list[str] = []
        selected = list(selected_recipes)

        for recipe_name in selected:
            if recipe_name not in self.list_recipes():
                skipped.append(recipe_name)
                continue
            bundle = self.load_bundle(recipe_name)
            write_recipe(str(destination_root), recipe_name, bundle.recipe_data)
            for idx, step in enumerate(bundle.steps, start=1):
                write_step(str(destination_root), recipe_name, idx, step)
            copied.append(recipe_name)

        if include_settings and self.settings_path.exists():
            settings_dest = destination_root / "Settings.txt"
            settings_dest.parent.mkdir(parents=True, exist_ok=True)
            settings_dest.write_text(self.settings_path.read_text(encoding="utf-8"), encoding="utf-8")

        return TransferResult(added=copied, updated=[], skipped=skipped, unchanged=[], settings_added={})

    def export_to_zip(
        self,
        zip_path: Path | str,
        selected_recipes: Iterable[str],
        include_settings: bool = True,
    ) -> TransferResult:
        temp_root = self.root / "_zip_export_temp"
        if temp_root.exists():
            for item in temp_root.rglob("*"):
                if item.is_file():
                    item.unlink()
            for item in sorted(temp_root.rglob("*"), reverse=True):
                if item.is_dir():
                    item.rmdir()

        temp_domaille = temp_root / DOMAILLE_DIR_NAME
        result = self.export_to_domaille_folder(temp_domaille, selected_recipes, include_settings)

        zip_target = Path(zip_path)
        zip_target.parent.mkdir(parents=True, exist_ok=True)
        with ZipFile(zip_target, "w", compression=ZIP_DEFLATED) as archive:
            for file in temp_root.rglob("*"):
                if file.is_file():
                    archive.write(file, arcname=file.relative_to(temp_root))

        for item in temp_root.rglob("*"):
            if item.is_file():
                item.unlink()
        for item in sorted(temp_root.rglob("*"), reverse=True):
            if item.is_dir():
                item.rmdir()
        if temp_root.exists():
            temp_root.rmdir()

        return result

    def import_from_zip(
        self,
        zip_path: Path | str,
        selected_recipes: Iterable[str] | None = None,
        overwrite: bool = False,
    ) -> TransferResult:
        extract_root = self.root / "_zip_import_temp"
        if extract_root.exists():
            for item in extract_root.rglob("*"):
                if item.is_file():
                    item.unlink()
            for item in sorted(extract_root.rglob("*"), reverse=True):
                if item.is_dir():
                    item.rmdir()

        extract_root.mkdir(parents=True, exist_ok=True)
        with ZipFile(zip_path, "r") as archive:
            archive.extractall(extract_root)

        domaille_root = extract_root / DOMAILLE_DIR_NAME
        result = self.import_from_domaille_folder(domaille_root, selected_recipes, overwrite=overwrite)

        for item in extract_root.rglob("*"):
            if item.is_file():
                item.unlink()
        for item in sorted(extract_root.rglob("*"), reverse=True):
            if item.is_dir():
                item.rmdir()
        if extract_root.exists():
            extract_root.rmdir()

        return result
