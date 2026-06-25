"""
Materialitetsprofiler + dynamisk severity-resolver (delt design m. SAF-T).

En profil definerer de absolutte og relative tærskler, der bruges til at
triagere fund på de lag, hvor severity beregnes ud fra den faktiske diff
i stedet for at være hårdkodet på reglen (i Pillar II især lag 6 — GIR/QDMTT).

Feltnavnene (line_absolute/account_absolute/relative_ppt) er bevaret fra
SAF-T-kernen, så modulet kan deles. I Pillar II-kontekst læses de generisk:
"per post" og "per jurisdiktion". Tærsklerne kalibreres i Fase 4-5.

Dynamisk regel:
    severity = LOW     hvis |diff| <= absolute_floor
               MEDIUM  hvis |diff| <= relative_ceiling * basis
               HIGH    ellers
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Literal

from .severity import BalSeverity


Scope = Literal["line", "account"]


@dataclass(frozen=True)
class MaterialityProfile:
    key: str                        # "standard", "konservativ", "lempelig"
    label_da: str
    use_case_da: str
    line_absolute_dkk: float        # generisk: pr. post
    account_absolute_dkk: float     # generisk: pr. jurisdiktion / aggregat
    relative_ppt: float             # promille (‰) af basis
    is_default: bool = False

    def absolute_floor(self, scope: Scope) -> float:
        if scope == "line":
            return self.line_absolute_dkk
        if scope == "account":
            return self.account_absolute_dkk
        raise ValueError(f"Unknown scope: {scope!r}")

    def relative_ceiling(self, basis: float) -> float:
        """Promille → fraktion; værn mod nul/negativ basis."""
        if basis is None or basis <= 0:
            return 0.0
        return (self.relative_ppt / 1000.0) * basis


def resolve_dynamic_severity(
    diff: float,
    profile: MaterialityProfile,
    scope: Scope,
    basis: float,
) -> BalSeverity:
    """
    Afgør severity for regler markeret severity='dynamic'.

    `diff` er signeret; vi bruger |diff|. `scope` vælger hvilken absolut
    tærskel der gælder.
    """
    abs_diff = abs(diff)
    floor = profile.absolute_floor(scope)

    if abs_diff <= floor:
        return BalSeverity.LOW

    ceiling = profile.relative_ceiling(basis)
    if ceiling > 0 and abs_diff <= ceiling:
        return BalSeverity.MEDIUM

    return BalSeverity.HIGH


def profiles_from_catalog(raw: Dict[str, dict]) -> Dict[str, MaterialityProfile]:
    """Konvertér katalogets `materiality_profiles`-blok til objekter."""
    out: Dict[str, MaterialityProfile] = {}
    for key, spec in raw.items():
        out[key] = MaterialityProfile(
            key=key,
            label_da=spec["label_da"],
            use_case_da=spec.get("use_case_da", ""),
            line_absolute_dkk=float(spec["line_absolute_dkk"]),
            account_absolute_dkk=float(spec["account_absolute_dkk"]),
            relative_ppt=float(spec["relative_ppt"]),
            is_default=bool(spec.get("default", False)),
        )
    return out


def default_profile(profiles: Dict[str, MaterialityProfile]) -> MaterialityProfile:
    for p in profiles.values():
        if p.is_default:
            return p
    if "standard" in profiles:
        return profiles["standard"]
    raise ValueError("No default materiality profile defined")
