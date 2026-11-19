"""Static checks for the compatibility shims (no heavy deps required)."""

import ast
from pathlib import Path

ROOT = Path(__file__).parents[1]

SHIMS = {
    "fmriprepciftify_helpers.py": "legacy_helpers.fmriprepciftify_helpers",
    "HCP_helpers.py": "legacy_helpers.HCP_helpers",
}


def _tree(name):
    return ast.parse((ROOT / name).read_text(encoding="utf-8"))


def test_shim_reexports_shared_core():
    for name in SHIMS:
        tree = _tree(name)
        imports_core = any(
            isinstance(n, ast.ImportFrom) and n.module == "fmriprep_helpers"
            and any(a.name == "*" for a in n.names)
            for n in tree.body
        )
        assert imports_core, f"{name} must re-export fmriprep_helpers"


def test_shim_legacy_modules_are_lazy():
    """Archived forks must not be imported at shim import time.

    They use removed SciPy APIs and require FSL; importing them eagerly would
    break every notebook that only needs the shared core.
    """
    for name, legacy_module in SHIMS.items():
        tree = _tree(name)
        top_level_legacy_imports = [
            n for n in tree.body
            if isinstance(n, ast.ImportFrom) and n.module == legacy_module
            or isinstance(n, ast.Import)
            and any(a.name == legacy_module for a in n.names)
        ]
        assert not top_level_legacy_imports, (
            f"{name} imports {legacy_module} eagerly"
        )
        names = {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
        assert "__getattr__" in names, f"{name} must define lazy __getattr__"
        assert legacy_module in (ROOT / name).read_text(encoding="utf-8")
