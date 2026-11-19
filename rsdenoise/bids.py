"""Dependency-light discovery of BIDS Derivatives files.

The original code assembled fmriprep filenames from a single hard-coded
template.  That broke whenever fmriprep changed an entity, a suffix, or the
confounds filename.  This module instead discovers files by BIDS entities and
ranks the candidates, so more than one fmriprep generation can be read.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

_EXTENSIONS = {".gz", ".nii", ".gii", ".tsv", ".json", ".csv"}
_ENTITY_RE = re.compile(r"^([A-Za-z][A-Za-z0-9]*)-(.+)$")


def strip_extensions(name: str) -> str:
    """Return a filename without any chain of known extensions."""
    while True:
        stem, ext = os.path.splitext(name)
        if ext.lower() in _EXTENSIONS:
            name = stem
        else:
            return name


def parse_entities(name: str) -> dict[str, str]:
    """Parse BIDS entities from a filename.  The suffix is stored as ``suffix``."""
    entities: dict[str, str] = {}
    for part in strip_extensions(Path(name).name).split("_"):
        match = _ENTITY_RE.match(part)
        if match:
            entities[match.group(1)] = match.group(2)
        else:
            entities["suffix"] = part
    return entities


def substitute_template(template: str, subject: str, fmri_run: str,
                        session: str | None = None) -> str:
    """Expand the legacy ``#...#`` placeholders used in older notebooks."""
    if session:
        template = template.replace("#fMRIsession#", session)
    else:
        template = re.sub(r"_?ses-#fMRIsession#", "", template)
        template = template.replace("#fMRIsession#_", "")
    result = template.replace("#subjectID#", subject).replace("#fMRIrun#", fmri_run)
    return result.replace("__", "_").strip("_")


def resolve_data_root(data_dir: str | os.PathLike) -> Path:
    """Accept an fmriprep derivatives root or a parent of one."""
    root = Path(data_dir)
    if any(root.glob("sub-*")):
        return root
    for name in ("fmriprep", "derivatives"):
        candidate = root / name
        if candidate.is_dir() and any(candidate.glob("sub-*")):
            return candidate
    if (root / "fmriprep").is_dir():
        return root / "fmriprep"
    return root


def _subject_dir(root: Path, subject: str, session: str | None) -> Path:
    name = subject if str(subject).startswith("sub-") else f"sub-{subject}"
    path = root / name
    if session:
        ses = session if str(session).startswith("ses-") else f"ses-{session}"
        path = path / ses
    return path


def _func_dir(root: Path, subject: str, session: str | None) -> Path:
    path = _subject_dir(root, subject, session) / "func"
    if not path.is_dir() and session:
        # Some derivatives omit the session level for functional data.
        path = _subject_dir(root, subject, None) / "func"
    return path


def _run_value(fmri_run: str) -> str:
    match = re.search(r"(?:^|_)run-(\d+)$", fmri_run)
    return match.group(1) if match else fmri_run.removeprefix("run-")


def _entity_matches(entities: dict[str, str], subject: str, fmri_run: str,
                    session: str | None) -> bool:
    sub = subject.removeprefix("sub-")
    run = _run_value(fmri_run)
    if "sub" in entities and entities["sub"] != sub:
        return False
    if session and "ses" in entities:
        ses = session.removeprefix("ses-")
        if entities["ses"] != ses:
            return False
    if "run" in entities:
        value = entities["run"]
        if value != run and value != run.zfill(2):
            return False
    return True


def _space_matches(entities: dict[str, str], space: str) -> bool:
    """Accept both ``space-X_res-Y`` and separate ``space-X``/``res-Y`` entities."""
    parts = space.split("_")
    if parts and not parts[0].startswith(("space-", "res-")):
        parts[0] = f"space-{parts[0]}"
    space_part = next((p for p in parts if p.startswith("space-")), None)
    res_part = next((p for p in parts if p.startswith("res-")), None)
    if space_part and entities.get("space") != space_part.removeprefix("space-"):
        return False
    if res_part and entities.get("res") and entities["res"] != res_part.removeprefix("res-"):
        return False
    return True


def _candidate_patterns(is_cifti: bool, is_gifti: bool) -> tuple[str, ...]:
    if is_cifti:
        return ("*_bold.dtseries.nii*", "*_Atlas*.dtseries.nii*", "*.dtseries.nii*")
    if is_gifti:
        return ("*_hemi-L*_bold.func.gii", "*_bold.func.gii", "*.func.gii")
    return ("*_desc-preproc_bold.nii*", "*_desc-aggrDenoised_bold.nii*",
            "*_desc-nonaggrDenoised_bold.nii*",
            "*_desc-orthaggrDenoised_bold.nii*", "*_bold.nii*", "*.nii*")


def find_bold_file(data_dir: str | os.PathLike, subject: str, fmri_run: str,
                   *, session: str | None = None, space: str | None = None,
                   is_cifti: bool = False, is_gifti: bool = False,
                   template: str | None = None) -> Path | None:
    """Find the preprocessed BOLD file, preferring BIDS-normal naming."""
    root = resolve_data_root(data_dir)
    if template:
        candidate = root / substitute_template(template, subject, fmri_run, session)
        return candidate if candidate.is_file() else None

    func_dir = _func_dir(root, subject, session)
    if not func_dir.is_dir():
        return None

    candidates: list[Path] = []
    for pattern in _candidate_patterns(is_cifti, is_gifti):
        candidates.extend(p for p in func_dir.glob(pattern) if p.is_file())
    candidates = list(dict.fromkeys(candidates))

    matching = []
    for path in candidates:
        entities = parse_entities(path.name)
        if not _entity_matches(entities, subject, fmri_run, session):
            continue
        description = entities.get("desc")
        allowed = {"preproc", "Atlas", "MSMAll", "aggrDenoised",
                   "nonaggrDenoised", "orthaggrDenoised"}
        if description and description not in allowed:
            continue
        matching.append((path, entities))

    if not matching:
        return None

    def rank(item: tuple[Path, dict[str, str]]):
        path, entities = item
        desc = entities.get("desc")
        return (
            0 if desc == "preproc" else 1,
            0 if space and _space_matches(entities, space) else 1,
            0 if "run" in entities else 1,
            0 if "ses" in entities else 1,
            len(path.name),
        )

    return min(matching, key=rank)[0]


_CONFOUNDS_PATTERNS = (
    "*_desc-confounds_timeseries.tsv",
    "*_desc-confounds_regressors.tsv",
    "*_confounds_timeseries.tsv",
    "*_confounds_regressors.tsv",
    "*_confounds.tsv",
)


def find_confounds_file(data_dir: str | os.PathLike, subject: str, fmri_run: str,
                        *, session: str | None = None) -> Path | None:
    """Find a confounds TSV across fmriprep naming generations."""
    func_dir = _func_dir(resolve_data_root(data_dir), subject, session)
    if not func_dir.is_dir():
        return None
    for pattern in _CONFOUNDS_PATTERNS:
        for path in sorted(func_dir.glob(pattern)):
            entities = parse_entities(path.name)
            if _entity_matches(entities, subject, fmri_run, session):
                return path
    return None


def find_aroma_confounds_file(data_dir: str | os.PathLike, subject: str,
                              fmri_run: str,
                              *, session: str | None = None) -> Path | None:
    """Find noise-component time series from a fmripost-aroma derivatives tree."""
    func_dir = _func_dir(resolve_data_root(data_dir), subject, session)
    if not func_dir.is_dir():
        return None
    for pattern in ("*_desc-aroma_timeseries.tsv", "*_aroma_timeseries.tsv"):
        for path in sorted(func_dir.glob(pattern)):
            if _entity_matches(parse_entities(path.name), subject, fmri_run, session):
                return path
    return None


def find_probseg_file(data_dir: str | os.PathLike, subject: str,
                      *, session: str | None = None, space: str | None = None,
                      label: str = "WM") -> Path | None:
    """Find a tissue probability segmentation for any fmriprep resolution."""
    root = resolve_data_root(data_dir)
    sub_dir = _subject_dir(root, subject, session)
    # probsegs live in the session's anat/ when a session is given; some
    # derivatives also keep a session-less subject-level anat/.
    anat_dirs = [sub_dir / "anat",
                 _subject_dir(root, subject, None) / "anat",
                 sub_dir]
    matches: list[Path] = []
    for directory in anat_dirs:
        if directory.is_dir():
            matches.extend(directory.glob(f"*_label-{label}_probseg.nii*"))
    if not matches:
        return None
    if space:
        exact = [p for p in matches if f"space-{space}" in p.name]
        if exact:
            return sorted(exact)[0]
    return sorted(matches)[0]


def find_aseg_file(data_dir: str | os.PathLike, subject: str,
                   *, session: str | None = None,
                   space: str | None = None) -> Path | None:
    """Find a FreeSurfer ``aseg`` segmentation written into fmriprep space."""
    root = resolve_data_root(data_dir)
    sub_dir = _subject_dir(root, subject, session)
    directories = [sub_dir / "func", sub_dir / "anat", sub_dir]
    matches: list[Path] = []
    for directory in directories:
        if directory.is_dir():
            matches.extend(directory.glob("*desc-aseg_dseg.nii*"))
    if not matches:
        return None
    if space:
        exact = [p for p in matches if f"space-{space}" in p.name]
        if exact:
            return sorted(exact)[0]
    return sorted(matches)[0]
