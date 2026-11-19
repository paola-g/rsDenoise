"""Read and validate fmriprep confounds TSVs.

Column lookup is by name (with aliases for older/newer fmriprep generations)
rather than by position, and component columns are ordered by their numeric
suffix instead of by their order in the file.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Iterable

_MISSING = {"", "n/a", "na", "nan", "none", "null"}


class ConfoundsError(ValueError):
    """Raised when a confounds file lacks a regressor the pipeline needs."""


# Canonical name -> accepted spellings across fmriprep releases.
ALIASES: dict[str, tuple[str, ...]] = {
    "framewise_displacement": ("framewise_displacement", "fd"),
    "dvars": ("dvars",),
    "std_dvars": ("std_dvars", "standardized_dvars"),
    "csf": ("csf",),
    "white_matter": ("white_matter", "wm"),
    "global_signal": ("global_signal", "gs"),
    "trans_x": ("trans_x", "mov-x", "motion_x"),
    "trans_y": ("trans_y", "mov-y", "motion_y"),
    "trans_z": ("trans_z", "mov-z", "motion_z"),
    "rot_x": ("rot_x", "rot-x", "motion_rot_x"),
    "rot_y": ("rot_y", "rot-y", "motion_rot_y"),
    "rot_z": ("rot_z", "rot-z", "motion_rot_z"),
    "aroma": ("aroma_motion__*",),
    "a_comp_cor": ("a_comp_cor_*",),
    "t_comp_cor": ("t_comp_cor_*",),
    "cosine": ("cosine*", "cos_*"),
}

MOTION_COLUMNS = ("trans_x", "trans_y", "trans_z", "rot_x", "rot_y", "rot_z")

# Families whose columns are numbered by the data and may appear out of order.
COMPONENT_PREFIXES = (
    "a_comp_cor_", "c_comp_cor_", "w_comp_cor_", "t_comp_cor_",
    "edge_comp_", "cosine", "non_steady_state_outlier", "motion_outlier",
    "aroma_motion__",
)


def canonicalize_column_names(columns: Iterable[str]) -> list[str]:
    """Rename known aliases to the names the pipeline expects."""
    reverse: dict[str, str] = {}
    for canonical, aliases in ALIASES.items():
        for alias in aliases:
            if not alias.endswith("*"):
                reverse[alias] = canonical
    return [reverse.get(name, name) for name in columns]


def _component_key(name: str) -> tuple[str, int]:
    match = re.search(r"(\d+)$", name)
    prefix = name[:match.start()] if match else name
    return (prefix, int(match.group(1)) if match else -1)


def order_component_columns(columns: Iterable[str]) -> list[str]:
    """Sort numbered component columns by suffix without moving other columns."""
    result = list(columns)
    indices = [
        i for i, name in enumerate(result)
        if any(name.startswith(prefix) for prefix in COMPONENT_PREFIXES)
    ]
    names = sorted((result[i] for i in indices), key=_component_key)
    for index, name in zip(indices, names):
        result[index] = name
    return result


def _to_float(value: str) -> float:
    value = value.strip()
    if value.lower() in _MISSING:
        return 0.0
    try:
        return float(value)
    except ValueError:
        return 0.0


def _numeric_suffix(name: str, prefix: str) -> tuple[int, str]:
    match = re.search(r"(\d+)$", name[len(prefix):])
    return (int(match.group(1)) if match else -1, name)


class Confounds:
    """A parsed confounds TSV with name-based access."""

    def __init__(self, path: str | Path, columns: list[str], rows: list[list[float]]):
        self.path = Path(path)
        self.columns = columns
        self.rows = rows
        self.n_volumes = len(rows)

    @classmethod
    def read(cls, path: str | Path) -> "Confounds":
        with open(path, "r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.reader(handle, delimiter="\t")
            try:
                columns = next(reader)
            except StopIteration as exc:
                raise ConfoundsError(f"Empty confounds file: {path}") from exc
            columns = [c.strip().lstrip("\ufeff") for c in columns]
            rows = [
                [_to_float(value) for value in row[:len(columns)]]
                for row in reader
            ]
            rows = [row + [0.0] * (len(columns) - len(row)) for row in rows]
        return cls(path, columns, rows)

    def find(self, pattern: str) -> list[str]:
        """Return matching columns, sorted by numeric suffix then name."""
        if pattern.endswith("*"):
            prefix = pattern[:-1]
            matches = [c for c in self.columns if c.startswith(prefix)]
            return sorted(matches, key=lambda c: _numeric_suffix(c, prefix))
        return [c for c in self.columns if c == pattern]

    def resolve(self, canonical: str) -> str | None:
        """Return the actual column name for a canonical regressor."""
        for candidate in ALIASES.get(canonical, (canonical,)):
            matches = self.find(candidate)
            if matches:
                return matches[0]
        return None

    def column(self, canonical: str) -> list[float]:
        """Return values for a canonical regressor, or a clear error."""
        name = self.resolve(canonical)
        if name is None:
            raise ConfoundsError(
                f"Confounds file {self.path} has no '{canonical}' column. "
                f"Available columns: {', '.join(self.columns)}"
            )
        index = self.columns.index(name)
        return [row[index] for row in self.rows]

    def validate(self, required: Iterable[str]) -> None:
        """Raise one error listing every missing required regressor."""
        missing = [name for name in required if self.resolve(name) is None]
        if missing:
            raise ConfoundsError(
                f"Confounds file {self.path} is missing required columns: "
                f"{', '.join(missing)}. Available columns: {', '.join(self.columns)}"
            )

    def motion(self) -> list[list[float]]:
        """Return the six translation/rotation regressors in canonical order."""
        self.validate(MOTION_COLUMNS)
        return [self.column(name) for name in MOTION_COLUMNS]

    def component_columns(self, kind: str = "a_comp_cor", limit: int | None = None) -> list[str]:
        """Return component columns ordered by component number."""
        columns = self.find(ALIASES.get(kind, (kind + "_*",))[0])
        return columns[:limit] if limit is not None else columns

    def cosine_columns(self) -> list[str]:
        columns: list[str] = []
        for pattern in ALIASES["cosine"]:
            for name in self.find(pattern):
                if name not in columns:
                    columns.append(name)
        return columns
