#!/usr/bin/env python3
"""
Uafhængig valideringssuite — runner.

For hver eksekverbar OECD-kontrol plantes ÉN målrettet defekt (synth.py), og det
bekræftes, at netop den kontrol fyrer i regelmotoren. Desuden bekræftes, at den
rene golden-GIR (gir_builder.build_base) ikke giver fund. Producerer en
valideringsrapport (Markdown) og exit-kode 0 hvis alt består — så suiten kan
bruges som CI-port og som dokumenteret korrektheds-bevis (tool validation).

Brug:
    python -m validation.run_validation            # kør + skriv rapport
    python -m validation.run_validation --quiet     # kun exit-kode
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from lxml import etree

from validator.rules import load_catalog
from validator.rules.oecd_rules import (
    load_oecd_rules, evaluate, switched_off_codes, coverage,
)
from validation.gir_builder import build_base
from validation.synth import synth_defect

REPORT_PATH = os.path.join(_REPO, "docs", "Pillar2-Validator_Valideringsrapport.md")


def _fired(xml: bytes, ruleset) -> set:
    """Returnér mængden af OECD-numre der fyrer på `xml`."""
    root = etree.fromstring(xml)
    return {v["rule"].get("oecd_rule") for v in evaluate(root, ruleset)}


def run_all():
    ruleset = load_oecd_rules()
    off = switched_off_codes()
    rules = [r for r in ruleset["rules"]
             if r.get("oecd_rule") and r["oecd_rule"] not in off]

    # Golden-base skal være ren (ingen OECD-fund).
    base_fired = _fired(build_base(), ruleset)
    base_ok = len(base_fired) == 0

    results = []
    for r in rules:
        code = r["oecd_rule"]
        level = r.get("level", "record")
        chk_type = r["check"]["type"]
        try:
            defect = synth_defect(r)
            if defect is None:
                results.append({"rule": code, "level": level, "type": chk_type,
                                "name": r["name_da"], "passed": None,
                                "fired": [], "error": "ingen auto-synth"})
                continue
            fired = _fired(defect, ruleset)
            passed = code in fired
            results.append({"rule": code, "level": level, "type": chk_type,
                            "name": r["name_da"], "passed": passed,
                            "fired": sorted(x for x in fired if x), "error": None})
        except Exception as exc:  # noqa: BLE001
            results.append({"rule": code, "level": level, "type": chk_type,
                            "name": r["name_da"], "passed": False,
                            "fired": [], "error": repr(exc)})

    return {"base_ok": base_ok, "base_fired": sorted(x for x in base_fired if x),
            "results": results, "catalog_version": load_catalog().catalog_version,
            "executable": coverage()["executable"]}


def _report_md(data) -> str:
    res = data["results"]
    auto = [r for r in res if r["passed"] is not None]
    npass = sum(1 for r in auto if r["passed"])
    nauto = len(auto)
    nman = len(res) - nauto
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    L = []
    L.append("# Valideringsrapport — Pillar II GIR-Validator")
    L.append("")
    L.append("Uafhængig valideringssuite: hver eksekverbar OECD-kontrol verificeres ved "
             "at plante ÉN målrettet defekt og bekræfte, at netop den tilsigtede kontrol "
             "udløses i regelmotoren — og at den rene golden-GIR ikke giver fund. Suiten "
             "er reproducerbar og køres som CI-port (`python -m validation.run_validation`).")
    L.append("")
    L.append(f"- **Genereret:** {ts}")
    L.append(f"- **Regelkatalog:** v{data['catalog_version']}")
    L.append(f"- **Eksekverbare kontroller:** {data['executable']}")
    L.append(f"- **Ren golden-GIR uden fund:** {'JA' if data['base_ok'] else 'NEJ — ' + ', '.join(data['base_fired'])}")
    L.append(f"- **Auto-scenarier bestået:** {npass} / {nauto}")
    if nman:
        L.append(f"- **Uden auto-scenarie (enhedstestet):** {nman}")
    L.append("")
    L.append("## Resultater")
    L.append("")
    L.append("| OECD-regel | Niveau | Check-type | Kontrol | Resultat | Udløste regler |")
    L.append("|---|---|---|---|---|---|")
    order = {"file": 0, "record": 1}
    for r in sorted(res, key=lambda x: (order.get(x["level"], 2), x["rule"])):
        if r["passed"] is None:
            status = "➖ Enhedstestet"
        elif r["passed"]:
            status = "✅ Bestået"
        else:
            status = "❌ FEJL"
        fired = ", ".join(r["fired"]) or "—"
        if r["error"] and r["passed"] is False:
            fired = f"FEJL: {r['error']}"
        elif r["error"]:
            fired = "—"
        L.append(f"| **{r['rule']}** | {r['level']} | {r['type']} | {r['name']} | "
                 f"{status} | {fired} |")
    L.append("")
    L.append("## Fortolkning")
    L.append("")
    L.append("«Bestået» betyder, at den tilsigtede kontrol (**fed**) optræder blandt de "
             "udløste regler for det defekte input. Et defekt-input kan realistisk udløse "
             "flere korrelerede kontroller; alle udløste regler vises for fuld transparens.")
    L.append("")
    L.append("Kontroller markeret «Enhedstestet» har ikke et auto-genereret defekt-scenarie "
             "(deres check-type kræver en kontekst, synthesizeren ikke bygger automatisk), "
             "men er dækket af enhedstest-suiten i `tests/`. Rapporten supplerer — den "
             "erstatter ikke — enhedstestene, og er tænkt som et uafhængigt, læsbart "
             "korrektheds-bevis.")
    L.append("")
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Kør den uafhængige valideringssuite.")
    ap.add_argument("--quiet", action="store_true", help="Kun exit-kode, ingen rapport.")
    args = ap.parse_args(argv)

    data = run_all()
    res = data["results"]
    auto = [r for r in res if r["passed"] is not None]
    npass = sum(1 for r in auto if r["passed"])
    all_ok = data["base_ok"] and npass == len(auto)

    if not args.quiet:
        os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
        with open(REPORT_PATH, "w", encoding="utf-8") as fh:
            fh.write(_report_md(data))
        print(f"Ren golden-GIR uden fund: {'JA' if data['base_ok'] else 'NEJ'}")
        for r in sorted(res, key=lambda x: (x["level"], x["rule"])):
            if r["passed"] is None:
                mark = "ENHEDSTEST"
            elif r["passed"]:
                mark = "OK  "
            else:
                mark = "FEJL"
            extra = "" if r["passed"] else f"  (udløste: {', '.join(r['fired']) or '—'}{'; '+r['error'] if r['error'] else ''})"
            print(f"  [{mark}] {r['rule']} — {r['name']}{extra if r['passed'] is False else ''}")
        print(f"\n{npass}/{len(auto)} auto-scenarier bestået. Rapport: {REPORT_PATH}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
