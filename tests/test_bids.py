from pathlib import Path

import pytest

from rsdenoise.bids import (
    find_aseg_file,
    find_bold_file,
    find_confounds_file,
    find_probseg_file,
    parse_entities,
    resolve_data_root,
    substitute_template,
)


def _touch(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch()
    return path


def test_parse_entities_handles_hyphenated_values_and_suffix():
    entities = parse_entities(
        "sub-01_ses-A_task-rest_run-1_space-MNI152NLin6Asym_res-2"
        "_desc-preproc_bold.nii.gz"
    )
    assert entities["sub"] == "01"
    assert entities["ses"] == "A"
    assert entities["run"] == "1"
    assert entities["space"] == "MNI152NLin6Asym"
    assert entities["res"] == "2"
    assert entities["desc"] == "preproc"
    assert entities["suffix"] == "bold"


def test_substitute_template_with_and_without_session():
    template = "sub-#subjectID#_ses-#fMRIsession#_#fMRIrun#_bold.nii.gz"
    assert substitute_template(template, "01", "task-rest_run-1", "A") == (
        "sub-01_ses-A_task-rest_run-1_bold.nii.gz"
    )
    assert "ses-" not in substitute_template(template, "01", "task-rest_run-1")


@pytest.mark.parametrize("root_has_fmriprep_subdir", [False, True])
def test_find_bold_file_volume_modern_and_legacy(tmp_path, root_has_fmriprep_subdir):
    root = tmp_path / ("derivatives" if root_has_fmriprep_subdir else "fmriprep")
    func = root / "sub-01" / "ses-A" / "func"
    modern = _touch(
        func / "sub-01_ses-A_task-rest_run-1_space-MNI152NLin6Asym_res-2"
              "_desc-preproc_bold.nii.gz"
    )
    legacy = _touch(func / "sub-01_ses-A_task-rest_run-1_desc-preproc_bold.nii.gz")
    search_root = tmp_path if root_has_fmriprep_subdir else root

    assert resolve_data_root(search_root) == root
    assert find_bold_file(search_root, "01", "task-rest_run-1", session="ses-A",
                          space="MNI152NLin6Asym_res-2") == modern
    assert find_bold_file(search_root, "sub-01", "run-1", session="A") in {modern, legacy}


def test_find_bold_file_ignores_confounds_and_other_descriptions(tmp_path):
    func = tmp_path / "sub-01" / "func"
    bold = _touch(func / "sub-01_task-rest_run-1_desc-preproc_bold.nii.gz")
    _touch(func / "sub-01_task-rest_run-1_desc-confounds_timeseries.tsv")
    _touch(func / "sub-01_task-rest_run-2_desc-preproc_bold.nii.gz")
    assert find_bold_file(tmp_path, "01", "task-rest_run-1") == bold


def test_find_bold_file_cifti_gifti_and_template(tmp_path):
    func = tmp_path / "sub-01" / "func"
    cifti = _touch(func / "sub-01_task-rest_run-1_space-fsLR_den-91k_bold.dtseries.nii")
    gifti = _touch(func / "sub-01_task-rest_run-1_space-fsaverage6_hemi-L_bold.func.gii")
    assert find_bold_file(tmp_path, "01", "task-rest_run-1", is_cifti=True) == cifti
    assert find_bold_file(tmp_path, "01", "task-rest_run-1", is_gifti=True) == gifti

    custom = _touch(tmp_path / "custom" / "run1.nii.gz")
    assert find_bold_file(tmp_path, "01", "task-rest_run-1",
                          template="custom/run1.nii.gz") == custom
    assert find_bold_file(tmp_path, "01", "task-rest_run-1",
                          template="missing.nii.gz") is None


def test_find_confounds_file_prefers_timeseries_name(tmp_path):
    func = tmp_path / "sub-01" / "func"
    old = _touch(func / "sub-01_task-rest_run-1_desc-confounds_regressors.tsv")
    new = _touch(func / "sub-01_task-rest_run-1_desc-confounds_timeseries.tsv")
    assert find_confounds_file(tmp_path, "01", "task-rest_run-1") == new
    new.unlink()
    assert find_confounds_file(tmp_path, "01", "task-rest_run-1") == old


def test_find_probseg_and_aseg(tmp_path):
    anat = tmp_path / "sub-01" / "anat"
    _touch(anat / "sub-01_space-MNI152NLin2009cAsym_res-2_label-WM_probseg.nii.gz")
    wm = _touch(anat / "sub-01_space-MNI152NLin6Asym_res-2_label-WM_probseg.nii.gz")
    assert find_probseg_file(tmp_path, "01", space="MNI152NLin6Asym_res-2") == wm
    assert find_probseg_file(tmp_path, "01", label="GM") is None

    aseg = _touch(tmp_path / "sub-01" / "func" /
                  "sub-01_task-rest_run-1_space-MNI152NLin6Asym_res-2_desc-aseg_dseg.nii.gz")
    assert find_aseg_file(tmp_path, "01", space="MNI152NLin6Asym_res-2") == aseg
