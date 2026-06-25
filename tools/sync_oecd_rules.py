#!/usr/bin/env python3
"""
Vedligehold + validér de maskinlæsbare OECD GIR-valideringsregler.

VIGTIGT: OECD publicerer IKKE de nummererede valideringsregler som en downloadbar
fil — de står i GIR XML Schema User Guide (jan. 2025) og juni-2026-guidance (PDF).
Reglerne curateres derfor manuelt ind i reference/oecd_validation_rules.json med
verificeret semantik, og dette værktøj LINTER den fil (struktur + at hver XPath
kan kompilere) i stedet for at hente noget. Samme rolle som en CI-port.

Brug:
    python tools/sync_oecd_rules.py --check     # lint + opsummering. Exit 0/1.
    python tools/sync_oecd_rules.py --list      # vis reglerne (id, level, type, nummer)

Kilde (curatér nye regler herfra):
  - GIR XML Schema: User Guide for Tax Administrations (jan. 2025)
  - Guidance on the Use of the GIR XML Schema and Validation Rules (juni 2026)
  Se schemas/SCHEMA_SOURCES.md for de officielle URLs.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = _THIS_DIR.parent
sys.path.insert(0, str(REPO_ROOT))

from validator.rules.oecd_rules import (  # noqa: E402
    RULES_PATH, load_oecd_rules, validate_ruleset, OecdRulesError,
)

EXIT_OK = 0
EXIT_ERROR = 1


def _check_xpaths(data: dict) -> list:
    """Bekræft at hver regels XPath(s) kan kompilere. Returnér fejl-linjer."""
    from lxml import etree
    ns = data["namespaces"]
    errors = []

    def compile_one(rid, where, expr):
        if not isinstance(expr, str) or not expr:
            return
        try:
            etree.XPath(expr, namespaces=ns)
        except etree.XPathSyntaxError as e:
            errors.append(f"  {rid}: ugyldig XPath i '{where}': {expr} ({e})")

    for r in data["rules"]:
        chk = r["check"]
        for key in ("xpath", "container", "require", "forbid", "left", "right",
                    "source", "target", "when"):
            if isinstance(chk.get(key), str):
                compile_one(r["id"], key, chk[key])
        # conditional: when/then er lister af {path, op, value}
        for key in ("when", "then"):
            if isinstance(chk.get(key), list):
                for cond in chk[key]:
                    compile_one(r["id"], f"{key}.path", cond.get("path"))
    return errors


def cmd_check() -> int:
    print("OECD-regler — lint")
    print("=" * 60)
    try:
        with open(RULES_PATH, "r", encoding="utf-8") as fh:
            import json
            data = json.load(fh)
        validate_ruleset(data)
    except FileNotFoundError:
        print(f"FEJL: {RULES_PATH} findes ikke.")
        return EXIT_ERROR
    except (OecdRulesError, ValueError) as e:
        print(f"FEJL: {e}")
        return EXIT_ERROR

    xpath_errors = _check_xpaths(data)
    if xpath_errors:
        print("FEJL: XPath-fejl:")
        print("\n".join(xpath_errors))
        return EXIT_ERROR

    rules = data["rules"]
    file_n = sum(1 for r in rules if r["level"] == "file")
    rec_n = sum(1 for r in rules if r["level"] == "record")
    confirmed = sum(1 for r in rules if r.get("oecd_rule"))
    print(f"Eksekverbare regler: {len(rules)} "
          f"({file_n} file-level, {rec_n} record-level), "
          f"{confirmed} med bekræftet OECD-nummer.")

    # Dækning mod det fulde katalog.
    from validator.rules.oecd_rules import coverage
    cov = coverage()
    print(f"Fuldt katalog: {cov['total_catalogue']} officielle regler "
          f"({cov['switched_off']} slået fra i 2026). "
          f"Eksekverbar dækning: {cov['executable']}/{cov['total_catalogue']}.")
    print("Resultat: OK — regelfilen er gyldig.")
    return EXIT_OK


def cmd_list() -> int:
    data = load_oecd_rules()
    print(f"{'ID':<24} {'LEVEL':<8} {'TYPE':<14} {'OECD#':<8} NAVN")
    print("-" * 78)
    for r in data["rules"]:
        print(f"{r['id']:<24} {r['level']:<8} {r['check']['type']:<14} "
              f"{str(r.get('oecd_rule') or '—'):<8} {r['name_da']}")
    return EXIT_OK


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Validér/vis OECD GIR-valideringsregler.")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true", help="Lint regelfilen.")
    g.add_argument("--list", action="store_true", help="Vis reglerne.")
    args = p.parse_args(argv)
    return cmd_list() if args.list else cmd_check()


if __name__ == "__main__":
    sys.exit(main())
