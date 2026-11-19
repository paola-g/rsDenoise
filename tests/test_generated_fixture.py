import json
from pathlib import Path

from rsdenoise import Confounds, find_bold_file, find_confounds_file, find_probseg_file
from scripts.generate_fixtures import RUN, SPACE, generate

SPEC = json.loads(
    (Path(__file__).parents[1] / "rsdenoise" / "fmriprep_spec.json").read_text(
        encoding="utf-8")
)


def test_generated_current_stable_fixture_is_discoverable(tmp_path):
    generate(tmp_path, SPEC)

    bold = find_bold_file(tmp_path, "01", RUN, session="A", space=SPACE)
    assert bold is not None and bold.name.endswith("_desc-preproc_bold.nii.gz")

    confounds = find_confounds_file(tmp_path, "01", RUN, session="A")
    assert confounds is not None and confounds.name.endswith(
        "_desc-confounds_timeseries.tsv")

    wm = find_probseg_file(tmp_path, "01", session="A", space=SPACE, label="WM")
    assert wm is not None and "label-WM_probseg" in wm.name

    table = Confounds.read(confounds)
    table.validate(SPEC["confounds"]["core_columns"])
    assert table.resolve("framewise_displacement") == "framewise_displacement"
    assert table.component_columns("a_comp_cor")
