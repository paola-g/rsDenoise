"""Generate a minimal synthetic fmriprep derivatives tree for compatibility tests.

No neuroimaging data is needed: discovery only inspects names, and confounds
tests only inspect the TSV header.  Files are therefore empty placeholders.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "rsdenoise" / "fmriprep_spec.json"

SUBJECT = "01"
SESSION = "A"
RUN = "task-rest_run-1"
SPACE = "MNI152NLin6Asym_res-2"


def _touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch()


def _confounds_columns(spec: dict) -> list[str]:
    expected = spec["confounds"]
    columns = list(expected["core_columns"]) + list(expected["optional_columns"])
    for prefix in expected["component_prefixes"]:
        columns.append(prefix + "00")
        columns.append(prefix + "01")
    return columns


def generate(out_dir: Path, spec: dict) -> None:
    root = out_dir / "fmriprep"
    func = root / f"sub-{SUBJECT}" / f"ses-{SESSION}" / "func"
    anat = root / f"sub-{SUBJECT}" / f"ses-{SESSION}" / "anat"
    stem = f"sub-{SUBJECT}_ses-{SESSION}_{RUN}"

    _touch(func / f"{stem}_space-{SPACE}_desc-preproc_bold.nii.gz")
    _touch(func / f"{stem}_space-{SPACE}_desc-brain_mask.nii.gz")
    _touch(func / f"{stem}_space-fsLR_den-91k_bold.dtseries.nii")
    _touch(func / f"{stem}_hemi-L_space-fsaverage6_bold.func.gii")
    _touch(func / f"{stem}_hemi-R_space-fsaverage6_bold.func.gii")
    _touch(func / f"{stem}_space-fsLR_den-91k_desc-aseg_dseg.nii.gz")
    _touch(func / f"{stem}_space-fsLR_den-91k_desc-aparcaseg_dseg.nii.gz")

    for label in ("WM", "GM", "CSF"):
        _touch(anat / f"sub-{SUBJECT}_space-{SPACE}_label-{label}_probseg.nii.gz")

    columns = _confounds_columns(spec)
    tsv = func / f"{stem}_desc-confounds_timeseries.tsv"
    tsv.parent.mkdir(parents=True, exist_ok=True)
    tsv.write_text("\t".join(columns) + "\n" + "\t".join(["0"] * len(columns)) + "\n",
                   encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--spec", type=Path, default=SPEC_PATH)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    generate(args.out, spec)
    print(f"Generated synthetic fmriprep {spec['fmriprep']['stable_version']} "
          f"fixtures in {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
