"""Compatibility shim for the legacy ``HCP_helpers`` import.

The implementation now lives in :mod:`fmriprep_helpers`, the single shared core.
Legacy HCP-only helpers (the old in-pipeline ICA-AROMA implementation and task
design utilities) are exposed lazily from ``legacy_helpers.HCP_helpers``.  They
depend on FSL and old SciPy/NumPy APIs and are loaded only on request.

For new analyses, ICA-AROMA noise components should come from the separate
``fmripost-aroma`` BIDS App.  Set ``config.DATADIR`` to its derivatives tree
and use the ``ICA-AROMA`` motion-regression flavor; the shared core discovers
``*_desc-aroma_timeseries.tsv`` automatically.
"""

from __future__ import annotations

from importlib import import_module

from fmriprep_helpers import *  # noqa: F401,F403  (re-export shared core)

_LEGACY_MODULE = "legacy_helpers.HCP_helpers"
_LEGACY_NAMES = frozenset({
    "TaskRegression",
    "get_EVs",
    "classification",
    "denoising",
    "feature_frequency",
    "feature_spatial",
    "feature_time_series",
})


def __getattr__(name: str):
    if name in _LEGACY_NAMES:
        value = getattr(import_module(_LEGACY_MODULE), name)
        globals()[name] = value
        return value
    raise AttributeError(
        f"module {__name__!r} has no attribute {name!r}"
    )


def __dir__():
    return sorted(set(globals()) | _LEGACY_NAMES)
