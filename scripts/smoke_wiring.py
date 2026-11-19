"""Runtime smoke test of the shared-core wiring (requires full dependencies)."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

from rsdenoise import find_bold_file  # noqa: E402
from scripts.generate_fixtures import RUN, SPACE, generate  # noqa: E402

import fmriprep_helpers as fh  # noqa: E402


def main() -> int:
    spec = json.loads((ROOT / "rsdenoise" / "fmriprep_spec.json").read_text(
        encoding="utf-8"))
    with tempfile.TemporaryDirectory() as tmp:
        generate(Path(tmp), spec)
        fh.config.DATADIR = tmp
        fh.config.subject = "01"
        fh.config.session = "ses-A"
        fh.config.fmriRun = RUN
        fh.config.space = SPACE
        fh.config.confounds = None

        bold = find_bold_file(tmp, "01", RUN, session="ses-A", space=SPACE)
        assert bold is not None, "BOLD discovery failed"

        data = fh.get_confounds()
        assert "framewise_displacement" in data.columns
        assert "a_comp_cor_00" in data.columns
        assert "a_comp_cor_01" in data.columns
        assert list(data.columns).index("a_comp_cor_00") < list(
            data.columns).index("a_comp_cor_01"), "component ordering failed"

        _check_pipelines(fh)

        print(f"wiring OK: {bold.name}, {data.shape[1]} confounds columns")
    return 0


def _check_pipelines(fh) -> None:
    """Every pipeline must reference known operations with the arity their
    implementation expects (a missing component count used to crash
    pipeline 'C' at run time)."""
    for name, operations in fh.config.operationDict.items():
        for op, _order, params in operations:
            assert op in fh.Hooks, f"{name}: unknown operation {op!r}"
            if op == "TissueRegression" and params and params[0] == "CompCor":
                assert isinstance(params[1], int), (
                    f"{name}: TissueRegression CompCor needs an integer "
                    f"component count, got {params!r}")


if __name__ == "__main__":
    raise SystemExit(main())
