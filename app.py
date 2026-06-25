"""
Pillar II GIR-Validator — Flask-app (Fase 0 skelet).

Minimal indgang: forside, sundhedstjek og en /valider-rute der kører
valideringspipelinen (Fase 0: lag 1 well-formedness). UI, rapportvisning,
historik og PDF-eksport bygges i senere faser — se ARCHITECTURE.md.

Sikkerhedsheaders, SECRET_KEY og upload-grænse følger SAF-T-konventionerne.
"""

from __future__ import annotations

import logging
import os
import tempfile

from flask import Flask, jsonify, render_template, request

from validator.engine import run_pipeline
from validator.presentation import build_report_context
from validator.rules import load_catalog

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# --- SECRET_KEY: påkrævet i prod, dev-fallback med advarsel ----------------
_secret = os.environ.get("SECRET_KEY")
if not _secret:
    if os.environ.get("FLASK_ENV") == "production":
        raise RuntimeError("SECRET_KEY skal være sat i produktion.")
    _secret = "dev-only-unsafe-key"
    logger.warning("SECRET_KEY ikke sat — bruger usikker dev-nøgle.")
app.config["SECRET_KEY"] = _secret

# --- Central BALAI-brugerstyring -------------------------------------------
# Delt login på tværs af *.balai.dk via balai_auth. Ikke-loggede brugere sendes
# til auth.balai.dk; @requires_auth kræver BÅDE login OG adgang til "pillar2".
# init_app sætter selv SECRET_KEY/cookie-domæne fra miljøet (samme som SAF-T).
import auth as auth_module

auth_module.init_app(app)
requires_auth = auth_module.login_required

# --- Upload-grænse ---------------------------------------------------------
MAX_UPLOAD_MB = int(os.environ.get("MAX_UPLOAD_MB", "200"))
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024

# Katalog indlæses én gang ved opstart (fejler hurtigt hvis JSON er brudt).
CATALOG = load_catalog()


# --- Sikkerhedsheaders (mirror SAF-T) --------------------------------------
_CSP = (
    "default-src 'self'; "
    "script-src 'self' https://cdn.tailwindcss.com 'unsafe-inline'; "
    "style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com; "
    "img-src 'self' data:; font-src 'self' data:; connect-src 'self'; "
    "object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'"
)


@app.after_request
def _security_headers(resp):
    resp.headers.setdefault("Content-Security-Policy", _CSP)
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("X-Frame-Options", "DENY")
    resp.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    resp.headers.setdefault(
        "Permissions-Policy", "geolocation=(), microphone=(), camera=()")
    resp.headers.setdefault(
        "Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    return resp


# --- Ruter -----------------------------------------------------------------
@app.route("/")
@requires_auth
def index():
    return render_template(
        "index.html",
        catalog_version=CATALOG.catalog_version,
        layers=sorted(CATALOG.layers.values(), key=lambda l: l.id),
        rule_count=len(CATALOG.rules),
    )


@app.route("/sundhed")
def sundhed():
    """Health-/parathedstjek: katalog indlæst + officielle skemaer til stede."""
    root = os.path.dirname(os.path.abspath(__file__))
    gir_xsd = os.path.join(root, "schemas", "gir", "GLOBEXML_v1.0.xsd")
    status_xsd = os.path.join(root, "schemas", "status", "GIRStatusMessageXML_v1.0.xsd")
    return jsonify({
        "status": "ok",
        "catalog_version": CATALOG.catalog_version,
        "antal_regler": len(CATALOG.rules),
        "antal_lag": len(CATALOG.layers),
        "gir_skema_til_stede": os.path.exists(gir_xsd),
        "status_skema_til_stede": os.path.exists(status_xsd),
        "fase": "1 — lag 1 (well-formed + XSD) og lag 2 (struktur) aktive; lag 3-8 følger",
    })


@app.route("/valider", methods=["POST"])
@requires_auth
def valider():
    """Modtag en GIR-fil, kør pipelinen, returnér outcome som JSON.

    Fase 0: kun lag 1 (well-formedness). Kildefilen slettes straks efter kørsel
    (samme databehandlingsprincip som SAF-T)."""
    if "file" not in request.files or not request.files["file"].filename:
        return jsonify({"error": "Ingen fil uploadet (forventet felt: 'file')."}), 400

    profile_key = request.form.get("profil", "standard")
    if profile_key not in CATALOG.profiles:
        return jsonify({"error": f"Ukendt profil: {profile_key!r}."}), 400

    upload = request.files["file"]
    tmp = tempfile.NamedTemporaryFile(suffix=".xml", delete=False)
    try:
        upload.save(tmp.name)
        tmp.close()
        outcome = run_pipeline(tmp.name, profile_key=profile_key, catalog=CATALOG)
        if request.args.get("format") == "json" or \
                request.accept_mimetypes.best == "application/json":
            return jsonify(outcome.to_dict())
        return render_template(
            "rapport.html", r=build_report_context(outcome, CATALOG))
    finally:
        try:
            os.unlink(tmp.name)   # kildefil slettes straks efter kørsel
        except OSError:
            pass


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=True)
