"""Access the recorded fmriprep compatibility specification."""

from __future__ import annotations

import json
from pathlib import Path

SPEC_PATH = Path(__file__).with_name("fmriprep_spec.json")


def load_spec(path: str | Path | None = None) -> dict:
    with open(path or SPEC_PATH, "r", encoding="utf-8") as handle:
        return json.load(handle)


def stable_version(spec: dict | None = None) -> str:
    return (spec or load_spec())["fmriprep"]["stable_version"]


def confounds_expectations(spec: dict | None = None) -> dict:
    return (spec or load_spec())["confounds"]
