"""Apply a compatibility-probe report to the repo for human review.

Called by the release-watch workflow.  It deliberately does NOT guess how new
confounds columns map to pipeline operations; it records them as pending and
writes a report so the PR is a reviewable proposal, not a silent code change.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "rsdenoise" / "fmriprep_spec.json"
REPORT_PATH = ROOT / "docs" / "fmriprep-compat-report.md"


def apply(report: dict, spec_path: Path = SPEC_PATH,
          report_path: Path = REPORT_PATH) -> None:
    spec = json.loads(spec_path.read_text(encoding="utf-8"))

    if report.get("version_changed"):
        spec["fmriprep"]["stable_version"] = report["new_version"]
        spec["fmriprep"]["last_probed"] = report["new_version"]

    pending = set(spec["confounds"].get("pending_prefixes", []))
    pending.update(report.get("new_prefixes", []))
    if pending:
        spec["confounds"]["pending_prefixes"] = sorted(pending)

    if report.get("filename_changed") and report.get("confounds_suffix"):
        pattern = f"*_desc-confounds_{report['confounds_suffix']}.tsv"
        patterns = spec["file_patterns"]["confounds"]
        if pattern not in patterns:
            patterns.insert(0, pattern)

    spec_path.write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# fMRIPrep compatibility report",
        "",
        f"- Recorded version: `{report['recorded_version']}`",
        f"- Detected stable version: `{report['new_version']}`",
        f"- Confounds suffix detected: `{report.get('confounds_suffix')}` "
        f"(expected `{report.get('expected_confounds_suffix')}`)",
        "",
        "## New confounds prefixes",
        "",
    ]
    new_prefixes = report.get("new_prefixes", [])
    lines += [f"- `{p}`" for p in new_prefixes] or ["- none"]
    lines += ["", "## Prefixes no longer detected", ""]
    missing = report.get("missing_prefixes", [])
    lines += [f"- `{p}`" for p in missing] or ["- none"]
    lines += [
        "",
        "## Review checklist",
        "",
        "- [ ] Map new prefixes to pipeline regressors in "
        "`rsdenoise/confounds.py` (`ALIASES`, `COMPONENT_PREFIXES`).",
        "- [ ] Update `rsdenoise/fmriprep_spec.json` expectations if the "
        "detected names are intentional.",
        "- [ ] Regenerate synthetic fixtures and run `python -m pytest`.",
        "- [ ] Confirm filename discovery in `rsdenoise/bids.py`.",
        "",
    ]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path, help="probe JSON report")
    args = parser.parse_args()
    apply(json.loads(args.report.read_text(encoding="utf-8")))
    print("Applied probe report to spec and docs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
