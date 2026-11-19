"""Shared rsDenoise compatibility layer.

The legacy helper modules (``fmriprep_helpers``, ``fmriprepciftify_helpers``,
``HCP_helpers``) re-export this API so existing imports keep working.
"""

from .bids import (
    find_aroma_confounds_file,
    find_aseg_file,
    find_bold_file,
    find_confounds_file,
    find_probseg_file,
    parse_entities,
    resolve_data_root,
    substitute_template,
)
from .confounds import (
    ALIASES,
    COMPONENT_PREFIXES,
    MOTION_COLUMNS,
    Confounds,
    ConfoundsError,
    canonicalize_column_names,
    order_component_columns,
)

__all__ = [
    "find_aroma_confounds_file",
    "find_aseg_file",
    "find_bold_file",
    "find_confounds_file",
    "find_probseg_file",
    "parse_entities",
    "resolve_data_root",
    "substitute_template",
    "ALIASES",
    "COMPONENT_PREFIXES",
    "MOTION_COLUMNS",
    "canonicalize_column_names",
    "order_component_columns",
    "Confounds",
    "ConfoundsError",
]
