"""Compatibility shim for the legacy ``fmriprepciftify_helpers`` import.

The implementation now lives in :mod:`fmriprep_helpers`, which is the single
shared core used by the CLI, the example script and all three helper import
paths.  Importing this module therefore gives you the modern, discovery-based
pipeline with the same ``config``/``Hooks``/``operationDict`` interface.

Functions that existed only in the ciftify fork are exposed lazily from
``legacy_helpers.fmriprepciftify_helpers``.  They rely on legacy SciPy APIs and
are only loaded if you actually request them.
"""

from __future__ import annotations

from importlib import import_module

from fmriprep_helpers import *  # noqa: F401,F403  (re-export shared core)

_LEGACY_MODULE = "legacy_helpers.fmriprepciftify_helpers"
_LEGACY_NAMES = frozenset({
    "TaskRegression",
    "get_EVs",
    "cov2corr",
    "partialcorr_via_inverse",
    "partialcorr_via_inverse_L1reg",
    "partialcorr_via_linreg",
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
