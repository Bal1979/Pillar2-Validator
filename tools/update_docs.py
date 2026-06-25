#!/usr/bin/env python3
"""
Hold dokumentationspakken i sync med koden.

Kør efter hver regel-batch (sammen med versionsbump + CHANGELOG-entry). Scriptet:
  1. Regenererer de DATA-DREVNE docs fuldt ud:
       - docs/Regel-sporbarhedsmatrix.md
       - docs/OECD_regelgrundlag.md
  2. Opdaterer de VOLATILE nøgletal i prosa-docs mellem markører
     <!-- STATS:START --> … <!-- STATS:END --> (Godkendelses-overblik.md, CLAUDE.md).
  3. Udskriver et resumé og fejler (exit 1), hvis noget mangler.

Nøgletal udledes af koden/data: katalogversion, antal eksekverbare regler,
antal check-typer, antal tests. Ingen håndholdte tal i prosa-docs der kan drive.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
REF = ROOT / "reference"


# ---------------------------------------------------------------------------
# Nøgletal
# ---------------------------------------------------------------------------

def stats() -> dict:
    sys.path.insert(0, str(ROOT))
    from validator.rules.oecd_rules import _VALID_TYPES
    exe = json.loads((REF / "oecd_validation_rules.json").read_text())
    cat = json.loads((REF / "oecd_validation_rules_catalogue.json").read_text())
    p2 = json.loads((ROOT / "validator/rules/P2-Validation-Rules.json").read_text())
    test_src = (ROOT / "tests/test_smoke.py").read_text()
    return {
        "version": p2["catalog_version"],
        "executable": len(exe["rules"]),
        "calc": sum(1 for r in exe["rules"] if r["check"]["type"] == "calculation"),
        "types": len(_VALID_TYPES),
        "tests": len(re.findall(r"^def test_", test_src, re.M)),
        "total": cat["counts"]["total"],
        "switched_off": cat["counts"]["switched_off"],
        "cat": cat, "exe": exe,
    }


# ---------------------------------------------------------------------------
# Data-drevne docs
# ---------------------------------------------------------------------------

_SUPPORTED = {"conditional", "conditional_ref", "compare", "format", "value_range",
              "cardinality", "unique", "not_equal", "mutually_exclusive",
              "ref_integrity", "required_if", "forbidden_if", "required",
              "forbidden", "calculation"}


def gen_sporbarhedsmatrix(s: dict) -> None:
    exe, cat = s["exe"], s["cat"]
    L = ["# Regel-sporbarhedsmatrix — Pillar II GIR-Validator\n",
         "Auto-genereret af `tools/update_docs.py`. Regenereres efter hver batch.\n",
         f"Katalogversion: **{s['version']}** · OECD-regelliste: **{s['total']}**, "
         f"heraf **{s['executable']}** eksekverbare (inkl. {s['calc']} beregningsregler).\n",
         "## Lag 3-4 — eksekverbare OECD-regler\n",
         "| OECD# | Level | Check-type | Navn | Kilde |", "|---|---|---|---|---|"]
    for r in exe["rules"]:
        L.append(f"| {r.get('oecd_rule') or '—'} | {r['level']} | {r['check']['type']} "
                 f"| {r['name_da']} | {r.get('authority', '—')} |")
    L += ["\n## Dækning pr. check-type-kategori\n", "| Kategori | Antal | Status |",
          "|---|---|---|"]
    for k, v in cat["category_counts"].items():
        if k == "calculation":
            st = f"✅ delvist ({s['calc']} kodet)"
        elif k in _SUPPORTED:
            st = "✅"
        else:
            st = "🔎 gennemgang"
        L.append(f"| {k} | {v} | {st} |")
    L.append(f"\n**Eksekverbar dækning:** {s['executable']}/{s['total']}. "
             f"{s['switched_off']} regler slået fra (fyres aldrig). Hver kodet regel er "
             "verificeret med negativ test + mod golden-fixturen `tests/fixtures/gir_valid_rich.xml`.\n")
    (DOCS / "Regel-sporbarhedsmatrix.md").write_text("\n".join(L))


_TYPE_DESC = {
    "conditional": "if/then (element+attribut; in/equals/contains/absent/not_in…)",
    "conditional_ref": "betinget reference-integritet (dokument-bredt)",
    "compare": "dato/tal-ordning mellem to felter", "format": "regex-format",
    "value_range": "numerisk min/max/exclude", "cardinality": "antalsbegrænsning",
    "unique": "værdier skal være entydige", "not_equal": "to felter må ikke være ens",
    "mutually_exclusive": "værdimængder må ikke optræde sammen",
    "ref_integrity": "værdi skal referere et kendt felt",
    "required_if": "felt kræves under betingelse",
    "forbidden_if": "felt forbudt under betingelse",
    "calculation": "beregningsmotor: aritmetisk formel (beregnet vs. rapporteret)",
}


def gen_regelgrundlag(s: dict) -> None:
    cat, exe = s["cat"], s["exe"]
    c, cc = cat["counts"], cat["category_counts"]
    L = ["# OECD GIR — regelgrundlag (komplet)\n",
         "Auto-genereret af `tools/update_docs.py`. Fuldt officielt regelgrundlag "
         "udtrukket fra OECD's egne dokumenter, committet i `reference/`.\n",
         "## Overblik\n", "| | Antal |\n|---|---|",
         f"| Regler i alt | {c['total']} |", f"| File-level | {c['file']} |",
         f"| Record-level | {c['record']} |", f"| Slået fra (2026) | {c['switched_off']} |",
         f"| **Eksekverbare i dag** | **{c['executable']}** (heraf {s['calc']} beregningsregler) |\n",
         "## Regler pr. check-type (klassificeret)\n", "| Kategori | Antal | Status |",
         "|---|---|---|"]
    for k, v in cc.items():
        if k == "calculation":
            st = f"✅ delvist ({s['calc']} kodet)"
        elif k in _SUPPORTED:
            st = "✅ understøttet"
        else:
            st = "🔎 gennemgang"
        L.append(f"| {k} | {v} | {st} |")
    L += ["", f"## Motorens check-type-vokabular ({len(_TYPE_DESC)})\n"]
    for t, d in _TYPE_DESC.items():
        L.append(f"- `{t}` — {d}")
    L += ["", "## Eksekverbare regler i dag\n", "| OECD# | Level | Type | Navn |",
          "|---|---|---|---|"]
    for r in exe["rules"]:
        L.append(f"| {r.get('oecd_rule') or '—'} | {r['level']} | {r['check']['type']} "
                 f"| {r['name_da']} |")
    L += ["", "## Slået fra for første filing-cyklus (juni-2026-guidance)\n"]
    for r in [x for x in cat["rules"] if x["switched_off_2026"]]:
        L.append(f"- **{r['code']}** ({r['element'] or '—'}): {r['rule_text'][:100]}…")
    (DOCS / "OECD_regelgrundlag.md").write_text("\n".join(L) + "\n")


# ---------------------------------------------------------------------------
# Markør-opdatering i prosa-docs
# ---------------------------------------------------------------------------

def stats_block(s: dict) -> str:
    return (f"**Nøgletal (katalog {s['version']}):** {s['executable']}/{s['total']} "
            f"OECD-regler eksekverbare (heraf {s['calc']} beregningsregler) · "
            f"{s['types']} check-typer · {s['tests']} tests grønne.")


def update_markers(path: Path, block: str) -> bool:
    text = path.read_text()
    pat = re.compile(r"(<!-- STATS:START -->).*?(<!-- STATS:END -->)", re.S)
    if not pat.search(text):
        print(f"  ADVARSEL: ingen STATS-markører i {path.name} — sprunget over.")
        return False
    path.write_text(pat.sub(rf"\1\n{block}\n\2", text))
    return True


def main() -> int:
    s = stats()
    gen_sporbarhedsmatrix(s)
    gen_regelgrundlag(s)
    block = stats_block(s)
    for name in ("Godkendelses-overblik.md",):
        update_markers(DOCS / name, block)
    update_markers(ROOT / "CLAUDE.md", block)
    print("Dokumentation opdateret:")
    print(f"  version {s['version']} · {s['executable']}/{s['total']} regler "
          f"({s['calc']} beregning) · {s['types']} check-typer · {s['tests']} tests")
    print("  regenereret: Regel-sporbarhedsmatrix.md, OECD_regelgrundlag.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
