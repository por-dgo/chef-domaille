"""I/O helpers for Domaille recipe and step files."""

from collections import OrderedDict
from pathlib import Path
from typing import Mapping


KV_SEPARATOR = " := "


def get_recipe_path(root: str, recipe_name: str) -> Path:
    return Path(root) / "Processes" / recipe_name


def get_step_path(root: str, recipe_name: str, step_number: int) -> Path:
    return Path(root) / "Processes" / "Steps" / f"{recipe_name}.{step_number:03d}"


def parse_kv_line(line: str) -> tuple[str, str]:
    if KV_SEPARATOR not in line:
        raise ValueError(f"Invalid key/value line: {line!r}")
    key, value = line.rstrip("\n").split(KV_SEPARATOR, 1)
    return key.strip(), value


def read_kv_file(path: Path) -> OrderedDict[str, str]:
    data: OrderedDict[str, str] = OrderedDict()
    with path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            if not raw_line.strip():
                continue
            key, value = parse_kv_line(raw_line)
            data[key] = value
    return data


def write_kv_file(path: Path, data: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for key, value in data.items():
            handle.write(f"{key}{KV_SEPARATOR}{value}\n")


def read_recipe(root: str, recipe_name: str) -> OrderedDict[str, str]:
    return read_kv_file(get_recipe_path(root, recipe_name))


def write_recipe(root: str, recipe_name: str, data: Mapping[str, object]) -> None:
    write_kv_file(get_recipe_path(root, recipe_name), data)


def read_step(root: str, recipe_name: str, step_number: int) -> OrderedDict[str, str]:
    return read_kv_file(get_step_path(root, recipe_name, step_number))


def write_step(
    root: str,
    recipe_name: str,
    step_number: int,
    data: Mapping[str, object],
) -> None:
    write_kv_file(get_step_path(root, recipe_name, step_number), data)


def serialize_kv_lines(data: Mapping[str, object]) -> list[str]:
    return [f"{key}{KV_SEPARATOR}{value}\n" for key, value in data.items()]
