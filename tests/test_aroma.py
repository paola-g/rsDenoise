from pathlib import Path

from rsdenoise import find_aroma_confounds_file, find_bold_file
from scripts.generate_fixtures import RUN

AROMA_PREFIXES = ("aggrDenoised", "nonaggrDenoised", "orthaggrDenoised")


def test_fmripost_aroma_outputs_are_discoverable(tmp_path):
    func = tmp_path / "sub-01" / "func"
    func.mkdir(parents=True)
    bold = func / f"sub-01_{RUN}_space-MNI152NLin6Asym_res-2_desc-aggrDenoised_bold.nii.gz"
    bold.touch()
    confounds = func / f"sub-01_{RUN}_desc-aroma_timeseries.tsv"
    confounds.write_text(
        "aroma_motion_00\taroma_orth_motion_00\n0.1\t0.2\n", encoding="utf-8")

    assert find_bold_file(tmp_path, "01", RUN) == bold
    assert find_aroma_confounds_file(tmp_path, "01", RUN) == confounds
    # Standard fmriprep confounds lookup must not pick up the AROMA-only file.
    from rsdenoise import find_confounds_file
    assert find_confounds_file(tmp_path, "01", RUN) is None
