"""Settings management for consumables and machine configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Iterator


class RecipeSettings:
    """Parse and manage Domaille Settings.txt (CSV format with consumable options)."""

    def __init__(self, settings_path: Path | str):
        self.path = Path(settings_path)

    def read_settings(self) -> dict[str, list[str]]:
        """
        Parse Settings.txt and return a dict of consumable/config categories.
        Format: "CategoryName,option1,option2,..."
        """
        if not self.path.exists():
            return {}
        
        settings = {}
        for line in self.path.read_text(encoding="utf-8").strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            parts = [p.strip() for p in line.split(",")]
            key = parts[0]
            values = parts[1:] if len(parts) > 1 else []
            settings[key] = values
        return settings

    def write_settings(self, settings: dict[str, list[str]]) -> None:
        """Write settings dict to Settings.txt in CSV format."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        lines = []
        for key, values in settings.items():
            csv_line = ",".join([key] + values)
            lines.append(csv_line)
        self.path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def get_consumables(self) -> dict[str, list[str]]:
        """Return only consumable categories (Film, Pad, Lubricant)."""
        all_settings = self.read_settings()
        return {k: v for k, v in all_settings.items() if k in ("Film", "Pad", "Lubricant")}

    def set_consumables(self, consumables: dict[str, list[str]]) -> None:
        """Update consumable options (Film, Pad, Lubricant) while preserving other settings."""
        settings = self.read_settings()
        for key in ("Film", "Pad", "Lubricant"):
            if key in consumables:
                settings[key] = consumables[key]
        self.write_settings(settings)
