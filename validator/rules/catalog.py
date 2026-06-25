"""
Regelkatalog-loader (delt design m. SAF-T).

Læser `P2-Validation-Rules.json` — single source of truth for regler,
severity-niveauer, lag og materialitetsprofiler. Udstiller et `RuleCatalog`-
objekt motoren bruger til at udsende fund.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .finding import Finding, Location
from .profiles import MaterialityProfile, profiles_from_catalog, default_profile
from .severity import SEVERITY_BY_ID, BalSeverity


CATALOG_PATH = Path(__file__).with_name("P2-Validation-Rules.json")


@dataclass(frozen=True)
class Rule:
    id: str                             # "P2-001"
    layer: int
    severity: Optional[BalSeverity]     # None når dynamic
    name_da: str
    message_template_da: str
    suggested_fix_da: Optional[str] = None
    formula: Optional[str] = None
    default_enabled: bool = True
    # Pillar II-specifikke, valgfri felter (referencesporbarhed):
    oecd_rule: Optional[str] = None     # OECD-regelnummer, fx "70106"
    authority: Optional[str] = None     # kilde: OECD / guidance-2026-06 / DK-hjemmel

    @property
    def is_dynamic(self) -> bool:
        return self.severity is None


@dataclass(frozen=True)
class Layer:
    id: int
    key: str
    label_da: str


@dataclass
class RuleCatalog:
    catalog_version: str
    catalog_released: str
    rules: Dict[str, Rule]
    layers: Dict[int, Layer]
    profiles: Dict[str, MaterialityProfile]
    severity_meta: List[Dict[str, Any]] = field(default_factory=list)
    raw: Dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Opslag
    # ------------------------------------------------------------------
    def rule(self, rule_id: str) -> Rule:
        try:
            return self.rules[rule_id]
        except KeyError as exc:
            raise KeyError(f"Unknown rule id: {rule_id!r}") from exc

    def default_profile(self) -> MaterialityProfile:
        return default_profile(self.profiles)

    def profile(self, key: str) -> MaterialityProfile:
        try:
            return self.profiles[key]
        except KeyError as exc:
            raise KeyError(f"Unknown materiality profile: {key!r}") from exc

    # ------------------------------------------------------------------
    # Finding-fabrik — håndhæver konsistent form på alle emit-steder.
    # ------------------------------------------------------------------
    def build_finding(
        self,
        rule_id: str,
        severity: BalSeverity,
        params: Dict[str, Any],
        location: Optional[Location] = None,
        diff: Optional[float] = None,
    ) -> Finding:
        """
        Render en Finding ud fra rule_id + params.

        `severity` skal være eksplicit — for dynamiske regler resolver
        kalderen den via profiles.resolve_dynamic_severity først.
        """
        rule = self.rule(rule_id)
        if rule.is_dynamic is False and rule.severity != severity:
            # Statiske regler kan kun udsende deres katalog-severity.
            raise ValueError(
                f"Rule {rule_id} is static ({rule.severity.value}) but engine "
                f"tried to emit {severity.value}"
            )

        message = _safe_format(rule.message_template_da, params)
        fix = (
            _safe_format(rule.suggested_fix_da, params)
            if rule.suggested_fix_da else None
        )

        return Finding(
            rule_id=rule.id,
            layer=rule.layer,
            severity=severity,
            message_da=message,
            params=dict(params),
            suggested_fix_da=fix,
            location=location or Location(),
            diff=diff,
        )


def _safe_format(template: str, params: Dict[str, Any]) -> str:
    """
    Render en besked-skabelon. Manglende nøgler efterlades som `{key}`, så en
    brudt skabelon er synlig for udviklere — ikke et crash i prod.
    """
    class _Missing(dict):
        def __missing__(self, key: str) -> str:  # type: ignore[override]
            return "{" + key + "}"

    try:
        return template.format_map(_Missing(params))
    except Exception:
        return template


def _load_rule(raw: Dict[str, Any]) -> Rule:
    sev_raw = raw["severity"]
    if sev_raw == "dynamic":
        severity: Optional[BalSeverity] = None
    else:
        severity = SEVERITY_BY_ID[sev_raw]

    return Rule(
        id=raw["id"],
        layer=int(raw["layer"]),
        severity=severity,
        name_da=raw["name_da"],
        message_template_da=raw["message_da"],
        suggested_fix_da=raw.get("suggested_fix_da"),
        formula=raw.get("formula"),
        default_enabled=bool(raw.get("default_enabled", True)),
        oecd_rule=raw.get("oecd_rule"),
        authority=raw.get("authority"),
    )


def _load_layer(raw: Dict[str, Any]) -> Layer:
    return Layer(id=int(raw["id"]), key=raw["key"], label_da=raw["label_da"])


def load_catalog(path: Optional[Path] = None) -> RuleCatalog:
    path = path or CATALOG_PATH
    with open(path, "r", encoding="utf-8") as fh:
        raw = json.load(fh)

    rules = {r["id"]: _load_rule(r) for r in raw["rules"]}
    layers = {int(l["id"]): _load_layer(l) for l in raw["layers"]}
    profiles = profiles_from_catalog(raw["materiality_profiles"])

    return RuleCatalog(
        catalog_version=raw["catalog_version"],
        catalog_released=raw["catalog_released"],
        rules=rules,
        layers=layers,
        profiles=profiles,
        severity_meta=raw.get("severity_levels", []),
        raw=raw,
    )
