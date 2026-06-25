"""
BALAI 5-niveau severity-model (delt design m. SAF-T).

Fem ordnede niveauer — Kritisk > Væsentlig > Medium > Lav > Info.
Severity er en egenskab på reglen, undtagen regler markeret `dynamic`,
hvor den beregnes ud fra materialitetsprofilen på kørselstidspunktet.
"""

from __future__ import annotations

from enum import Enum
from typing import Dict


class BalSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

    @property
    def order(self) -> int:
        return _ORDER[self]

    @property
    def label_da(self) -> str:
        return _LABEL_DA[self]

    @property
    def label_en(self) -> str:
        return _LABEL_EN[self]

    @property
    def color(self) -> str:
        return _COLOR[self]


_ORDER: Dict[BalSeverity, int] = {
    BalSeverity.CRITICAL: 1,
    BalSeverity.HIGH: 2,
    BalSeverity.MEDIUM: 3,
    BalSeverity.LOW: 4,
    BalSeverity.INFO: 5,
}

_LABEL_DA: Dict[BalSeverity, str] = {
    BalSeverity.CRITICAL: "Kritisk",
    BalSeverity.HIGH: "Væsentlig",
    BalSeverity.MEDIUM: "Medium",
    BalSeverity.LOW: "Lav",
    BalSeverity.INFO: "Info",
}

_LABEL_EN: Dict[BalSeverity, str] = {
    BalSeverity.CRITICAL: "Critical",
    BalSeverity.HIGH: "High",
    BalSeverity.MEDIUM: "Medium",
    BalSeverity.LOW: "Low",
    BalSeverity.INFO: "Info",
}

_COLOR: Dict[BalSeverity, str] = {
    BalSeverity.CRITICAL: "#C23B22",
    BalSeverity.HIGH: "#E07B00",
    BalSeverity.MEDIUM: "#D4A017",
    BalSeverity.LOW: "#6B7280",
    BalSeverity.INFO: "#2E5C8A",
}


SEVERITY_BY_ID: Dict[str, BalSeverity] = {s.value: s for s in BalSeverity}


def verdict_from_counts(counts: Dict[BalSeverity, int]) -> str:
    """
    Map severity-tællinger → samlet dom.

    - afvist            → mindst ét CRITICAL- eller HIGH-fund
    - betinget_godkendt → kun MEDIUM/LOW-fund
    - godkendt          → ingen fund (eller kun INFO)
    """
    if counts.get(BalSeverity.CRITICAL, 0) > 0 or counts.get(BalSeverity.HIGH, 0) > 0:
        return "afvist"
    if counts.get(BalSeverity.MEDIUM, 0) > 0 or counts.get(BalSeverity.LOW, 0) > 0:
        return "betinget_godkendt"
    return "godkendt"
