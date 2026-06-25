"""
Præsentation: omsæt et EngineOutcome til en dansk rapport-kontekst, som
templates/rapport.html kan rendere. Holder app.py tynd og samler al
visnings-logik ét sted.
"""

from __future__ import annotations

from typing import Dict, List

from .engine import EngineOutcome
from .rules import BalSeverity, RuleCatalog

_VERDICT = {
    "afvist": {"label": "Afvist", "color": "#C23B22",
               "hint": "Filen har kritiske eller væsentlige fejl og bør rettes før indsendelse."},
    "betinget_godkendt": {"label": "Betinget godkendt", "color": "#D4A017",
                          "hint": "Ingen kritiske fejl, men der er forhold værd at gennemgå."},
    "godkendt": {"label": "Godkendt", "color": "#2E7D32",
                 "hint": "Ingen fund i de aktive kontroller."},
}

# Severity-rækkefølge til visning (kritisk øverst).
_SEV_ORDER = [BalSeverity.CRITICAL, BalSeverity.HIGH, BalSeverity.MEDIUM,
              BalSeverity.LOW, BalSeverity.INFO]


def build_report_context(outcome: EngineOutcome, catalog: RuleCatalog) -> Dict:
    """Byg en JSON-/template-venlig kontekst fra et outcome."""
    verdict = outcome.verdict
    v = _VERDICT.get(verdict, _VERDICT["godkendt"])

    # Severity-opsummering (kun niveauer med fund vises som chips).
    severity_summary: List[Dict] = []
    for sev in _SEV_ORDER:
        n = outcome.counts.get(sev, 0)
        if n:
            severity_summary.append({
                "label": sev.label_da, "color": sev.color, "count": n,
            })

    # Fund grupperet efter lag → severity, sorteret.
    by_layer: Dict[int, List] = {}
    for f in outcome.findings:
        by_layer.setdefault(f.layer, []).append(f)

    groups: List[Dict] = []
    for layer_id in sorted(by_layer):
        layer = catalog.layers.get(layer_id)
        items = sorted(by_layer[layer_id], key=lambda f: f.severity.order)
        groups.append({
            "layer_id": layer_id,
            "layer_label": layer.label_da if layer else f"Lag {layer_id}",
            "findings": [{
                "rule_id": f.rule_id,
                "name_da": catalog.rule(f.rule_id).name_da,
                "severity_label": f.severity.label_da,
                "severity_color": f.severity.color,
                "message_da": f.message_da,
                "suggested_fix_da": f.suggested_fix_da,
                "location": f.location.to_dict(),
            } for f in items],
        })

    return {
        "verdict": verdict,
        "verdict_label": v["label"],
        "verdict_color": v["color"],
        "verdict_hint": v["hint"],
        "total_findings": len(outcome.findings),
        "severity_summary": severity_summary,
        "groups": groups,
        "company": vars(outcome.company),
        "layers_run": outcome.layers_run,
        "blocked_at_layer": outcome.blocked_at_layer,
        "namespace": outcome.namespace,
        "gir_version": outcome.gir_version,
        "catalog_version": catalog.catalog_version,
    }
