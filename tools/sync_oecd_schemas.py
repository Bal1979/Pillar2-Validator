#!/usr/bin/env python3
"""
Synkroniser OECD's officielle GIR-skemaer til Pillar II-validatoren.

Henter de to officielle XML Schema-ZIP'er fra OECD's Tax Transparency Resource
Centre og udpakker XSD'erne til projektets schemas/-mappe, så de ligger klar som
SOURCE OF TRUTH (samme princip og stil som SAF-T's tools/sync_erst_reference.py):

  1. GIR XML Schema            -> schemas/gir/      (input vi validerer, lag 1)
  2. GIR Status Message Schema -> schemas/status/   (output-format, fejlrapportering)

OECD opdaterer løbende både skema og valideringsregler (jf. juni-2026-guidance),
så en forældet lokal kopi kan afvise gyldige filer. Kør derfor jævnligt --check.

Brug:
    python tools/sync_oecd_schemas.py --check
        Hent og sammenlign med de lokale kopier (skriver INTET). Dansk opsummering.
        Exit: 0 = alt aktuelt, 10 = mindst én opdatering findes, 1 = fejl.

    python tools/sync_oecd_schemas.py --apply
        Som --check, men udpak og skriv opdateringer til schemas/. Exit: 0 = ok
        (uanset om der var noget at opdatere), 1 = fejl.

    python tools/sync_oecd_schemas.py --import \
        --gir-zip ~/Downloads/globe-xsd.zip \
        --status-zip ~/Downloads/xml-schema-gir-status-message.zip
        Importér ZIP'er du selv har hentet i browseren (anbefalet vej, da OECD's
        CDN ofte afviser automatiseret download med HTTP 403). Udpakker til
        schemas/ præcis som --apply. Mindst én af --gir-zip/--status-zip kræves.

Hvis OECD ændrer download-URL'erne kan de overstyres:
    --gir-zip-url <URL>      (eller miljøvariabel OECD_GIR_ZIP_URL)
    --status-zip-url <URL>   (eller miljøvariabel OECD_STATUS_ZIP_URL)
Det rigtige link findes ved at højreklikke "XML Schema (ZIP)" på OECD-siden ->
"Kopiér linkadresse". Mislykkes de indbyggede URL'er, prøver scriptet desuden at
scrape linket fra resource-centre-siden automatisk.

Kun standardbiblioteket bruges (ingen tredjepartsafhængigheder).
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import ssl
import sys
import urllib.error
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Konfiguration
# ---------------------------------------------------------------------------

_THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = _THIS_DIR.parent
SCHEMAS_DIR = REPO_ROOT / "schemas"

# OECD's samleside (bruges til scrape-fallback hvis de direkte URL'er fejler).
RESOURCE_CENTRE_URL = (
    "https://www.oecd.org/en/topics/sub-issues/"
    "international-standards-on-tax-transparency/tax-transparency-resource-centre.html"
)

# Officielle direkte ZIP-URL'er (verificeret på OECD's resource centre, juni 2026).
GIR_ZIP_URL = (
    "https://www.oecd.org/content/dam/oecd/en/topics/policy-sub-issues/"
    "global-minimum-tax/globe-xsd.zip"
)
STATUS_ZIP_URL = (
    "https://www.oecd.org/content/dam/oecd/en/topics/policy-issues/"
    "tax-transparency-and-international-co-operation/xml-schema-gir-status-message.zip"
)

PROVENANCE_NAME = "_provenance.json"

# Et "bundle" = ét skema vi henter. scrape_hints bruges hvis URL'en fejler:
# linktekst-mønstre der identificerer den rigtige ZIP på resource-centre-siden.
SCHEMA_BUNDLES = [
    {
        "key": "gir",
        "label": "GIR XML Schema (input, lag 1)",
        "zip_url": GIR_ZIP_URL,
        "env": "OECD_GIR_ZIP_URL",
        "target": SCHEMAS_DIR / "gir",
        "scrape_hints": ["globe-xsd", "global-minimum-tax"],
        "expect": ["globe", "gir"],   # mindst ét XSD-navn bør indeholde et af disse
    },
    {
        "key": "status",
        "label": "GIR Status Message XML Schema (output)",
        "zip_url": STATUS_ZIP_URL,
        "env": "OECD_STATUS_ZIP_URL",
        "target": SCHEMAS_DIR / "status",
        "scrape_hints": ["gir-status-message", "status-message"],
        "expect": ["status"],
    },
]

EXIT_OK = 0
EXIT_UPDATE_AVAILABLE = 10
EXIT_ERROR = 1

# OECD's CDN (Akamai) afviser "Python-agtige" klienter med HTTP 403. Vi sender
# derfor almindelige browser-headers — det er stadig en helt normal download af en
# offentlig fil, blot med en User-Agent CDN'en accepterer.
_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)
_BROWSER_HEADERS = {
    "User-Agent": _UA,
    "Accept": "application/zip,application/octet-stream,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,da;q=0.8",
    "Referer": RESOURCE_CENTRE_URL,
    "Connection": "keep-alive",
}


class SyncError(Exception):
    """Fejl der skal stoppe kørslen med en dansk besked (ingen skrivning)."""


# ---------------------------------------------------------------------------
# Netværk
# ---------------------------------------------------------------------------

def _ssl_context() -> ssl.SSLContext:
    # Normal verificering. Hvis et miljø mangler CA-bundle kan man sætte
    # PILLAR2_INSECURE_SSL=1, men det frarådes (kun til fejlfinding).
    if os.environ.get("PILLAR2_INSECURE_SSL") == "1":
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx
    # macOS-Python (python.org/Homebrew) mangler ofte et lokalt CA-bundle, så
    # TLS-verificering fejler med CERTIFICATE_VERIFY_FAILED. Brug certifi's
    # bundle hvis det er installeret — ellers OS'ets standard. certifi er ikke
    # en hård afhængighed; scriptet kører på stdlib alene hvor OS leverer certs.
    try:
        import certifi  # type: ignore
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def fetch_bytes(url: str, timeout: int = 60) -> bytes:
    req = urllib.request.Request(url, headers=_BROWSER_HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=_ssl_context()) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        raise SyncError(f"HTTP {e.code} ved hentning af {url}") from e
    except urllib.error.URLError as e:
        raise SyncError(f"Netværksfejl ved hentning af {url}: {e.reason}") from e


def scrape_zip_url(hints: List[str]) -> Optional[str]:
    """Find en .zip-URL på resource-centre-siden, hvis et hint matcher href'en."""
    try:
        html = fetch_bytes(RESOURCE_CENTRE_URL).decode("utf-8", "replace")
    except SyncError:
        return None
    hrefs = re.findall(r'href=["\']([^"\']+\.zip)["\']', html, flags=re.IGNORECASE)
    for href in hrefs:
        low = href.lower()
        if any(h in low for h in hints):
            if href.startswith("/"):
                return "https://www.oecd.org" + href
            return href
    return None


def resolve_zip_url(bundle: dict, override: Optional[str]) -> str:
    """Vælg ZIP-URL: CLI-override > miljøvariabel > indbygget > scrape-fallback."""
    if override:
        return override
    env_val = os.environ.get(bundle["env"])
    if env_val:
        return env_val
    return bundle["zip_url"]


# ---------------------------------------------------------------------------
# ZIP-håndtering (rene funktioner — testbare)
# ---------------------------------------------------------------------------

def _safe_members(zf: zipfile.ZipFile) -> List[str]:
    """Returnér filnavne i zip'en uden mapper og uden sti-traversal (zip-slip)."""
    out: List[str] = []
    for name in zf.namelist():
        if name.endswith("/"):
            continue
        norm = os.path.normpath(name)
        if norm.startswith("..") or os.path.isabs(norm) or norm.startswith("/"):
            raise SyncError(f"Usikkert sti-navn i zip: {name!r} — afbryder.")
        out.append(name)
    return out


def extract_schema_files(zip_bytes: bytes) -> Dict[str, bytes]:
    """Udpak alle skema-relaterede filer fra zip'en til {relativ_sti: indhold}.

    Bevarer den interne mappestruktur (sanitiseret), så XSD'ernes indbyrdes
    import/include via schemaLocation stadig virker. Tager XSD + ledsagende
    filer med (fx README), men springer mac-/zip-støj over.
    """
    if not zipfile.is_zipfile(io.BytesIO(zip_bytes)):
        raise SyncError(
            "Det hentede indhold er ikke en gyldig ZIP — tjek URL'en "
            "(måske en HTML-fejlside i stedet for filen)."
        )
    files: Dict[str, bytes] = {}
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        for name in _safe_members(zf):
            base = os.path.basename(name)
            if base.startswith(".") or "__MACOSX" in name:
                continue
            rel = os.path.normpath(name).replace(os.sep, "/")
            files[rel] = zf.read(name)
    if not files:
        raise SyncError("ZIP'en indeholdt ingen filer.")
    return files


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def selfcheck_xsd(files: Dict[str, bytes], expect: List[str]) -> List[str]:
    """Advarsler hvis udpakningen ikke ligner et rigtigt skema-bundle."""
    warnings: List[str] = []
    xsds = [n for n in files if n.lower().endswith(".xsd")]
    if not xsds:
        warnings.append("  ! Ingen .xsd-filer i bundlet — er URL'en korrekt?")
        return warnings
    names_low = " ".join(n.lower() for n in xsds)
    if expect and not any(tok in names_low for tok in expect):
        warnings.append(
            f"  ! Ingen XSD-navn matcher forventede nøgleord {expect} — "
            "verificér at det er det rigtige skema."
        )
    return warnings


# ---------------------------------------------------------------------------
# Provenance
# ---------------------------------------------------------------------------

def read_provenance(target: Path) -> Optional[dict]:
    p = target / PROVENANCE_NAME
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def build_provenance(source_url: str, zip_sha: str, files: Dict[str, bytes]) -> dict:
    return {
        "_comment": (
            "Provenance for OECD-skemaet. Vedligeholdes af "
            "tools/sync_oecd_schemas.py — rediger ikke i haanden."
        ),
        "source_url": source_url,
        "downloaded_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "zip_sha256": zip_sha,
        "file_count": len(files),
        "files": sorted(files.keys()),
    }


def write_bundle(target: Path, files: Dict[str, bytes], provenance: dict) -> None:
    target.mkdir(parents=True, exist_ok=True)
    for rel, content in files.items():
        dest = target / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(content)
    (target / PROVENANCE_NAME).write_text(
        json.dumps(provenance, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Delkørsel pr. bundle — returnerer (opdatering_fundet, linjer)
# ---------------------------------------------------------------------------

def process_bundle(
    bundle: dict, source_label: str, zip_bytes: bytes, apply: bool,
) -> Tuple[bool, List[str]]:
    """Udpak + sammenlign + (evt.) skriv ét bundle. Returnerer detalje-linjer
    (uden label-overskrift, som kalderen selv har sat)."""
    body: List[str] = []
    files = extract_schema_files(zip_bytes)
    zip_sha = sha256_hex(zip_bytes)

    local = read_provenance(bundle["target"])
    target_has_files = bundle["target"].exists() and any(
        p.suffix.lower() == ".xsd" for p in bundle["target"].rglob("*")
    )

    if local and local.get("zip_sha256") == zip_sha and target_has_files:
        body.append(f"  - aktuel (sha256 uændret). Kilde: {source_label}")
        body.extend(selfcheck_xsd(files, bundle["expect"]))
        return False, body

    status = "MANGLER lokalt" if not target_has_files else "AFVIGER fra forrige"
    body.append(f"  - {status}. Kilde: {source_label}")
    body.append(
        f"    {len(files)} fil(er), "
        f"{sum(1 for n in files if n.lower().endswith('.xsd'))} XSD."
    )
    body.extend(selfcheck_xsd(files, bundle["expect"]))

    if apply:
        prov = build_provenance(source_label, zip_sha, files)
        write_bundle(bundle["target"], files, prov)
        body.append(f"    -> Skrevet til {bundle['target'].relative_to(REPO_ROOT)}/")
    else:
        body.append("    (kør --apply for at skrive)")

    return True, body


def import_bundle(bundle: dict, zip_path: str, apply: bool) -> Tuple[bool, List[str]]:
    """Importér et allerede-hentet ZIP (fx fra browseren) fra en lokal sti."""
    lines: List[str] = [f"{bundle['label']}:"]
    p = Path(zip_path).expanduser()
    if not p.exists():
        raise SyncError(f"{bundle['label']}: filen findes ikke: {p}")
    zip_bytes = p.read_bytes()
    updated, body = process_bundle(bundle, f"lokal fil: {p}", zip_bytes, apply)
    return updated, lines + body


def sync_bundle(bundle: dict, apply: bool, override: Optional[str]) -> Tuple[bool, List[str]]:
    lines: List[str] = [f"{bundle['label']}:"]
    url = resolve_zip_url(bundle, override)

    try:
        zip_bytes = fetch_bytes(url)
    except SyncError as e:
        # Indbygget/angivet URL fejlede — prøv at scrape den fra OECD-siden.
        scraped = scrape_zip_url(bundle["scrape_hints"])
        if scraped and scraped != url:
            lines.append(f"  - primær URL fejlede ({e}); prøver scrapet link.")
            url = scraped
            zip_bytes = fetch_bytes(url)
        else:
            raise SyncError(
                f"{bundle['label']}: kunne ikke hentes fra {url} ({e}). "
                f"Angiv korrekt link med --{bundle['key']}-zip-url eller "
                f"miljøvariablen {bundle['env']}."
            )

    updated, body = process_bundle(bundle, url, zip_bytes, apply)
    return updated, lines + body


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Synkroniser OECD's officielle GIR-skemaer til schemas/.",
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true",
                      help="Hent + sammenlign med lokale kopier (skriver intet).")
    mode.add_argument("--apply", action="store_true",
                      help="Hent, udpak og skriv opdateringer til schemas/.")
    mode.add_argument("--import", dest="do_import", action="store_true",
                      help="Importér allerede-hentede ZIP'er (fx fra browseren) "
                           "via --gir-zip / --status-zip.")
    parser.add_argument("--gir-zip-url", help="Overstyr GIR-skemaets ZIP-URL (netværk).")
    parser.add_argument("--status-zip-url", help="Overstyr Status Message-ZIP-URL (netværk).")
    parser.add_argument("--gir-zip", help="Sti til lokal GIR-ZIP (til --import).")
    parser.add_argument("--status-zip", help="Sti til lokal Status Message-ZIP (til --import).")
    args = parser.parse_args(argv)

    print("OECD GIR-skema-synkronisering")
    print("=" * 60)

    # --- Import-tilstand: lokale ZIP'er hentet i browseren ------------------
    if args.do_import:
        paths = {"gir": args.gir_zip, "status": args.status_zip}
        if not any(paths.values()):
            print("Tilstand: --import")
            print("\nFEJL: angiv mindst én sti med --gir-zip og/eller --status-zip.")
            print("Eksempel:")
            print("  python3 tools/sync_oecd_schemas.py --import \\")
            print("    --gir-zip ~/Downloads/globe-xsd.zip \\")
            print("    --status-zip ~/Downloads/xml-schema-gir-status-message.zip")
            return EXIT_ERROR
        print("Tilstand: --import (skriver til schemas/)\n")
        had_error = False
        for bundle in SCHEMA_BUNDLES:
            path = paths.get(bundle["key"])
            if not path:
                print(f"{bundle['label']}:\n  - sprunget over (ingen sti angivet).\n")
                continue
            try:
                _, lines = import_bundle(bundle, path, apply=True)
            except SyncError as e:
                had_error = True
                lines = [f"{bundle['label']}:", f"  FEJL: {e}"]
            print("\n".join(lines))
            print()
        print("=" * 60)
        if had_error:
            print("Resultat: FEJL — mindst ét skema kunne ikke importeres.")
            return EXIT_ERROR
        print("Resultat: OK — importeret.")
        return EXIT_OK

    # --- Netværks-tilstand: --check / --apply ------------------------------
    apply = bool(args.apply)
    overrides = {"gir": args.gir_zip_url, "status": args.status_zip_url}
    print("Tilstand: --apply (skriver til schemas/)\n" if apply
          else "Tilstand: --check (skriver intet)\n")

    any_update = False
    had_error = False
    for bundle in SCHEMA_BUNDLES:
        try:
            updated, lines = sync_bundle(bundle, apply, overrides.get(bundle["key"]))
            any_update = any_update or updated
        except SyncError as e:
            had_error = True
            lines = [f"{bundle['label']}:", f"  FEJL: {e}"]
        print("\n".join(lines))
        print()

    print("=" * 60)
    if had_error:
        print("Resultat: FEJL — mindst ét skema kunne ikke hentes fra OECD's CDN "
              "(typisk HTTP 403: CDN'en blokerer automatiserede klienter).")
        print("Løsning: hent de to ZIP'er i din browser og importér dem:")
        print("  python3 tools/sync_oecd_schemas.py --import \\")
        print("    --gir-zip ~/Downloads/globe-xsd.zip \\")
        print("    --status-zip ~/Downloads/xml-schema-gir-status-message.zip")
        return EXIT_ERROR
    if apply:
        print("Resultat: OK." if any_update else "Resultat: OK — alt var allerede aktuelt.")
        return EXIT_OK
    if any_update:
        print("Resultat: Opdatering(er) findes. Kør --apply for at hente dem ind.")
        return EXIT_UPDATE_AVAILABLE
    print("Resultat: Alt er aktuelt.")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
