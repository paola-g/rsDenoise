<div align="center">

# rsDenoise

**A configurable, extensible pipeline for resting-state fMRI denoising and functional connectivity.**

[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Tests](https://github.com/paola-g/rsDenoise/actions/workflows/tests.yml/badge.svg?branch=refactor)](https://github.com/paola-g/rsDenoise/actions/workflows/tests.yml)
[![fMRIPrep release watch](https://github.com/paola-g/rsDenoise/actions/workflows/fmriprep-release-watch.yml/badge.svg?branch=refactor)](https://github.com/paola-g/rsDenoise/actions/workflows/fmriprep-release-watch.yml)
[![fMRIPrep](https://img.shields.io/badge/fMRIPrep-25.2.7-blueviolet.svg)](https://fmriprep.org/)

*Authors: Paola Galdi ([paola.galdi@gmail.com](mailto:paola.galdi@gmail.com)) · Julien Dubois ([jcrdubois@gmail.com](mailto:jcrdubois@gmail.com))*

</div>

> [!WARNING]
> The software is provided **as is**, without warranty of any kind.

`rsDenoise` turns minimally preprocessed resting-state fMRI into denoised time
series and functional-connectivity matrices, using a pipeline you describe as
data rather than code. It was originally built for the Human Connectome Project
([HCP directory structure](https://wiki.humanconnectome.org/display/PublicData/How+To+Handle+Downloaded+HCP+Data)),
was later adapted to HCP-like data converted with
[ciftify](https://github.com/edickie/ciftify), and today works directly with
[**fMRIPrep**](https://fmriprep.org/en/stable/) derivatives. Both volumetric
(NIfTI) and surface (CIFTI/GIFTI) data are supported.

The original implementation is preserved at
[adolphslab/HCP_MRI-behavior](https://github.com/adolphslab/HCP_MRI-behavior).

---

## Table of contents

- [Why rsDenoise](#why-rsdenoise)
- [Installation](#installation)
- [Quick start](#quick-start)
- [fMRIPrep compatibility](#fmriprep-compatibility)
- [Configuring a pipeline](#configuring-a-pipeline)
- [Pipeline operations reference](#pipeline-operations-reference)
- [Advanced functionality](#advanced-functionality)
- [Architecture](#architecture)
- [Development, testing and CI](#development-testing-and-ci)
- [Project layout](#project-layout)
- [References](#references)
- [Changelog](#changelog)

---

## Why rsDenoise

- 🧩 **Pipelines as data.** A pipeline is an ordered list of operations, so you
  can build, share and re-run a denoising strategy without writing code.
- 🧠 **Modern fMRIPrep first.** Inputs and confounds are *discovered* from BIDS
  entities, so current and older fMRIPrep layouts both work.
- 🔀 **Surface or volume.** CIFTI, GIFTI and NIfTI inputs are handled uniformly.
- 🧪 **Tested.** A dependency-light compatibility suite runs on every push, and a
  weekly workflow watches fMRIPrep releases for breaking changes.
- 📈 **Beyond denoising.** Functional connectivity (parcel-wise, seed-based or
  vertex/voxel-wise), QC plots and XML reports are built in.

---

## Installation

**Requirements:** Python ≥ 3.10. Runtime dependencies (installed automatically)
are `numpy`, `scipy`, `pandas`, `matplotlib`, `nibabel`, `nilearn`, `nipype`,
`scikit-learn`, `seaborn` and `statsmodels`.

Install from a checkout:

```bash
pip install -e .            # editable install for development
# or
pip install .               # regular install
```

Optional extras:

```bash
pip install -e ".[test]"    # pytest, for the compatibility suite
pip install -e ".[legacy]"  # `future`, only needed by the archived legacy helpers
```

> [!NOTE]
> **Cluster / queue users.** Running pipelines through a Sun Grid Engine cluster
> (`config.queue = True`) additionally needs SGE (`qsub`/`qstat`) and FSL
> (`$FSLDIR`). The archived ICA-AROMA helpers shell out to FSL tools.

---

## Quick start

### Command line

The recommended entry point is the `rsDenoise` CLI (also installed as the
`rsdenoise` console command):

```bash
rsdenoise \
  -data /path/to/fmriprep/derivatives \
  -i    subjects.txt \
  -pipe A \
  -o    rsDenoise \
  -cifti
```

`-data`, `-i`, `-pipe` and `-o` are required; see `rsdenoise --help` for the
full flag list (spaces, surfaces, smoothing, parcellation, seed- and
voxel-wise connectivity). `subjects.txt` holds one subject ID per line (a
`sub-` prefix is added automatically if missing).

### From Python

`runPipeline_example.py` is a minimal in-code example:

```python
from fmriprep_helpers import *

config.DATADIR = "/path/to/fmriprep/derivatives"
config.subject = "sub-0040"
config.Operations = config.operationDict["A"]
config.isCifti = True
config.queue = False          # run locally
config.outDir = "rsDenoise"

runPipelinePar(launchSubproc=True, do_makeGrayPlot=True, do_computeFC=True)
```

### Notebooks

The IPython notebooks demonstrate common workflows. `fmriprep_YALE.ipynb` and
`FC_plots_Conte.ipynb` are maintained; the remaining `Conte_*.ipynb` files
predate the shared-core refactor and are kept for historical reference.

---

## fMRIPrep compatibility

The pipeline targets the current stable fMRIPrep release, recorded in
[`rsdenoise/fmriprep_spec.json`](rsdenoise/fmriprep_spec.json) (currently
**25.2.7**). Rather than reconstructing filenames from a hard-coded template,
inputs are **discovered by BIDS entities** and ranked, so multiple fMRIPrep
generations can be read side by side.

| Item | Modern | Older / still supported |
| --- | --- | --- |
| Confounds file | `*_desc-confounds_timeseries.tsv` | `*_desc-confounds_regressors.tsv`, legacy names |
| Volumetric BOLD | `*_space-<space>_desc-preproc_bold.nii.gz` | ciftify / older fMRIPrep names |
| Surface BOLD | `*_space-fsLR_den-91k_bold.dtseries.nii`, `*_hemi-L*_bold.func.gii` | ciftify GIFTI names |

Confounds are looked up **by column name** (with aliases across releases) and
numbered components are ordered by their **numeric suffix** rather than by TSV
position. Recognised families include `a_`/`c_`/`w_`/`t_comp_cor_*`,
`edge_comp_*`, `cosine*`, `non_steady_state_outlier*` and `motion_outlier*`.

> [!IMPORTANT]
> If a required regressor family is absent — for example `a_comp_cor_*` when
> CompCor was not enabled — the failing operation raises a **descriptive error**
> instead of silently building an empty design matrix.

You can still force a specific file with `config.fmriFileTemplate`, using the
`#subjectID#`, `#fMRIsession#` and `#fMRIrun#` placeholders. When present, it
takes precedence over discovery.

### ICA-AROMA via `fmripost-aroma`

fMRIPrep removed ICA-AROMA in 23.1.0. The `ICA-AROMA` motion-regression flavor
is still supported, but it now consumes noise components produced by the
standalone [fmripost-aroma](https://fmripost-aroma.readthedocs.io/) BIDS App:

1. Run current fMRIPrep with `--cifti-output` (or the volume space you need).
2. Run fmripost-aroma on those derivatives.
3. Point `config.DATADIR` at the **fmripost-aroma** derivatives directory and
   select the `ICA-AROMA` motion flavor.

The shared core discovers `*_desc-aroma_timeseries.tsv` and the
`*_desc-{aggr,nonaggr,orthaggr}Denoised_bold.nii.gz` files automatically. The old
in-pipeline AROMA implementation remains available only through the lazily
loaded `HCP_helpers` archive.

---

## Configuring a pipeline

Preprocessing is a sequence of **operations**. Every operation is a function
with the following signature:

```python
def OperationName(niiImg, flavor, masks, imgInfo):
    ...
```

| Argument | Meaning |
| --- | --- |
| `niiImg` | `[data, volData]`. For NIfTI inputs `volData` is `None`; for CIFTI inputs `data` is the CIFTI array and `volData` the volumetric array. Load with `load_img()`. |
| `flavor` | The operation's parameter list (see the [reference](#pipeline-operations-reference)). |
| `masks` | Output of `makeTissueMasks()`: `[whole brain, white matter, CSF, gray matter]`. |
| `imgInfo` | `[rows, columns, slices, time points, affine, TR]`, retrievable with `load_img()`. |

A pipeline is a list of `[operation_name, order, params]` entries:

```python
[
    ['Operation1', 1, [param1]],
    ['Operation2', 2, [param1, param2, param3]],
    ['Operation3', 3, [param1, param2]],
    ['Operation4', 4, [param1]],
    ['Operation5', 5, [param1, param2]],
    ['Operation6', 6, [param1, param2, param3]],
    ['Operation7', 7, [param]],
]
```

Operations run in ascending `order`. **Regression operations that share the same
order are merged into a single regression step** — that is how you combine, say,
tissue and global-signal regressors in one design matrix.

Several named pipelines ship in `config.operationDict`:

```python
config.operationDict = {
    'A': [  # Finn et al. 2015
        ['VoxelNormalization',      1, ['zscore']],
        ['Detrending',              2, ['legendre', 3, 'WMCSF']],
        ['TissueRegression',        3, ['WMCSF', 'GM']],
        ['MotionRegression',        4, ['R dR']],
        ['TemporalFiltering',       5, ['Gaussian', 1]],
        ['Detrending',              6, ['legendre', 3, 'GM']],
        ['GlobalSignalRegression',  7, ['GS']],
    ],
    'B': [  # Satterthwaite et al. 2013 (Ciric7)
        ['VoxelNormalization',      1, ['demean']],
        ['Detrending',              2, ['poly', 2, 'wholebrain']],
        ['TemporalFiltering',       3, ['Butter', 0.01, 0.08]],
        ['MotionRegression',        4, ['R dR R^2 dR^2']],
        ['TissueRegression',        4, ['WMCSF+dt+sq', 'wholebrain']],
        ['GlobalSignalRegression',  4, ['GS+dt+sq']],
        ['Scrubbing',               4, ['RMS', 0.25]],
    ],
    'C': [  # Siegel et al. 2016 (SiegelB)
        ['VoxelNormalization',      1, ['demean']],
        ['Detrending',              2, ['poly', 1, 'wholebrain']],
        ['TissueRegression',        3, ['CompCor', 5, 'WMCSF', 'wholebrain']],
        ['TissueRegression',        3, ['GM', 'wholebrain']],
        ['GlobalSignalRegression',  3, ['GS']],
        ['MotionRegression',        3, ['censoring']],
        ['Scrubbing',               3, ['FD+DVARS', 0.25, 5]],
        ['TemporalFiltering',       4, ['Butter', 0.009, 0.08]],
    ],
    # ... 12 more
}
```

### Custom operations

Add your function to the `Hooks` mapping in the core and reference it by name in
a pipeline:

```python
Hooks = {
    'MotionRegression':       MotionRegression,
    'Scrubbing':              Scrubbing,
    'TissueRegression':       TissueRegression,
    'Detrending':             Detrending,
    'TemporalFiltering':      TemporalFiltering,
    'GlobalSignalRegression': GlobalSignalRegression,
    'VoxelNormalization':     VoxelNormalization,
    'newFunction':            newFunction,
}
```

---

## Pipeline operations reference

There are seven built-in operations: [Voxel Normalization](#voxel-normalization),
[Detrending](#detrending), [Motion Regression](#motion-regression),
[Scrubbing](#scrubbing), [Tissue Regression](#tissue-regression),
[Global Signal Regression](#global-signal-regression) and
[Temporal Filtering](#temporal-filtering).

### Voxel Normalization

- **`zscore`** — convert each voxel's time course to a z-score (remove mean,
  divide by standard deviation).
- **`demean`** — subtract the mean from each voxel's time series.
- **`pcSigCh`** — convert each voxel's time course to % signal change (remove
  mean, divide by mean, multiply by 100).

```python
['VoxelNormalization', 1, ['zscore']]
```

### Detrending

- **`poly`** — polynomial regressors up to the specified order.
  1. Polynomial order.
  2. Tissue: `'WMCSF'` or `'GM'`.
- **`legendre`** — Legendre polynomials up to the specified order.
  1. Polynomial order.
  2. Tissue: `'WMCSF'` or `'GM'`.

```python
['Detrending', 2, ['poly', 3, 'GM']]
```

### Motion Regression

> [!NOTE]
> `R = [X Y Z pitch yaw roll]`. If temporal filtering has already been performed,
> the motion regressors are filtered too. If scrubbing was requested, a regressor
> is added for every volume to be censored; the `censoring` option performs only
> scrubbing.

- **`R`** — realignment parameters (R).
- **`R dR`** — R and their temporal derivatives (dR).
- **`R R^2`** — R and their quadratic terms.
- **`R dR R^2 dR^2`** — R with derivatives, quadratic terms and squared derivatives.
- **`R R^2 R-1 R-1^2`** — R at time *t* and *t-1*, with their square terms.
- **`R R^2 R-1 R-1^2 R-2 R-2^2`** — R at *t*, *t-1* and *t-2*, with square terms.
- **`censoring`** — a unit impulse per volume tagged for scrubbing.
- **`ICA-AROMA`** — ICA noise components as regressors (see
  [ICA-AROMA via fmripost-aroma](#ica-aroma-via-fmripost-aroma)).

```python
['MotionRegression', 3, ['R dR']]
```

### Scrubbing

> [!NOTE]
> This step only *flags* volumes; they are regressed out in the Motion
> Regression step. Uncensored segments shorter than 5 contiguous volumes are
> flagged for removal as well.

- **`FD`**
  1. Framewise-displacement threshold (mm).
  2. Number of adjacent volumes to exclude (optional).
- **`DVARS`**
  1. DVARS threshold.
  2. Number of adjacent volumes to exclude (optional).
- **`FD+DVARS`**
  1. Framewise-displacement threshold (mm).
  2. Threshold *t* such that volumes with DVARS greater than (100 + *t*)% of the
     run median DVARS are flagged (as in Siegel et al., *Cerebral Cortex*, 2016).
  3. Number of adjacent volumes to exclude (optional).
- **`RMS`**
  1. Root-mean-square displacement threshold (mm).
  2. Number of adjacent volumes to exclude (optional).

```python
['Scrubbing', 4, ['FD+DVARS', 0.25, 5]]
```

### Tissue Regression

Each flavor takes one argument specifying whether regression is performed on the
gray-matter signal (`'GM'`) or the whole-brain signal (`'wholebrain'`).

- **`GM`** — gray-matter signal as a regressor.
- **`WM`** — white-matter signal as a regressor.
- **`WMCSF`** — white-matter and CSF signals as regressors.
- **`WMCSF+dt`** — WM and CSF signals with their derivatives.
- **`WMCSF+dt+sq`** — WM and CSF signals with derivatives and quadratic terms.
- **`CompCor`** — PCA-based components (Behzadi et al., 2007).
  1. Number of components to compute for the specified tissue mask.
  2. Mask: a single `'WMCSF'` mask, or separate `'WM+CSF'` masks.
  3. `'GM'` or `'wholebrain'`.

```python
['TissueRegression', 5, ['CompCor', 5, 'WMCSF', 'wholebrain']]
```

### Global Signal Regression

- **`GS`** — global signal as a regressor.
- **`GS+dt`** — global signal with its derivatives.
- **`GS+dt+sq`** — global signal with derivatives and quadratic terms.

```python
['GlobalSignalRegression', 6, ['GS+dt+sq']]
```

### Temporal Filtering

> [!NOTE]
> If scrubbing was requested, censored volumes are replaced by linear
> interpolation.

- **`Butter`** — Butterworth band-pass filter.
  1. High-pass threshold.
  2. Low-pass threshold.
- **`Gaussian`** — low-pass Gaussian smoothing.
  1. Standard deviation.
- **`DCT`** — discrete cosine transform regressors for temporal filtering.
  1. High-pass threshold.
  2. Low-pass threshold.

```python
['TemporalFiltering', 7, ['Butter', 0.009, 0.08]]
```

---

## Advanced functionality

- **QC plots** — framewise-displacement trace and grayplot.
- **XML reports** — per-run provenance and QC summaries.
- **SGE support** — submit pipelines as job arrays on a Sun Grid Engine cluster.
- **Functional connectivity** — parcel-wise, seed-based, or vertex/voxel-wise
  (`-vFC`).
- **Score prediction** — predict individual scores from connectivity matrices.

---

## Architecture

The three historical import paths still work, but the implementation now lives in
a **single shared core**:

| Module | Role |
| --- | --- |
| `fmriprep_helpers.py` | **Shared core.** Used by the CLI, the example script and both shims. Works directly with fMRIPrep outputs, with or without FreeSurfer. |
| `fmriprepciftify_helpers.py` | Compatibility **shim** re-exporting the shared core. |
| `HCP_helpers.py` | Compatibility **shim** re-exporting the shared core. |

Both shims share the core's `config` object and expose a handful of
fork-specific functions **lazily** (task design, partial-correlation helpers and
the old in-pipeline ICA-AROMA implementation). Those depend on FSL and legacy
SciPy/NumPy APIs, so they are only imported when explicitly requested. The
original pre-consolidation forks are archived under `legacy_helpers/` for
reference — **new analyses should use the shared core.**

[`rsdenoise/`](rsdenoise) is a lightweight, dependency-free compatibility layer
that the automated tests exercise directly:

- `bids.py` — BIDS-entity discovery of BOLD / confounds / aseg / probseg files.
- `confounds.py` — TSV parsing, alias canonicalisation, component ordering.
- `spec.py` + `fmriprep_spec.json` — the pinned compatibility spec and history.

---

## Development, testing and CI

```bash
python -m pip install -e ".[test]"
python -m pytest -q          # 23 tests, stdlib-only by design
python -m scripts.smoke_wiring   # full-dependency discovery/confounds smoke test
```

GitHub Actions provides two workflows:

- **`tests`** — unit tests plus a full-dependency import/wiring smoke test on
  every push and pull request.
- **`fmriprep release watch`** — weekly. It polls the stable fMRIPrep version
  from PyPI and parses the pinned fMRIPrep source for confound-name drift,
  regenerates synthetic fixtures, runs the suite, and opens a **review PR** with
  a compatibility report when naming or columns change. The PR is a proposal,
  not an auto-merge.

Synthetic fixtures live under `tests/fixtures/` (gitignored) and are regenerated
by the tests — do not commit them.

---

## Project layout

```
rsDenoise.py                 # command-line interface (also `rsdenoise`)
runPipeline_example.py       # minimal in-code example
fmriprep_helpers.py          # shared core
fmriprepciftify_helpers.py   # compatibility shim
HCP_helpers.py               # compatibility shim
rsdenoise/                   # dependency-free compatibility layer + pinned spec
legacy_helpers/              # archived pre-consolidation forks (reference only)
scripts/                     # release-watch probe, fixture generator, smoke test
tests/                       # synthetic-fixture compatibility suite
.github/workflows/           # tests + fMRIPrep release watch
data/                        # example subject ID lists
```

---

## References

- Dubois J, Galdi P, Han Y, Paul LK, Adolphs R. *Resting-state functional brain
  connectivity best predicts the personality dimension of openness to
  experience.* Personality Neuroscience. 2018 Jul;1:e6.
- Dubois J, Galdi P, Paul LK, Adolphs R. *A distributed brain network predicts
  general intelligence from resting-state human neuroimaging data.*
  Philosophical Transactions of the Royal Society B. 2018;373(1756):20170284.
- Kliemann D, Adolphs R, Armstrong T, Galdi P, et al. *Caltech Conte Center, a
  multimodal data resource for exploring social cognition and decision-making.*
  Scientific Data. 2022;9(1):138.

Example output for an HCP subject is available
[here](https://caltech.box.com/s/t7zaw05wcnudl7b2jvn69wa2fvzlcc4j).

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for the release history, including the shared-core
refactor and the fMRIPrep compatibility work.
