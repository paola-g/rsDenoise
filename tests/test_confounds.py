import pytest

from rsdenoise.confounds import Confounds, ConfoundsError


TSV = """framewise_displacement\tdvars\ttrans_x\trot_z\ta_comp_cor_2\ta_comp_cor_10\tcosine00\tcosine01\twhite_matter\tcsf\tglobal_signal
n/a\tn/a\t0.0\t0.0\t1\t10\t1\t1\t0\t0\t0
0.1\t0.2\t0.3\t0.4\t2\t20\t0\t1\t0.5\t0.6\t0.7
"""


@pytest.fixture
def confounds(tmp_path):
    path = tmp_path / "confounds.tsv"
    path.write_text(TSV, encoding="utf-8")
    return Confounds.read(path)


def test_read_handles_na_and_numeric_values(confounds):
    assert confounds.n_volumes == 2
    assert confounds.column("framewise_displacement") == [0.0, 0.1]
    assert confounds.column("dvars") == [0.0, 0.2]


def test_component_columns_sorted_by_number_not_file_order(confounds):
    assert confounds.component_columns("a_comp_cor") == ["a_comp_cor_2", "a_comp_cor_10"]
    assert confounds.component_columns("a_comp_cor", limit=1) == ["a_comp_cor_2"]


def test_cosine_columns(confounds):
    assert confounds.cosine_columns() == ["cosine00", "cosine01"]


def test_motion_columns_in_canonical_order(confounds):
    # Only trans_x and rot_z exist here; a clear error must list the gaps.
    with pytest.raises(ConfoundsError) as exc:
        confounds.motion()
    assert "trans_y" in str(exc.value)
    assert "rot_z" not in str(exc.value).split("missing required columns:")[1].split(".")[0]


def test_aliases_and_clear_errors(confounds):
    assert confounds.resolve("white_matter") == "white_matter"
    assert confounds.column("csf") == [0.0, 0.6]
    with pytest.raises(ConfoundsError) as exc:
        confounds.column("std_dvars")
    assert "std_dvars" in str(exc.value)
    assert "Available columns" in str(exc.value)


def test_validate_lists_all_missing_columns(confounds):
    with pytest.raises(ConfoundsError) as exc:
        confounds.validate(["std_dvars", "framewise_displacement", "trans_y"])
    message = str(exc.value)
    assert "std_dvars" in message
    assert "trans_y" in message
    assert "framewise_displacement" not in message.split("missing required columns:")[1].split(".")[0]


def test_empty_file_raises(tmp_path):
    path = tmp_path / "empty.tsv"
    path.write_text("", encoding="utf-8")
    with pytest.raises(ConfoundsError):
        Confounds.read(path)
