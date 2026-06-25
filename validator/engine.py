"""
Pillar II-valideringsmotor — offentligt indgangspunkt + delte datatyper.

Fase 0 (skelet): run_pipeline indlæser regelkataloget og kører lag 1's
well-formedness-tjek (P2-002) med XXE slået fra. Fuld XSD-validering (P2-001)
og lag 2-8 implementeres i de følgende faser — se ARCHITECTURE.md §9.

EngineOutcome-formatet er designet til at være stabilt, så senere lag kan
tilføjes uden at kaldere (app.py, tests) mærker forskel.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from .rules import (
    BalSeverity,
    Finding,
    Location,
    MaterialityProfile,
    RuleCatalog,
    load_catalog,
    verdict_from_counts,
)

from .xsd_validator import (
    GIR_NAMESPACE,
    GIR_ROOT_TAG,
    format_xsd_detail,
    safe_parser,
    validate_gir,
)

logger = logging.getLogger(__name__)

_NS = f"{{{GIR_NAMESPACE}}}"


# ---------------------------------------------------------------------------
# Delte dataclasses
# ---------------------------------------------------------------------------

@dataclass
class CompanyContext:
    """
    Metadata læst fra GIR'ens MessageSpec/header — identificerer *hvis* fil og
    *hvilken* periode der valideres. Alle felter er valgfri.
    """
    name: Optional[str] = None
    mne_group_id: Optional[str] = None           # koncern-id / TIN
    reporting_period: Optional[str] = None        # regnskabsår
    message_type: Optional[str] = None            # MessageTypeIndic
    message_ref_id: Optional[str] = None


@dataclass
class EngineOutcome:
    findings: List[Finding]
    layers_run: List[int]
    blocked_at_layer: Optional[int]
    profile: Optional[MaterialityProfile]
    namespace: Optional[str]
    gir_version: Optional[str]
    counts: Dict[BalSeverity, int] = field(default_factory=dict)
    company: CompanyContext = field(default_factory=CompanyContext)

    def counts_by_id(self, rule_id: str) -> Dict[BalSeverity, int]:
        out: Dict[BalSeverity, int] = defaultdict(int)
        for f in self.findings:
            if f.rule_id == rule_id:
                out[f.severity] += 1
        return dict(out)

    @property
    def verdict(self) -> str:
        return verdict_from_counts(self.counts)

    def to_dict(self) -> Dict:
        return {
            "verdict": self.verdict,
            "layers_run": self.layers_run,
            "blocked_at_layer": self.blocked_at_layer,
            "namespace": self.namespace,
            "gir_version": self.gir_version,
            "profile": self.profile.key if self.profile else None,
            "counts": {s.value: n for s, n in self.counts.items()},
            "company": vars(self.company),
            "findings": [f.to_dict() for f in self.findings],
        }


# ---------------------------------------------------------------------------
# Pipeline — offentligt indgangspunkt
# ---------------------------------------------------------------------------

def run_pipeline(
    file_path: str,
    profile_key: str = "standard",
    catalog: Optional[RuleCatalog] = None,
) -> EngineOutcome:
    """
    Kør valideringspipelinen over en GIR-fil.

    Fase 1 — lag 1 (Skema) + lag 2 (Struktur):
      Lag 1: well-formed XML (P2-002) og XSD-validering mod GIR-skemaet (P2-001).
             Ikke-parselbar XML blokerer (dybere lag er meningsløse).
      Lag 2: rod-element, MessageSpec, GLOBEBody, JurisdictionSection (P2-010..013)
             + udtræk af CompanyContext til rapporten.

    Lag 3-8 følger i senere faser (se ARCHITECTURE.md §9).
    """
    from lxml import etree

    catalog = catalog or load_catalog()
    profile = catalog.profile(profile_key)
    findings: List[Finding] = []
    layers_run: List[int] = []
    blocked_at: Optional[int] = None
    company = CompanyContext()
    namespace: Optional[str] = None
    gir_version: Optional[str] = None

    # --- Lag 1a: well-formedness ------------------------------------------
    layers_run.append(1)
    if not Path(file_path).exists():
        findings.append(catalog.build_finding(
            "P2-002", BalSeverity.CRITICAL,
            params={"line": 0, "detail": "filen findes ikke"},
            location=Location(line=0)))
        return _finalize(findings, layers_run, 1, profile, None, None, company)

    try:
        doc = etree.parse(file_path, safe_parser())
    except etree.XMLSyntaxError as e:
        line = getattr(e, "lineno", None) or 0
        findings.append(catalog.build_finding(
            "P2-002", BalSeverity.CRITICAL,
            params={"line": line, "detail": str(e)},
            location=Location(line=line)))
        return _finalize(findings, layers_run, 1, profile, None, None, company)

    # --- Lag 1b: XSD-validering -------------------------------------------
    xsd = validate_gir(file_path)
    if xsd["ran"] and not xsd["valid"]:
        for err in xsd["errors"]:
            findings.append(catalog.build_finding(
                "P2-001", BalSeverity.CRITICAL,
                params={"detail": format_xsd_detail(err)},
                location=Location(line=err.get("line"))))

    # --- Lag 2: strukturel integritet + CompanyContext --------------------
    layers_run.append(2)
    root = doc.getroot()
    namespace = _local_namespace(root)
    gir_version = root.get("version")

    if root.tag != GIR_ROOT_TAG:
        findings.append(catalog.build_finding(
            "P2-010", BalSeverity.CRITICAL,
            params={"found": root.tag},
            location=Location(line=root.sourceline, element=root.tag)))
        # Forkert rod → ingen meningsfuld videre strukturudtrækning.
        return _finalize(findings, layers_run, None, profile,
                         namespace, gir_version, company)

    mspec = root.find(f"{_NS}MessageSpec")
    if mspec is None:
        findings.append(catalog.build_finding(
            "P2-011", BalSeverity.CRITICAL, params={},
            location=Location(element="GLOBE_OECD")))
    else:
        company = _extract_company(root, mspec)

    bodies = root.findall(f"{_NS}GLOBEBody")
    if not bodies:
        findings.append(catalog.build_finding(
            "P2-012", BalSeverity.CRITICAL, params={},
            location=Location(element="GLOBE_OECD")))
    else:
        juris = sum(len(b.findall(f"{_NS}JurisdictionSection")) for b in bodies)
        if juris == 0:
            findings.append(catalog.build_finding(
                "P2-013", BalSeverity.MEDIUM, params={},
                location=Location(element="GLOBEBody")))

    # --- Lag 3-4: OECD-regler (file- og record-level) ---------------------
    _run_oecd_rules(root, catalog, findings, layers_run)

    return _finalize(findings, layers_run, None, profile,
                     namespace, gir_version, company)


def _run_oecd_rules(root, catalog, findings: List[Finding], layers_run: List[int]) -> None:
    """Evaluér de data-drevne OECD-regler (lag 3-4) og tilføj fund. Fejl i
    regelmotoren må aldrig vælte kørslen."""
    try:
        from .rules.oecd_rules import load_oecd_rules, evaluate as eval_oecd
        ruleset = load_oecd_rules()
    except Exception:
        logger.warning("kunne ikke indlæse OECD-regler", exc_info=True)
        return

    layers_run.extend([3, 4])
    try:
        violations = eval_oecd(root, ruleset)
    except Exception:
        logger.warning("OECD-regelmotor fejlede", exc_info=True)
        return

    for v in violations:
        rid = "P2-030" if v["level"] == "file" else "P2-040"
        rule = v["rule"]
        findings.append(catalog.build_finding(
            rid, BalSeverity.HIGH,
            params={
                "oecd": rule.get("oecd_rule") or rule["id"],
                "name": rule["name_da"],
                "detail": v["detail"],
                "fix": rule.get("fix_da", ""),
            },
            location=Location(line=v.get("line"), xpath=v.get("xpath"))))


# ---------------------------------------------------------------------------
# Hjælpere
# ---------------------------------------------------------------------------

def _finalize(findings, layers_run, blocked_at, profile, namespace,
              gir_version, company) -> EngineOutcome:
    counts: Dict[BalSeverity, int] = defaultdict(int)
    for f in findings:
        counts[f.severity] += 1
    return EngineOutcome(
        findings=findings,
        layers_run=layers_run,
        blocked_at_layer=blocked_at,
        profile=profile,
        namespace=namespace,
        gir_version=gir_version,
        counts=dict(counts),
        company=company,
    )


def _local_namespace(root) -> Optional[str]:
    tag = root.tag
    if isinstance(tag, str) and tag.startswith("{"):
        return tag[1:tag.index("}")]
    return None


def _extract_company(root, mspec) -> CompanyContext:
    """Læs identificerende metadata fra MessageSpec + første FilingInfo."""
    def t(parent, name):
        el = parent.find(f"{_NS}{name}")
        return el.text.strip() if el is not None and el.text else None

    name = None
    mne_group_id = None
    body = root.find(f"{_NS}GLOBEBody")
    if body is not None:
        fi = body.find(f"{_NS}FilingInfo")
        if fi is not None:
            name = t(fi, "NameMNE")
            fce = fi.find(f"{_NS}FilingCE")
            if fce is not None:
                mne_group_id = t(fce, "TIN")

    return CompanyContext(
        name=name,
        mne_group_id=mne_group_id,
        reporting_period=t(mspec, "ReportingPeriod"),
        message_type=t(mspec, "MessageTypeIndic"),
        message_ref_id=t(mspec, "MessageRefId"),
    )
