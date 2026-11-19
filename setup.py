"""Minimal setup.py shim for legacy tooling.

This project is configured via ``pyproject.toml`` (PEP 518/621).  This file
exists only so that older tooling that does not support PEP 517 can still
invoke ``python setup.py ...``.  All metadata is defined in ``pyproject.toml``.
"""

from setuptools import setup


if __name__ == "__main__":
    setup()
