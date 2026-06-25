"""
XSD-validering af GIR-filer mod OECD's officielle skema (pipeline-lag 1).

Validerer DIREKTE mod schemas/gir/GLOBEXML_v1.0.xsd (som importerer
isoglobetypes + oecdglobetypes) — ikke mod en gengivelse. XXE er slået fra.
Det kompilerede skema caches, så gentagne kørsler er hurtige.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Dict, List

from lxml import etree

_THIS = os.path.dirname(os.path.abspath(__file__))
SCHEMAS_DIR = os.path.join(os.path.dirname(_THIS), "schemas")
GIR_SCHEMA_PATH = os.path.join(SCHEMAS_DIR, "gir", "GLOBEXML_v1.0.xsd")

# OECD GIR-namespace + rod-element (bekræftet i GLOBEXML_v1.0.xsd).
GIR_NAMESPACE = "urn:oecd:ties:globe:v2"
GIR_ROOT_TAG = f"{{{GIR_NAMESPACE}}}GLOBE_OECD"

# Maks. antal unikke XSD-fejl vi medtager — en gennem-ugyldig fil kan ellers
# generere tusindvis. Identiske beskeder rulles sammen med en tæller.
MAX_XSD_ERRORS = 200


def safe_parser() -> etree.XMLParser:
    """Parser med XXE-beskyttelse (ingen entitetsopløsning, intet netværk)."""
    return etree.XMLParser(resolve_entities=False, no_network=True, huge_tree=True)


@lru_cache(maxsize=1)
def load_gir_schema() -> etree.XMLSchema:
    """Indlæs og kompilér GIR-skemaet (cachet). Importerne opløses relativt
    til skemafilens placering i schemas/gir/."""
    schema_doc = etree.parse(GIR_SCHEMA_PATH, safe_parser())
    return etree.XMLSchema(schema_doc)


def validate_gir(file_path: str) -> Dict:
    """
    Validér en GIR-fil mod skemaet.

    Returnerer:
      {
        "ran": bool,            # kørte valideringen (False hvis ikke parselbar)
        "valid": bool,
        "errors": [ {"line": int, "message": str, "count": int} ],
        "truncated": bool,
        "parse_error": str|None,
      }
    Forudsætter ikke well-formedness — håndterer parse-fejl pænt.
    """
    try:
        doc = etree.parse(file_path, safe_parser())
    except etree.XMLSyntaxError as e:
        return {"ran": False, "valid": False, "errors": [],
                "truncated": False, "parse_error": str(e)}

    schema = load_gir_schema()
    valid = schema.validate(doc)
    if valid:
        return {"ran": True, "valid": True, "errors": [],
                "truncated": False, "parse_error": None}

    # Rul identiske beskeder sammen (samme tekst → ét fund med tæller).
    seen: Dict[str, Dict] = {}
    truncated = False
    for entry in schema.error_log:
        key = entry.message
        if key in seen:
            seen[key]["count"] += 1
            continue
        if len(seen) >= MAX_XSD_ERRORS:
            truncated = True
            break
        seen[key] = {"line": entry.line, "message": entry.message, "count": 1}

    return {"ran": True, "valid": False, "errors": list(seen.values()),
            "truncated": truncated, "parse_error": None}


def format_xsd_detail(err: Dict) -> str:
    """Byg en kort dansk-venlig detalje til en P2-001-besked."""
    msg = err.get("message", "").strip()
    count = err.get("count", 1)
    if count > 1:
        return f"{msg} (forekommer {count} gange)"
    return msg
