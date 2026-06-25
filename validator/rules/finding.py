"""
Finding-dataclass for Pillar II-validatorens output (delt design m. SAF-T).

En Finding er den atomare enhed motoren producerer. Hvert fund bærer:
- rule_id (P2-*) og severity resolvet ved emit
- layer (1–8 fra pipelinen)
- en renderet, læsbar dansk besked + de rå params
- en Location der peger tilbage i kilde-XML'en (linje + XPath — OECD's egne
  fejlrapporter peger netop med XPath)
- valgfri diff (beløb) brugt af KPI-summer og dynamisk severity
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Optional

from .severity import BalSeverity


@dataclass
class Location:
    """
    Hvor fundet lever i kilde-XML'en.

    Hvert felt er best-effort — lxml giver linjenumre under parse, XPath bygges
    ved at gå træet igennem, og element_id fanger den forretningslæsbare nøgle
    (fx DocRefId, jurisdiktion, ConstituentEntity-id).
    """

    line: Optional[int] = None
    xpath: Optional[str] = None
    element: Optional[str] = None       # tag-navn, fx "JurisdictionSection"
    element_id: Optional[str] = None    # forretnings-id: DocRefId, jurisdiktion, …
    snippet: Optional[str] = None       # valgfrit råt XML-fragment til UI
    parent_id: Optional[str] = None     # fx GIR-sektion når element er en post

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class Finding:
    rule_id: str                        # "P2-001"
    layer: int                          # 1..8
    severity: BalSeverity               # resolvet (aldrig "dynamic" her)
    message_da: str                     # renderet fra skabelon
    params: Dict[str, Any] = field(default_factory=dict)
    suggested_fix_da: Optional[str] = None
    location: Location = field(default_factory=Location)
    diff: Optional[float] = None        # signeret beløbsmæssig effekt, hvis relevant

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "layer": self.layer,
            "severity": self.severity.value,
            "severity_label_da": self.severity.label_da,
            "message_da": self.message_da,
            "params": self.params,
            "suggested_fix_da": self.suggested_fix_da,
            "location": self.location.to_dict(),
            "diff": self.diff,
        }
