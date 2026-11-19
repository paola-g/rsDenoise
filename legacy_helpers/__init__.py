"""Archived, pre-consolidation copies of the helper forks.

These modules are kept for historical reference and for the few functions that
were unique to a fork.  They use legacy SciPy/NumPy APIs and require FSL; they
are loaded lazily by the root-level compatibility shims only when one of those
unique functions is requested.
"""
