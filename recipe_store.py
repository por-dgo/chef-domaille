"""Internal recipe store and transfer adapters for Domaille-compatible files."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from zipfile import ZIP_DEFLATED, ZipFile

from recipe_io import get_recipe_path, get_step_path, read_recipe, read_step, write_recipe, write_step


APP_NAME = "Chef Domaille"
DOMAILLE_DIR_NAME = "Domaille"


@dataclass
class RecipeBundle:
    recipe_name: str
    recipe_data: dict[str, str]
    steps: list[dict[str, str]]


@dataclass
class TransferResult:
    copied: list[str]
    skipped: list[str]


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
            # Create default Settings.txt
            if not self.settings_path.exists():
                settings_content = "\n".join([
                    "strMachineProfile := 5316",
                    "strLanguage := English",
                    "strDefaultUnit := Inches",
                    "",
                ])
                self.settings_path.write_text(settings_content, encoding="utf-8")
            
            # Create default "Sample" recipe (use internal save to avoid re-bootstrapping)
            sample_recipe = RecipeBundle(
                recipe_name="Sample",
                recipe_data={
                    "strRecipeDescription": "Sample glass bead polishing recipe",
                    "intRecipeNoOfSteps": "2",
                    "intRecipeQty": "12",
                    "intRecipeReworkStep": "2",
                },
                steps=[
                    {
                        "rRecipeStepTime": "45",
                        "rRecipeStepSpeed": "150",
                        "rRecipeStepSpeedRamp": "2",
                        "rRecipeStepPressure": "14",
                        "rRecipeStepPressureRamp": "2",
                        "rRecipeStepFCI": "25",
                        "rRecipeStepLowerSpeedLimit": "100",
                        "rRecipeStepUpperSpeedLimit": "200",
                        "rRecipeStepLowerPressureLimit": "10",
                        "rRecipeStepUpperPressureLimit": "16",
                        "rRecipeStepFixtureWeight": "2.5",
                        "intRecipeStepOpCode": "300",
                        "strRecipeStepFilm": "Brown 5µm",
                        "strRecipeStepLubricant": "DI Water",
                        "strRecipeStepPad": "70 Duro Violet",
                        "rRecipeStepSpeedRampDn": "1",
                        "rRecipeStepPressureRampDn": "1",
                    },
                    {
                        "rRecipeStepTime": "30",
                        "rRecipeStepSpeed": "120",
                        "rRecipeStepSpeedRamp": "1",
                        "rRecipeStepPressure": "12",
                        "rRecipeStepPressureRamp": "1",
                        "rRecipeStepFCI": "50",
                        "rRecipeStepLowerSpeedLimit": "80",
                        "rRecipeStepUpperSpeedLimit": "160",
                        "rRecipeStepLowerPressureLimit": "8",
                        "rRecipeStepUpperPressureLimit": "14",
                        "rRecipeStepFixtureWeight": "2.5",
                        "intRecipeStepOpCode": "310",
                        "strRecipeStepFilm": "Red 1µm",
                        "strRecipeStepLubricant": "DI Water + Isopropanol",
                        "strRecipeStepPad": "90 Duro White",
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

        copied: list[str] = []
        skipped: list[str] = []
        for recipe_name in sorted(selected):
            if recipe_name not in available:
                skipped.append(recipe_name)
                continue
            if recipe_name in self.list_recipes() and not overwrite:
                skipped.append(recipe_name)
                continue

            recipe_data = dict(read_recipe(str(source_root), recipe_name))
            step_count = int(recipe_data["intRecipeNoOfSteps"])
            steps = [
                dict(read_step(str(source_root), recipe_name, n))
                for n in range(1, step_count + 1)
            ]
            self.save_bundle(RecipeBundle(recipe_name, recipe_data, steps))
            copied.append(recipe_name)

        return TransferResult(copied=copied, skipped=skipped)

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

        return TransferResult(copied=copied, skipped=skipped)

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
