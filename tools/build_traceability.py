#!/usr/bin/env python3
"""
build_traceability.py — auto-genererer sporbarhedsmatrixen (xlsx) for Pillar II
GIR-Validator fra regel-JSON + det fulde katalog + referencedata-provenance +
den uafhængige valideringssuite.

  docs/Pillar2-Validator_Regel-sporbarhedsmatrix.xlsx

Faner:
  1. Sporbarhed           – hver eksekverbar OECD-kontrol → kilde → modul → test
  2. Fuldt katalog        – alle 163 officielle regler (eksekverbar / switched-off)
  3. Referencedata        – OECD-skemaernes provenance (fil, kilde, hash, dato)
  4. Severity & materialitet – severity-niveauer + materialitetsprofiler

Alt udledes fra kataloget, så matrixen aldrig kommer ud af sync. Kør efter
enhver katalogændring:

    python3 tools/build_traceability.py
"""

import json
import os
import sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from validator.rules import load_catalog
from validator.rules.oecd_rules import (
    load_oecd_rules, load_catalogue, switched_off_codes, coverage,
)

DOCS = os.path.join(ROOT, "docs")
OUT = os.path.join(DOCS, "Pillar2-Validator_Regel-sporbarhedsmatrix.xlsx")

FONT = "Arial"
NAVY = "1B365D"
HEADER_FONT = Font(name=FONT, bold=True, color="FFFFFF", size=10)
HEADER_FILL = PatternFill("solid", fgColor=NAVY)
BODY_FONT = Font(name=FONT, size=10)
WRAP = Alignment(vertical="top", wrap_text=True)
MODULE = "validator/rules/oecd_rules.py (datadrevet motor)"


def _style(ws, headers, widths):
    for col, (head, width) in enumerate(zip(headers, widths), start=1):
        c = ws.cell(row=1, column=col, value=head)
        c.font = HEADER_FONT
        c.fill = HEADER_FILL
        c.alignment = WRAP
        ws.column_dimensions[get_column_letter(col)].width = width
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(headers))}1"


def _row(ws, values):
    ws.append(values)
    for c in ws[ws.max_row]:
        c.font = BODY_FONT
        c.alignment = WRAP


def _validation_coverage():
    """Kør valideringssuiten og returnér {oecd_rule: 'Ja (auto)' | 'Enhedstest'}."""
    try:
        from validation.run_validation import run_all
        data = run_all()
        cov = {}
        for r in data["results"]:
            if r["passed"] is True:
                cov[r["rule"]] = "Ja — auto-scenarie (bestået)"
            elif r["passed"] is None:
                cov[r["rule"]] = "Enhedstest (intet auto-scenarie)"
            else:
                cov[r["rule"]] = "FEJL — scenarie udløste ikke"
        return cov, data["base_ok"]
    except Exception as exc:  # noqa: BLE001
        return {}, None


def sheet_sporbarhed(wb, rules, cov):
    ws = wb.active
    ws.title = "Sporbarhed"
    _style(ws, ["OECD#", "Niveau", "Check-type", "Kontrol", "Autoritativ kilde",
                "Implementering (modul)", "Valideringsscenarie", "Severity"],
           [10, 9, 16, 44, 50, 34, 30, 12])
    for r in sorted(rules, key=lambda x: (0 if x["level"] == "file" else 1,
                                          x.get("oecd_rule", ""))):
        code = r.get("oecd_rule", r["id"])
        _row(ws, [
            code, r["level"], r["check"]["type"], r["name_da"],
            r.get("authority", ""), MODULE,
            cov.get(code, "—"),
            "Væsentlig (High)",
        ])


def sheet_katalog(wb, catalogue, impl_codes, off):
    ws = wb.create_sheet("Fuldt katalog")
    _style(ws, ["Kode", "Niveau", "Kategori", "Eksekverbar", "Switched-off 2026",
                "Target (XPath)", "Reference"],
           [10, 9, 18, 13, 18, 52, 30])
    for r in catalogue["rules"]:
        _row(ws, [
            r["code"], r.get("level", ""), r.get("category", ""),
            "Ja" if r["code"] in impl_codes else "Nej",
            "Ja (fyres aldrig)" if r["code"] in off else "Nej",
            r.get("target") or "", r.get("reference") or "",
        ])


def sheet_referencedata(wb):
    ws = wb.create_sheet("Referencedata")
    _style(ws, ["Artefakt", "Filer", "Kilde", "Hentet", "ZIP SHA-256"],
           [22, 46, 30, 22, 66])
    for label, rel in [("OECD GIR XML Schema", "schemas/gir/_provenance.json"),
                       ("OECD GIR Status Message Schema", "schemas/status/_provenance.json")]:
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            continue
        prov = json.load(open(p, encoding="utf-8"))
        _row(ws, [label, ", ".join(prov.get("files", [])),
                  prov.get("source_url", ""), prov.get("downloaded_at", ""),
                  prov.get("zip_sha256", "")])
    ws.append([])
    _row(ws, ["Nummererede regler", "oecd_validation_rules_catalogue.json",
              "GIR Status Message User Guide (juli 2025) Part 4",
              "udtrukket", "— (PDF-kilde, se docs/oecd_sources/)"])
    _row(ws, ["Guidance-afvigelser", "guidance_deviations_2026-06.json",
              "OECD GloBE Information Return — June 2026 guidance",
              "udtrukket", "—"])


def sheet_severity(wb, cat):
    ws = wb.create_sheet("Severity & materialitet")
    _style(ws, ["Severity-niveau", "Label (DA)", "Rækkefølge", "Synlighed"],
           [16, 16, 12, 22])
    raw = json.load(open(os.path.join(ROOT, "validator/rules/P2-Validation-Rules.json"),
                         encoding="utf-8"))
    for s in raw.get("severity_levels", []):
        _row(ws, [s["id"], s.get("label_da", ""), s.get("order", ""),
                  s.get("default_visibility", "")])
    ws.append([])
    _row(ws, ["Materialitetsprofil", "Label", "Brug", "Linje / Konto / Relativ"])
    for c in ws[ws.max_row]:
        c.font = HEADER_FONT
        c.fill = HEADER_FILL
        c.alignment = WRAP
    for key, p in raw.get("materiality_profiles", {}).items():
        thresh = f"{p.get('line_absolute_dkk')} / {p.get('account_absolute_dkk')} / {p.get('relative_ppt')}%"
        _row(ws, [key, p.get("label_da", ""), p.get("use_case_da", ""), thresh])


def main():
    cat = load_catalog()
    ruleset = load_oecd_rules()
    rules = [r for r in ruleset["rules"] if r.get("oecd_rule")]
    catalogue = load_catalogue()
    off = switched_off_codes()
    impl_codes = {r["oecd_rule"] for r in rules}
    cov, base_ok = _validation_coverage()

    wb = Workbook()
    sheet_sporbarhed(wb, rules, cov)
    sheet_katalog(wb, catalogue, impl_codes, off)
    sheet_referencedata(wb)
    sheet_severity(wb, cat)

    os.makedirs(DOCS, exist_ok=True)
    wb.save(OUT)
    c = coverage()
    print(f"Skrev {OUT}")
    print(f"  Katalogversion: {cat.catalog_version}")
    print(f"  Eksekverbare: {c['executable']}/{c['total_catalogue']} "
          f"(switched-off: {c['switched_off']})")
    print(f"  Valideringssuite golden ren: {base_ok}")


if __name__ == "__main__":
    main()
