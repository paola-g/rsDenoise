# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- **Modern-stack compatibility of the shared core**: replaced the NumPy alias
  `np.float` (removed in NumPy 2) with `float`, which fixes the `pcSigCh`
  voxel-normalisation flavor, switched the deprecated
  `scipy.ndimage.morphology` / `scipy.ndimage.filters` imports to the top-level
  `scipy.ndimage` namespace (removed in SciPy 2), and replaced
  `xml.etree.cElementTree` with `xml.etree.ElementTree`.
- `getAllFC()` now selects the correct output extension for CIFTI input; an
  `if`/`else` mistake made it fall back to `.nii.gz`.
- Corrected the fmripost-aroma confound prefix to `aroma_motion_` (single
  underscore) in `rsdenoise/confounds.py` and `fmriprep_spec.json`, matching
  fMRIPrep's actual column names.
- `find_probseg_file()` no longer probes a non-existent `ses-anat/anat` path;
  it checks the session `anat/` and the subject-level `anat/` instead.
- README: removed the broken HCP example-output link.

### Added

- `tests/test_core_modern_apis.py` statically guards the live modules against
  NumPy aliases and SciPy submodules that have been removed.

## [0.2.0] - 2026-11-19

The shared-core refactor: three near-duplicate helpers were consolidated into one
implementation with a lightweight fMRIPrep compatibility layer, a synthetic test
suite, and an automated release watch.

### Added

- **Shared compatibility layer** (`rsdenoise/`), dependency-free and exercised by
  the test suite:
  - `bids.py` — BIDS-entity discovery of BOLD, confounds, `aseg` and `probseg`
    files, plus legacy `fmriFileTemplate` expansion.
  - `confounds.py` — confounds TSV parsing, cross-release alias
    canonicalisation, numeric-suffix component ordering and validation.
  - `spec.py` + `fmriprep_spec.json` — a pinned fMRIPrep compatibility spec
    (targets **25.2.7**, LTS) with version history.
- **Automated test suite** (`tests/`) covering BIDS discovery, confounds
  handling, the release-watch probe, generated fixtures, ICA-AROMA inputs and
  the compatibility shims. Uses synthetic fixtures only.
- **Compatibility tooling** (`scripts/`):
  - `probe_fmriprep_spec.py` — detects the stable fMRIPrep version from PyPI and
    confound-name/filename drift from pinned fMRIPrep source.
  - `apply_probe.py` — records findings in the spec and writes
    `docs/fmriprep-compat-report.md` with a human review checklist.
  - `generate_fixtures.py` — writes an empty synthetic derivatives tree.
  - `smoke_wiring.py` — full-dependency discovery/confounds smoke test.
- **CI** (`.github/workflows/`):
  - `tests.yml` — unit tests plus a full-dependency import/wiring smoke test.
  - `fmriprep-release-watch.yml` — weekly probe that regenerates fixtures, runs
    the suite, and opens a review PR when output naming or columns drift.
- **Packaging**: `pyproject.toml` (setuptools) with pinned minimum dependency
  versions and `[test]` / `[legacy]` extras; a thin `setup.py` shim for legacy
  tooling; and a `rsdenoise` console script equivalent to `python rsDenoise.py`.
- **ICA-AROMA support for modern fMRIPrep** via the standalone
  [fmripost-aroma](https://fmripost-aroma.readthedocs.io/) BIDS App, consumed as
  an opt-in derivatives input.
- **Documentation**: rewritten `README.md` and a new `CHANGELOG.md`.

### Changed

- **Consolidated the three standalone forks into a single shared core.**
  `fmriprep_helpers.py` is now the only implementation; `fmriprepciftify_helpers.py`
  and `HCP_helpers.py` are thin shims that re-export it and share its `config`
  object. Edits to the core now propagate to every import path.
- **Input discovery replaces hard-coded filenames.** BOLD, confounds, `aseg` and
  `probseg` files are discovered by BIDS entities, so modern
  (`*_desc-confounds_timeseries.tsv`, `*_space-<space>_desc-preproc_bold.nii.gz`,
  fsLR CIFTI / GIFTI) and older (ciftify, `*_desc-confounds_regressors.tsv`)
  layouts are both supported.
- **Confounds are keyed by name**, not TSV position, and numbered component
  columns are ordered by their numeric suffix.
- **CLI portability**: `config.sourceDir` / `sys.path` fall back to the script's
  own directory when the historical HCP path is absent, so a checkout works
  without editing the file. No CLI flags were changed.
- The original forks were **archived under `legacy_helpers/`** and patched to
  import on current SciPy / scikit-learn / nilearn (`scipy.ndimage`,
  `GraphicalLassoCV`, `nilearn.glm.first_level.design_matrix`, `np.bool_`,
  `xml.etree.ElementTree`).

### Fixed

- Missing required confound families (for example `a_comp_cor_*` or `cosine*`)
  now raise a **descriptive error** instead of silently producing an empty
  design matrix.
- MCFLIRT motion confound handling is aligned with fMRIPrep ≥ 25.2.7.
- `fmriprep_spec.json` is now shipped as package data, so an installed copy can
  load the compatibility spec.
- Restored `config.operationDict`, which an automated edit during the refactor
  had accidentally dropped.

### Deprecated

- `legacy_helpers/` and the lazily exposed fork-only functions (task design,
  partial-correlation helpers, in-pipeline ICA-AROMA). Kept for reference; new
  work should use the shared core and fmripost-aroma.

## [0.1.0] - 2023-06-22

Baseline of the existing rsDenoise source as it stood on the remote tip
(`c28a029`), including the three near-duplicate helper forks
(`fmriprep_helpers.py`, `fmriprepciftify_helpers.py`, `HCP_helpers.py`), the
`rsDenoise.py` CLI, the example script, and the notebooks.
