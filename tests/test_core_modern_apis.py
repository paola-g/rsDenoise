"""Guard the shared core against APIs removed in NumPy 2 / SciPy 2 / Python 3.9+.

These are static AST checks so the compatibility suite stays dependency-free,
while still catching the drift that only shows up when the core is imported
with a modern scientific stack.
"""

import ast
from pathlib import Path

ROOT = Path(__file__).parents[1]

# Files that make up the live import surface (archived forks are exempt).
LIVE_FILES = (
    "fmriprep_helpers.py",
    "rsDenoise.py",
    "runPipeline_example.py",
    "fmriprepciftify_helpers.py",
    "HCP_helpers.py",
)

# numpy aliases removed in NumPy 1.24/2.0 (np.float64 etc. are still fine).
REMOVED_NUMPY_ATTRS = {"float", "int", "bool", "object", "str", "complex",
                       "unicode"}

# scipy submodule shims that moved to the top-level ``scipy.ndimage``.
DEPRECATED_SCIPY_MODULES = {
    "scipy.ndimage.morphology",
    "scipy.ndimage.filters",
}


def _trees():
    for name in LIVE_FILES:
        yield name, ast.parse((ROOT / name).read_text(encoding="utf-8"))


def test_no_removed_numpy_aliases():
    offenders = []
    for name, tree in _trees():
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Attribute)
                and node.attr in REMOVED_NUMPY_ATTRS
                and isinstance(node.value, ast.Name)
                and node.value.id == "np"
            ):
                offenders.append(f"{name}:{node.lineno} np.{node.attr}")
    assert not offenders, (
        "Removed NumPy aliases are no longer valid (use np.float64/float, "
        "np.int64/int, ...): " + ", ".join(offenders)
    )


def test_no_deprecated_scipy_ndimage_submodules():
    offenders = []
    for name, tree in _trees():
        for node in ast.walk(tree):
            module = None
            if isinstance(node, ast.ImportFrom):
                module = node.module
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in DEPRECATED_SCIPY_MODULES:
                        offenders.append(f"{name}:{node.lineno} {alias.name}")
            if module in DEPRECATED_SCIPY_MODULES:
                offenders.append(f"{name}:{node.lineno} {module}")
    assert not offenders, (
        "scipy.ndimage.morphology/filters are deprecated and removed in "
        "SciPy 2; import from scipy.ndimage instead: " + ", ".join(offenders)
    )


def test_no_deprecated_c_element_tree():
    offenders = []
    for name, tree in _trees():
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "xml.etree.cElementTree":
                        offenders.append(f"{name}:{node.lineno}")
            elif isinstance(node, ast.ImportFrom) and node.module == (
                "xml.etree.cElementTree"
            ):
                offenders.append(f"{name}:{node.lineno}")
    assert not offenders, (
        "xml.etree.cElementTree is deprecated (removed in Python 3.9); use "
        "xml.etree.ElementTree: " + ", ".join(offenders)
    )
