"""BALAI regelkerne (delt design m. SAF-T): katalog, severity, profiler, fund.

Kopieret bevidst tæt på SAF-T-validatorens rules/-kerne, så modulerne senere
kan udtrækkes til ét delt bibliotek (mekanisk, ikke en refaktorering). Kun
katalog-stien (P2-Validation-Rules.json) og rule-id'erne (P2-*) afviger.
"""

from .catalog import CATALOG_PATH, Layer, Rule, RuleCatalog, load_catalog
from .finding import Finding, Location
from .profiles import (
    MaterialityProfile,
    Scope,
    default_profile,
    profiles_from_catalog,
    resolve_dynamic_severity,
)
from .severity import SEVERITY_BY_ID, BalSeverity, verdict_from_counts

__all__ = [
    "BalSeverity",
    "CATALOG_PATH",
    "Finding",
    "Layer",
    "Location",
    "MaterialityProfile",
    "Rule",
    "RuleCatalog",
    "SEVERITY_BY_ID",
    "Scope",
    "default_profile",
    "load_catalog",
    "profiles_from_catalog",
    "resolve_dynamic_severity",
    "verdict_from_counts",
]
