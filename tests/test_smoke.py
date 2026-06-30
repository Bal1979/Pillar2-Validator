"""Fase 0 smoke-tests: kataloget indlæses, kernen virker, skemaerne ligger,
appen booter, og lag 1 fanger ugyldig XML."""

import os

import pytest

from validator.engine import run_pipeline
from validator.rules import BalSeverity, load_catalog, verdict_from_counts


# --- Katalog ---------------------------------------------------------------
def test_catalog_loads_with_eight_layers():
    cat = load_catalog()
    assert cat.catalog_version
    assert len(cat.layers) == 8
    assert {l.id for l in cat.layers.values()} == set(range(1, 9))
    assert "P2-001" in cat.rules and "P2-002" in cat.rules


def test_default_profile_is_standard():
    cat = load_catalog()
    assert cat.default_profile().key == "standard"


def test_severity_levels_and_verdict():
    assert [s.label_da for s in BalSeverity] == \
        ["Kritisk", "Væsentlig", "Medium", "Lav", "Info"]
    assert verdict_from_counts({BalSeverity.CRITICAL: 1}) == "afvist"
    assert verdict_from_counts({BalSeverity.MEDIUM: 1}) == "betinget_godkendt"
    assert verdict_from_counts({}) == "godkendt"


def test_build_finding_renders_danish_message():
    cat = load_catalog()
    f = cat.build_finding(
        "P2-002", BalSeverity.CRITICAL,
        params={"line": 12, "detail": "uventet tegn"},
    )
    assert "linje 12" in f.message_da
    assert f.layer == 1


# --- Officielle skemaer ----------------------------------------------------
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_official_schemas_present():
    assert os.path.exists(os.path.join(ROOT, "schemas/gir/GLOBEXML_v1.0.xsd"))
    assert os.path.exists(os.path.join(ROOT, "schemas/status/GIRStatusMessageXML_v1.0.xsd"))


VALID_GIR = os.path.join(ROOT, "tests", "fixtures", "gir_valid.xml")
RICH_GIR = os.path.join(ROOT, "tests", "fixtures", "gir_valid_rich.xml")


def test_rich_fixture_actually_rich():
    """Værn mod at fixturen i det stille bliver tom: strukturen SKAL være der."""
    from lxml import etree
    ns = "{urn:oecd:ties:globe:v2}"
    root = etree.parse(RICH_GIR).getroot()
    have = {n: len(list(root.iter(ns + n))) for n in
            ("GeneralSection", "CE", "OtherUPE", "Ownership", "GlobeStatus")}
    assert have["CE"] >= 1 and have["Ownership"] >= 1 and have["GeneralSection"] == 1, have


def test_rich_fixture_is_clean():
    """Komplet, skemagyldig GIR (alle tre sektioner + CorporateStructure +
    JurisdictionSection/GLoBETax) → fuldt godkendt, ingen fund overhovedet.
    Golden-fixtur og regressionsfacit for alle aktive regler."""
    outcome = run_pipeline(RICH_GIR)
    assert outcome.verdict == "godkendt", [f.rule_id for f in outcome.findings]
    assert outcome.findings == []


# --- Lag 1: well-formedness + XSD ------------------------------------------
def test_pipeline_flags_malformed_xml(tmp_path):
    p = tmp_path / "broken.xml"
    p.write_text("<root><a>1</root>", encoding="utf-8")
    outcome = run_pipeline(str(p))
    assert outcome.blocked_at_layer == 1
    assert outcome.verdict == "afvist"
    assert outcome.findings[0].rule_id == "P2-002"


def test_valid_gir_passes_xsd():
    outcome = run_pipeline(VALID_GIR)
    assert outcome.layers_run == [1, 2, 3, 4]
    # XSD-gyldig → ingen P2-001.
    assert all(f.rule_id != "P2-001" for f in outcome.findings)
    assert outcome.namespace == "urn:oecd:ties:globe:v2"
    assert outcome.gir_version == "1.0"


def test_schema_invalid_gir_emits_p2_001(tmp_path):
    bad = open(VALID_GIR).read().replace(
        "<globe:MessageRefId>DK2026-0001</globe:MessageRefId>", "")
    p = tmp_path / "invalid.xml"
    p.write_text(bad, encoding="utf-8")
    outcome = run_pipeline(str(p))
    assert any(f.rule_id == "P2-001" for f in outcome.findings)
    assert outcome.verdict == "afvist"


# --- Lag 2: struktur + CompanyContext --------------------------------------
def test_company_context_extracted():
    outcome = run_pipeline(VALID_GIR)
    c = outcome.company
    assert c.message_ref_id == "DK2026-0001"
    assert c.message_type == "GIR101"
    assert c.reporting_period == "2025-12-31"
    assert c.name == "Example Group"


def test_wrong_root_emits_p2_010(tmp_path):
    p = tmp_path / "foo.xml"
    p.write_text("<Foo/>", encoding="utf-8")
    outcome = run_pipeline(str(p))
    assert any(f.rule_id == "P2-010" for f in outcome.findings)


def test_no_jurisdiction_section_emits_p2_013():
    outcome = run_pipeline(VALID_GIR)
    assert any(f.rule_id == "P2-013" for f in outcome.findings)


def test_outcome_serializes_to_dict():
    d = run_pipeline(VALID_GIR).to_dict()
    assert d["layers_run"] == [1, 2, 3, 4]
    assert "findings" in d and "verdict" in d


# --- Rapport-kontekst ------------------------------------------------------
def test_report_context_builds():
    from validator.presentation import build_report_context
    cat = load_catalog()
    r = build_report_context(run_pipeline(VALID_GIR), cat)
    assert r["verdict_label"] in ("Afvist", "Betinget godkendt", "Godkendt")
    assert isinstance(r["groups"], list)
    assert r["company"]["message_ref_id"] == "DK2026-0001"


# --- App booter ------------------------------------------------------------
def _login_pillar2(app_module):
    """Returnér en test-client logget ind som all_access-bruger (har dermed
    adgang til 'pillar2'). Bruger den isolerede test-auth-DB fra conftest."""
    from balai_auth import repo, core
    app = app_module.app
    app.config["TESTING"] = True
    with app.app_context():
        email = "test@balai.dk"
        u = repo.get_user_by_email(email)
        if u is None:
            repo.create_user(email, core.hash_password("test-password-12"),
                             all_access=True)
            u = repo.get_user_by_email(email)
        uid, tv = u["id"], u["token_version"]
    client = app.test_client()
    with client.session_transaction() as sess:
        sess["uid"] = uid
        sess["tv"] = tv
        sess["iat"] = repo.now().isoformat()
    return client


def test_app_health_endpoint():
    import app as app_module
    client = app_module.app.test_client()
    r = client.get("/sundhed")              # offentlig (health check)
    assert r.status_code == 200
    body = r.get_json()
    assert body["status"] == "ok"
    assert body["gir_skema_til_stede"] is True


def test_app_requires_login():
    """Sikkerhed: forsiden og /valider er bag central login."""
    import app as app_module
    client = app_module.app.test_client()
    r = client.get("/")
    assert r.status_code == 302
    assert "/login" in r.headers.get("Location", "")
    rj = client.post("/valider", headers={"Accept": "application/json"})
    assert rj.status_code == 401


def test_app_valider_renders_report():
    import app as app_module
    client = _login_pillar2(app_module)
    with open(VALID_GIR, "rb") as fh:
        r = client.post("/valider", data={"file": (fh, "gir.xml")},
                        content_type="multipart/form-data")
    assert r.status_code == 200
    assert "Betinget godkendt" in r.get_data(as_text=True) or \
           "Godkendt" in r.get_data(as_text=True)


def test_app_valider_json_format():
    import app as app_module
    client = _login_pillar2(app_module)
    with open(VALID_GIR, "rb") as fh:
        r = client.post("/valider?format=json",
                        data={"file": (fh, "gir.xml")},
                        content_type="multipart/form-data")
    assert r.status_code == 200
    assert r.get_json()["layers_run"] == [1, 2, 3, 4]


# --- Lag 3-4: OECD-regelmotor ----------------------------------------------
def test_oecd_ruleset_lints():
    from validator.rules.oecd_rules import load_oecd_rules, validate_ruleset
    data = load_oecd_rules()
    validate_ruleset(data)            # rejser ved fejl
    assert len(data["rules"]) >= 3


def test_valid_gir_has_no_oecd_violations():
    outcome = run_pipeline(VALID_GIR)
    assert outcome.layers_run == [1, 2, 3, 4]
    assert all(f.rule_id not in ("P2-030", "P2-040") for f in outcome.findings)


def test_corrdocrefid_forbidden_on_new_data(tmp_path):
    # DocTypeIndic=OECD1 (ny data) + CorrDocRefId → record-level overtrædelse.
    xml = open(VALID_GIR).read().replace(
        "<stf:DocRefId>DK2026-0001-1</stf:DocRefId>",
        "<stf:DocRefId>DK2026-0001-1</stf:DocRefId>\n"
        "        <stf:CorrDocRefId>DK2026-0001-0</stf:CorrDocRefId>")
    p = tmp_path / "corr.xml"; p.write_text(xml, encoding="utf-8")
    outcome = run_pipeline(str(p))
    assert any(f.rule_id == "P2-030" for f in outcome.findings)
    assert outcome.verdict == "afvist"


def test_corrdocrefid_required_on_correction(tmp_path):
    # DocTypeIndic=OECD2 (rettelse) uden CorrDocRefId → record-level overtrædelse.
    xml = open(VALID_GIR).read().replace(
        "<stf:DocTypeIndic>OECD1</stf:DocTypeIndic>",
        "<stf:DocTypeIndic>OECD2</stf:DocTypeIndic>")
    p = tmp_path / "req.xml"; p.write_text(xml, encoding="utf-8")
    outcome = run_pipeline(str(p))
    assert any(f.rule_id == "P2-030" for f in outcome.findings)


def test_evaluator_unique_and_not_equal():
    from lxml import etree
    from validator.rules.oecd_rules import evaluate
    ns = {"globe": "urn:oecd:ties:globe:v2", "stf": "urn:oecd:ties:globestf:v5"}
    xml = (b'<g:Root xmlns:g="urn:oecd:ties:globe:v2" xmlns:s="urn:oecd:ties:globestf:v5">'
           b'<g:DocSpec><s:DocRefId>A</s:DocRefId></g:DocSpec>'
           b'<g:DocSpec><s:DocRefId>A</s:DocRefId></g:DocSpec>'
           b'<g:Pair><g:Left>x</g:Left><g:Right>x</g:Right></g:Pair></g:Root>')
    root = etree.fromstring(xml)
    rs = {"namespaces": ns, "rules": [
        {"id": "U", "level": "file", "name_da": "unik", "message_da": "dublet {value}",
         "check": {"type": "unique", "xpath": "//stf:DocRefId"}},
        {"id": "NE", "level": "record", "name_da": "ulig", "message_da": "ens {value}",
         "check": {"type": "not_equal", "container": "//globe:Pair",
                   "left": "globe:Left", "right": "globe:Right"}},
    ]}
    v = evaluate(root, rs)
    ids = {x["rule"]["id"] for x in v}
    assert ids == {"U", "NE"}


def test_sync_oecd_rules_check_runs():
    import importlib
    sync = importlib.import_module("tools.sync_oecd_rules")
    assert sync.cmd_check() == 0


# --- Fuldt regelgrundlag (katalog + guidance) ------------------------------
def test_full_catalogue_loads():
    from validator.rules.oecd_rules import load_catalogue
    cat = load_catalogue()
    assert cat["counts"]["total"] == 163
    assert len(cat["rules"]) == 163


def test_guidance_deviations_loads():
    import json
    from validator.rules.oecd_rules import _REFERENCE_DIR
    g = json.load(open(os.path.join(_REFERENCE_DIR, "guidance_deviations_2026-06.json")))
    assert g["count"] == 14
    affected = {i["affected_rule"] for i in g["issues"] if i["affected_rule"]}
    assert {"60025", "60026", "70092", "70028"} <= affected


def test_switched_off_codes():
    from validator.rules.oecd_rules import switched_off_codes
    assert switched_off_codes() == frozenset({"60025", "60026", "70092", "70028"})


def test_switched_off_rule_never_fires():
    from lxml import etree
    from validator.rules.oecd_rules import evaluate
    ns = {"globe": "urn:oecd:ties:globe:v2", "stf": "urn:oecd:ties:globestf:v5"}
    xml = (b'<g:Root xmlns:g="urn:oecd:ties:globe:v2" xmlns:s="urn:oecd:ties:globestf:v5">'
           b'<s:X>A</s:X><s:X>A</s:X></g:Root>')
    root = etree.fromstring(xml)
    # En 'unique'-regel der VILLE fyre — men er markeret som slået fra (70028).
    rs = {"namespaces": ns, "rules": [
        {"id": "OFF", "oecd_rule": "70028", "level": "record", "name_da": "x",
         "message_da": "dub {value}", "check": {"type": "unique", "xpath": "//stf:X"}},
    ]}
    assert evaluate(root, rs) == []


def test_coverage_reports():
    from validator.rules.oecd_rules import coverage
    c = coverage()
    assert c["total_catalogue"] == 163
    assert c["switched_off"] == 4
    assert c["executable"] >= 3


def test_docrefid_rule_has_real_oecd_number():
    from validator.rules.oecd_rules import load_oecd_rules
    rules = {r["id"]: r for r in load_oecd_rules()["rules"]}
    assert rules["OECD-DOCREFID-UNIQUE"]["oecd_rule"] == "60007"
    assert rules["OECD-CORR-FORBIDDEN"]["oecd_rule"] == "60012"


# --- Nye eksekverbare regler (batch 1): 60004, 60006 -----------------------
def test_no_mix_new_and_correction(tmp_path):
    # To GLOBEBody: én med OECD1, én med OECD2 → 60004 (mutually_exclusive).
    base = open(VALID_GIR).read()
    second_body = base[base.index("<globe:GLOBEBody>"):base.index("</globe:GLOBEBody>")+len("</globe:GLOBEBody>")]
    second_body = second_body.replace("OECD1", "OECD2").replace(
        "DK2026-0001-1", "DK2026-0002-1")
    xml = base.replace("</globe:GLOBE_OECD>", second_body + "\n</globe:GLOBE_OECD>")
    p = tmp_path / "mix.xml"; p.write_text(xml, encoding="utf-8")
    outcome = run_pipeline(str(p))
    assert any(f.rule_id == "P2-030" and "60004" in f.message_da
               for f in outcome.findings)


def test_corrdocrefid_unique(tmp_path):
    from lxml import etree
    from validator.rules.oecd_rules import evaluate, load_oecd_rules
    ns = {"globe": "urn:oecd:ties:globe:v2", "stf": "urn:oecd:ties:globestf:v5"}
    xml = (b'<g:Root xmlns:g="urn:oecd:ties:globe:v2" xmlns:s="urn:oecd:ties:globestf:v5">'
           b'<s:CorrDocRefId>X1</s:CorrDocRefId>'
           b'<s:CorrDocRefId>X1</s:CorrDocRefId></g:Root>')
    root = etree.fromstring(xml)
    v = evaluate(root, load_oecd_rules())
    assert any(x["rule"]["oecd_rule"] == "60006" for x in v)


def test_executable_coverage_grew():
    from validator.rules.oecd_rules import coverage
    assert coverage()["executable"] == 92


# --- Batch 18: CEComputation-conditionals + TIN-ulighed --------------------
def test_investmententitytin_neq_ce_tin_70058():
    g = (b'<g:GLOBE_OECD xmlns:g="urn:oecd:ties:globe:v2"><g:CEComputation>'
         b'<g:TIN>DK111</g:TIN><g:Elections><g:Art7.6>'
         b'<g:InvestmentEntityTIN>DK222</g:InvestmentEntityTIN>'
         b'</g:Art7.6></g:Elections></g:CEComputation></g:GLOBE_OECD>')
    bad = g.replace(b"<g:InvestmentEntityTIN>DK222<", b"<g:InvestmentEntityTIN>DK111<")
    assert "70058" not in _eval_real(g)
    assert "70058" in _eval_real(bad)


def test_adjustmentitem_gir2024_requires_art76_70117():
    bad = (b'<g:GLOBE_OECD xmlns:g="urn:oecd:ties:globe:v2"><g:CEComputation>'
           b'<g:AdjustmentItem>GIR2024</g:AdjustmentItem></g:CEComputation></g:GLOBE_OECD>')
    good = bad.replace(b"</g:AdjustmentItem>",
                       b"</g:AdjustmentItem><g:Art7.6>X</g:Art7.6>")
    assert "70117" in _eval_real(bad)
    assert "70117" not in _eval_real(good)


# --- Batch 17: dato-aware conditional + relativ år-grænse (motor-udvidelse) -
def test_safeharbour_sunset_date_70039():
    base = (b'<g:GLOBE_OECD xmlns:g="urn:oecd:ties:globe:v2">'
            b'<g:Period><g:Start>2027-01-01</g:Start><g:End>2027-12-31</g:End></g:Period>'
            b'<g:Summary><g:SafeHarbour>GIR1206</g:SafeHarbour></g:Summary></g:GLOBE_OECD>')
    # Periode efter 31/12/2026 + GIR1206 → fyrer.
    assert "70039" in _eval_real(base)
    # Periode FØR cutoff → fyrer ikke.
    ok = base.replace(b"<g:End>2027-12-31</g:End>", b"<g:End>2026-06-30</g:End>")
    assert "70039" not in _eval_real(ok)


def test_recapture_year_window_70071():
    # End=2024 → tilladte år 2021-2024. Year=2020 ligger 4 år før → fyrer.
    bad = (b'<g:GLOBE_OECD xmlns:g="urn:oecd:ties:globe:v2">'
           b'<g:Period><g:Start>2024-01-01</g:Start><g:End>2024-12-31</g:End></g:Period>'
           b'<g:Recapture><g:Year>2020</g:Year></g:Recapture></g:GLOBE_OECD>')
    good = bad.replace(b"<g:Year>2020</g:Year>", b"<g:Year>2022</g:Year>")
    assert "70071" in _eval_real(bad)
    assert "70071" not in _eval_real(good)


# --- Batch 16: flere beregningsregler --------------------------------------
def test_expected_adjusted_covered_tax_70091():
    g = (b'<g:GLOBE_OECD xmlns:g="urn:oecd:ties:globe:v2"><g:OverallComputation>'
         b'<g:GlobeLoss>1000</g:GlobeLoss>'
         b'<g:AdditionalTopUpTax><g:Art4.1.5>'
         b'<g:ExpectedAdjustedCoveredTax>150</g:ExpectedAdjustedCoveredTax>'
         b'</g:Art4.1.5></g:AdditionalTopUpTax></g:OverallComputation></g:GLOBE_OECD>')
    bad = g.replace(b"<g:ExpectedAdjustedCoveredTax>150<",
                    b"<g:ExpectedAdjustedCoveredTax>999<")
    assert "70091" not in _eval_real(g)
    assert "70091" in _eval_real(bad)


# --- Batch 15: år-mod-periode-compares + kryds-CE-eksistens ----------------
def _wrap_period(inner):
    return (b'<g:GLOBE_OECD xmlns:g="urn:oecd:ties:globe:v2">'
            b'<g:Period><g:Start>2024-01-01</g:Start><g:End>2024-12-31</g:End></g:Period>'
            + inner + b'</g:GLOBE_OECD>')


def test_recapture_year_after_period_end_70070():
    bad = _wrap_period(b'<g:Recapture><g:Year>2025</g:Year></g:Recapture>')
    good = _wrap_period(b'<g:Recapture><g:Year>2024</g:Year></g:Recapture>')
    assert "70070" in _eval_real(bad)
    assert "70070" not in _eval_real(good)


def test_gir308_requires_gir307_70015():
    bad = _wrap_period(b'<g:CE><g:ID><g:GlobeStatus>GIR308</g:GlobeStatus></g:ID></g:CE>')
    good = _wrap_period(b'<g:CE><g:ID><g:GlobeStatus>GIR308</g:GlobeStatus></g:ID></g:CE>'
                        b'<g:CE><g:ID><g:GlobeStatus>GIR307</g:GlobeStatus></g:ID></g:CE>')
    assert "70015" in _eval_real(bad)
    assert "70015" not in _eval_real(good)


# --- Batch 14: unique_in + flere conditional/calc/value_range-regler --------
def test_adjustmentitem_unique_per_etr_70059():
    g = (b'<g:GLOBE_OECD xmlns:g="urn:oecd:ties:globe:v2"><g:ETR>'
         b'<g:AdjustmentItem>GIR4001</g:AdjustmentItem>'
         b'<g:AdjustmentItem>GIR4002</g:AdjustmentItem></g:ETR></g:GLOBE_OECD>')
    bad = g.replace(b"<g:AdjustmentItem>GIR4002</g:AdjustmentItem>",
                    b"<g:AdjustmentItem>GIR4001</g:AdjustmentItem>")
    assert "70059" not in _eval_real(g)
    assert "70059" in _eval_real(bad)


def test_globestatus_316_requires_ownershipchange_70021():
    bad = (b'<g:GLOBE_OECD xmlns:g="urn:oecd:ties:globe:v2"><g:CE><g:ID>'
           b'<g:GlobeStatus>GIR316</g:GlobeStatus></g:ID></g:CE></g:GLOBE_OECD>')
    good = bad.replace(b"</g:ID>", b"</g:ID><g:OwnershipChange>GIR320</g:OwnershipChange>")
    assert "70021" in _eval_real(bad)
    assert "70021" not in _eval_real(good)


# --- Batch 13: flere beregningsregler (nested sum_all, dotted/hyphen navne) -
def test_calc_adjustedfanil_total_60028():
    g = (b'<g:GLOBE_OECD xmlns:g="urn:oecd:ties:globe:v2"><g:AdjustedFANIL>'
         b'<g:FANIL>100</g:FANIL>'
         b'<g:MainEntityPEandFTE><g:Additions>20</g:Additions></g:MainEntityPEandFTE>'
         b'<g:MainEntityPEandFTE><g:Reductions>5</g:Reductions></g:MainEntityPEandFTE>'
         b'<g:Total>115</g:Total></g:AdjustedFANIL></g:GLOBE_OECD>')
    bad = g.replace(b"<g:Total>115</g:Total>", b"<g:Total>120</g:Total>")
    assert "60028" not in _eval_real(g)
    assert "60028" in _eval_real(bad)


def test_formula_literal_constant():
    from validator.rules.oecd_rules import _eval_formula
    from lxml import etree
    node = etree.fromstring(b'<g:X xmlns:g="urn:oecd:ties:globe:v2"><g:a>100</g:a></g:X>')
    ns = {"globe": "urn:oecd:ties:globe:v2"}
    assert _eval_formula(node, {"op": "multiply", "operands": ["globe:a", 0.15]}, ns) == 15.0


# --- Batch 12: numeriske operatorer (lt/gt/le/ge) + local-name() -----------
def test_numeric_ownership_pct_70026():
    g = (b'<g:GLOBE_OECD xmlns:g="urn:oecd:ties:globe:v2"><g:CE><g:ID>'
         b'<g:GlobeStatus>GIR305</g:GlobeStatus></g:ID><g:Ownership>'
         b'<g:OwnershipPercentage>1</g:OwnershipPercentage></g:Ownership></g:CE></g:GLOBE_OECD>')
    bad = g.replace(b"<g:OwnershipPercentage>1<", b"<g:OwnershipPercentage>0.5<")
    assert "70026" not in _eval_real(g)
    assert "70026" in _eval_real(bad)


def test_numeric_when_neg_income_70088():
    bad = (b'<g:GLOBE_OECD xmlns:g="urn:oecd:ties:globe:v2"><g:OverallComputation>'
           b'<g:NetGlobeIncome><g:Total>-5</g:Total></g:NetGlobeIncome>'
           b'</g:OverallComputation></g:GLOBE_OECD>')
    assert "70088" in _eval_real(bad)
    good = bad.replace(b"<g:Total>-5</g:Total>", b"<g:Total>5</g:Total>")
    assert "70088" not in _eval_real(good)


# --- Batch 11: SafeHarbour-regler ------------------------------------------
def test_safeharbour_requires_revenue_70047():
    g = (b'<g:GLOBE_OECD xmlns:g="urn:oecd:ties:globe:v2"><g:Summary>'
         b'<g:SafeHarbour>GIR1203</g:SafeHarbour><g:Revenue>1</g:Revenue>'
         b'</g:Summary></g:GLOBE_OECD>')
    bad = g.replace(b"<g:Revenue>1</g:Revenue>", b"")
    assert "70047" not in _eval_real(g)
    assert "70047" in _eval_real(bad)


def test_cfsofupe_forbids_safeharbour_70041():
    bad = (b'<g:GLOBE_OECD xmlns:g="urn:oecd:ties:globe:v2">'
           b'<g:CFSofUPE>GIR502</g:CFSofUPE>'
           b'<g:Summary><g:SafeHarbour>GIR1208</g:SafeHarbour></g:Summary></g:GLOBE_OECD>')
    assert "70041" in _eval_real(bad)


def test_docs_stats_in_sync():
    """Selvhåndhævende: STATS-blokken i CLAUDE.md skal matche den faktiske
    regeldækning. Fejler den, så kør `python3 tools/update_docs.py`."""
    import re
    from validator.rules.oecd_rules import coverage
    txt = open(os.path.join(ROOT, "CLAUDE.md"), encoding="utf-8").read()
    m = re.search(r"Nøgletal.*?(\d+)/163", txt)
    assert m, "ingen STATS-nøgletalsblok i CLAUDE.md"
    assert int(m.group(1)) == coverage()["executable"], \
        "STATS-blok er forældet — kør: python3 tools/update_docs.py"


# --- Batch 10: Basis/AdjustmentItem/Exception conditional-regler -----------
def test_basis_requires_taxrate_70108():
    g = (b'<g:GLOBE_OECD xmlns:g="urn:oecd:ties:globe:v2"><g:Owner>'
         b'<g:Basis>GIR1901</g:Basis><g:EntityOwner><g:TaxRate>0.1</g:TaxRate>'
         b'</g:EntityOwner></g:Owner></g:GLOBE_OECD>')
    bad = g.replace(b"<g:TaxRate>0.1</g:TaxRate>", b"")
    assert "70108" not in _eval_real(g)
    assert "70108" in _eval_real(bad)


def test_exception_forbids_crossborder_70107():
    bad = (b'<g:GLOBE_OECD xmlns:g="urn:oecd:ties:globe:v2"><g:CEComputation>'
           b'<g:Exception>true</g:Exception><g:CrossBorderAdjustments/>'
           b'</g:CEComputation></g:GLOBE_OECD>')
    assert "70107" in _eval_real(bad)


# --- Batch 9: flere beregningsregler (Recast + PostFilingAdjust) -----------
def test_calc_befrecast_70078():
    G = b'<g:GLOBE_OECD xmlns:g="urn:oecd:ties:globe:v2">'
    good = G + (b'<g:DeferTaxAdjustAmt><g:DefTaxAmt>100</g:DefTaxAmt>'
                b'<g:DiffCarryValue>30</g:DiffCarryValue><g:GLoBEValue>10</g:GLoBEValue>'
                b'<g:BefRecastAdjust>80</g:BefRecastAdjust></g:DeferTaxAdjustAmt></g:GLOBE_OECD>')
    bad = good.replace(b"<g:BefRecastAdjust>80", b"<g:BefRecastAdjust>70")
    assert "70078" not in _eval_real(good)
    assert "70078" in _eval_real(bad)


# --- Batch 8: beregningsmotor (calculation) --------------------------------
def _oc(ngi, se, ep):
    return (f'<g:GLOBE_OECD xmlns:g="urn:oecd:ties:globe:v2"><g:OverallComputation>'
            f'<g:NetGlobeIncome><g:Total>{ngi}</g:Total></g:NetGlobeIncome>'
            f'<g:SubstanceExclusion><g:Total>{se}</g:Total></g:SubstanceExclusion>'
            f'<g:ExcessProfits>{ep}</g:ExcessProfits>'
            f'</g:OverallComputation></g:GLOBE_OECD>').encode()


def test_calculation_excessprofits_70086():
    # 1000 - 300 = 700: korrekt → ingen fund; 650 → fyrer.
    assert "70086" not in _eval_real(_oc(1000, 300, 700))
    assert "70086" in _eval_real(_oc(1000, 300, 650))


def test_calculation_skips_when_fields_missing():
    # Mangler operander → kan ikke beregnes → ingen falsk positiv.
    xml = (b'<g:GLOBE_OECD xmlns:g="urn:oecd:ties:globe:v2"><g:OverallComputation>'
           b'<g:ExcessProfits>700</g:ExcessProfits></g:OverallComputation></g:GLOBE_OECD>')
    assert "70086" not in _eval_real(xml)


def test_calc_fires_end_to_end_on_planted_error(tmp_path):
    # Plant én forkert Remaining i den ellers fuldt gyldige golden-fil →
    # beregningsregel 70083 fyrer gennem HELE pipelinen (XSD ok, men calc afviger).
    xml = open(RICH_GIR).read().replace(
        "<globe:Remaining>0</globe:Remaining>",
        "<globe:Remaining>5</globe:Remaining>")
    p = tmp_path / "planted.xml"
    p.write_text(xml, encoding="utf-8")
    outcome = run_pipeline(str(p))
    assert not any(f.rule_id == "P2-001" for f in outcome.findings)  # stadig XSD-gyldig
    assert any(f.rule_id == "P2-040" and "70083" in f.message_da
               for f in outcome.findings)
    assert outcome.verdict == "afvist"


def test_calculation_formula_evaluator():
    from validator.rules.oecd_rules import _eval_formula
    from lxml import etree
    ns = {"globe": "urn:oecd:ties:globe:v2"}
    node = etree.fromstring(
        b'<g:X xmlns:g="urn:oecd:ties:globe:v2"><g:a>10</g:a><g:b>3</g:b>'
        b'<g:c>2</g:c></g:X>')
    assert _eval_formula(node, {"op": "subtract", "operands": ["globe:a", "globe:b"]}, ns) == 7
    assert _eval_formula(node, {"op": "sum", "operands": ["globe:a", "globe:b", "globe:c"]}, ns) == 15
    assert _eval_formula(node, {"op": "multiply", "operands": ["globe:b", "globe:c"]}, ns) == 6
    assert _eval_formula(node, {"op": "sum_all", "path": ".//globe:a"}, ns) == 10


# --- Batch 7: Ownership-regler (conditional_ref) ---------------------------
def test_ownership_tin_must_match_reported_70029():
    bad = _eval_real(b'<g:GLOBE_OECD xmlns:g="urn:oecd:ties:globe:v2">'
                     b'<g:ID><g:TIN TypeOfTIN="GIR3001">DKAAA</g:TIN></g:ID>'
                     b'<g:Ownership><g:OwnershipType>GIR801</g:OwnershipType>'
                     b'<g:TIN TypeOfTIN="GIR3001">DKZZZ</g:TIN></g:Ownership></g:GLOBE_OECD>')
    good = _eval_real(b'<g:GLOBE_OECD xmlns:g="urn:oecd:ties:globe:v2">'
                      b'<g:ID><g:TIN TypeOfTIN="GIR3001">DKAAA</g:TIN></g:ID>'
                      b'<g:Ownership><g:OwnershipType>GIR801</g:OwnershipType>'
                      b'<g:TIN TypeOfTIN="GIR3001">DKAAA</g:TIN></g:Ownership></g:GLOBE_OECD>')
    assert "70029" in bad and "70029" not in good


def test_preownership_nominee_70025():
    bad = _eval_real(b'<g:GLOBE_OECD xmlns:g="urn:oecd:ties:globe:v2">'
                     b'<g:PreOwnership><g:OwnershipType>GIR805</g:OwnershipType>'
                     b'<g:TIN TypeOfTIN="GIR3001">DK1</g:TIN></g:PreOwnership></g:GLOBE_OECD>')
    assert "70025" in bad


# --- Batch 6: CorporateStructure (verificeret mod righoldig fixture) -------
def test_rich_fixture_clean_for_corpstructure_rules():
    # Den righoldige fixture må ikke udløse nogen af de nye CE-/UPE-regler.
    out = run_pipeline(RICH_GIR)
    fired = {f.params.get("oecd") for f in out.findings if f.rule_id in ("P2-030", "P2-040")}
    assert fired == set()


def test_cardinality_ce_rescountry_70011():
    bad = _eval_real(b'<g:GLOBE_OECD xmlns:g="urn:oecd:ties:globe:v2"><g:CE><g:ID>'
                     b'<g:ResCountryCode>DK</g:ResCountryCode>'
                     b'<g:ResCountryCode>SE</g:ResCountryCode></g:ID></g:CE></g:GLOBE_OECD>')
    assert "70011" in bad


def test_qiir_requires_rules_70032():
    bad = _eval_real(b'<g:GLOBE_OECD xmlns:g="urn:oecd:ties:globe:v2"><g:CE>'
                     b'<g:ID><g:Rules>GIR203</g:Rules></g:ID><g:QIIR/></g:CE></g:GLOBE_OECD>')
    assert "70032" in bad


def test_upe_invalid_globestatus_70009():
    bad = _eval_real(b'<g:GLOBE_OECD xmlns:g="urn:oecd:ties:globe:v2"><g:OtherUPE><g:ID>'
                     b'<g:GlobeStatus>GIR305</g:GlobeStatus></g:ID></g:OtherUPE></g:GLOBE_OECD>')
    assert "70009" in bad


# --- Batch 5: union-present + value_range-regler ---------------------------
def test_etrstatus_must_have_content_70044():
    bad = _eval_real(b'<g:GLOBE_OECD xmlns:g="urn:oecd:ties:globe:v2">'
                     b'<g:ETRStatus><g:Foo/></g:ETRStatus></g:GLOBE_OECD>')
    good = _eval_real(b'<g:GLOBE_OECD xmlns:g="urn:oecd:ties:globe:v2">'
                      b'<g:ETRStatus><g:ETRComputation/></g:ETRStatus></g:GLOBE_OECD>')
    assert "70044" in bad and "70044" not in good


def test_value_range_endamount_70073():
    bad = _eval_real(b'<g:GLOBE_OECD xmlns:g="urn:oecd:ties:globe:v2">'
                     b'<g:EndAmount>-5</g:EndAmount></g:GLOBE_OECD>')
    good = _eval_real(b'<g:GLOBE_OECD xmlns:g="urn:oecd:ties:globe:v2">'
                      b'<g:EndAmount>0</g:EndAmount></g:GLOBE_OECD>')
    assert "70073" in bad and "70073" not in good


def test_present_op_counts_empty_elements():
    # Regression: et tomt element skal tælle som 'present'.
    from validator.rules.oecd_rules import _cond_holds
    root = _root(b'<g:R xmlns:g="urn:oecd:ties:globe:v2"><g:X/></g:R>')
    ns = {"globe": "urn:oecd:ties:globe:v2"}
    assert _cond_holds(root, {"path": "globe:X", "op": "present"}, ns) is True
    assert _cond_holds(root, {"path": "globe:Y", "op": "absent"}, ns) is True


# --- Batch 4: stikprøver af de nye regler ----------------------------------
def _eval_real(xml: bytes):
    from validator.rules.oecd_rules import evaluate, load_oecd_rules
    return {x["rule"]["oecd_rule"] for x in evaluate(_root(xml), load_oecd_rules())}


def test_globestatus_mutual_exclusion_70013():
    ids = _eval_real(b'<g:GLOBE_OECD xmlns:g="urn:oecd:ties:globe:v2">'
                     b'<g:CE><g:ID><g:GlobeStatus>GIR313</g:GlobeStatus>'
                     b'<g:GlobeStatus>GIR314</g:GlobeStatus></g:ID></g:CE></g:GLOBE_OECD>')
    assert "70013" in ids


def test_changedate_before_period_start_70022():
    ids = _eval_real(b'<g:GLOBE_OECD xmlns:g="urn:oecd:ties:globe:v2">'
                     b'<g:Period><g:Start>2025-01-01</g:Start></g:Period>'
                     b'<g:OwnershipChange><g:ChangeDate>2024-06-01</g:ChangeDate>'
                     b'</g:OwnershipChange></g:GLOBE_OECD>')
    assert "70022" in ids


def test_filingce_country_mismatch_60023():
    ids = _eval_real(b'<g:GLOBE_OECD xmlns:g="urn:oecd:ties:globe:v2">'
                     b'<g:MessageSpec><g:TransmittingCountry>DK</g:TransmittingCountry></g:MessageSpec>'
                     b'<g:FilingCE><g:ResCountryCode>SE</g:ResCountryCode></g:FilingCE></g:GLOBE_OECD>')
    assert "60023" in ids


def test_tin_issuedby_required_70005():
    ids = _eval_real(b'<g:GLOBE_OECD xmlns:g="urn:oecd:ties:globe:v2">'
                     b'<g:TIN TypeOfTIN="GIR3001">12345</g:TIN></g:GLOBE_OECD>')
    assert "70005" in ids


# --- Batch 2: conditional (70001/70002) + ref_integrity-type --------------
def _root(xml: bytes):
    from lxml import etree
    return etree.fromstring(xml)


def test_conditional_tin_70001_fires():
    from validator.rules.oecd_rules import evaluate, load_oecd_rules
    root = _root(b'<g:GLOBE_OECD xmlns:g="urn:oecd:ties:globe:v2" '
                 b'xmlns:s="urn:oecd:ties:globestf:v5">'
                 b'<g:CE><g:TIN TypeOfTIN="GIR3004" unknown="false">12345</g:TIN></g:CE>'
                 b'</g:GLOBE_OECD>')
    v = evaluate(root, load_oecd_rules())
    assert any(x["rule"]["oecd_rule"] == "70001" for x in v)


def test_conditional_tin_70002_fires():
    from validator.rules.oecd_rules import evaluate, load_oecd_rules
    root = _root(b'<g:GLOBE_OECD xmlns:g="urn:oecd:ties:globe:v2" '
                 b'xmlns:s="urn:oecd:ties:globestf:v5">'
                 b'<g:CE><g:TIN TypeOfTIN="GIR3001">NOTIN</g:TIN></g:CE>'
                 b'</g:GLOBE_OECD>')
    v = evaluate(root, load_oecd_rules())
    ids = {x["rule"]["oecd_rule"] for x in v}
    assert "70002" in ids and "70001" not in ids


def test_conditional_passes_when_correct():
    from validator.rules.oecd_rules import evaluate, load_oecd_rules
    # Korrekt NOTIN-TIN: GIR3004 + 'NOTIN' + unknown=true, ingen issuedBy.
    root = _root(b'<g:GLOBE_OECD xmlns:g="urn:oecd:ties:globe:v2" '
                 b'xmlns:s="urn:oecd:ties:globestf:v5">'
                 b'<g:CE><g:TIN TypeOfTIN="GIR3004" unknown="true">NOTIN</g:TIN></g:CE>'
                 b'</g:GLOBE_OECD>')
    v = evaluate(root, load_oecd_rules())
    assert not any(x["rule"]["oecd_rule"] in ("70001", "70002") for x in v)


def test_ref_integrity_type():
    from validator.rules.oecd_rules import evaluate
    ns = {"globe": "urn:oecd:ties:globe:v2", "stf": "urn:oecd:ties:globestf:v5"}
    root = _root(b'<g:R xmlns:g="urn:oecd:ties:globe:v2" xmlns:s="urn:oecd:ties:globestf:v5">'
                 b'<s:DocRefId>A</s:DocRefId><s:CorrDocRefId>A</s:CorrDocRefId>'
                 b'<s:CorrDocRefId>MISSING</s:CorrDocRefId></g:R>')
    rs = {"namespaces": ns, "rules": [
        {"id": "R", "level": "file", "name_da": "ref", "message_da": "ukendt {value}",
         "check": {"type": "ref_integrity", "source": "//stf:CorrDocRefId",
                   "target": "//stf:DocRefId"}}]}
    v = evaluate(root, rs)
    assert len(v) == 1 and v[0]["detail"].endswith("MISSING")


# --- Batch 3: format / value_range / compare (alle ikke-beregnings-typer) ---
def test_compare_period_60020():
    from validator.rules.oecd_rules import evaluate, load_oecd_rules
    root = _root(b'<g:GLOBE_OECD xmlns:g="urn:oecd:ties:globe:v2">'
                 b'<g:Period><g:Start>2025-12-31</g:Start><g:End>2025-01-01</g:End></g:Period>'
                 b'</g:GLOBE_OECD>')
    v = evaluate(root, load_oecd_rules())
    assert any(x["rule"]["oecd_rule"] == "60020" for x in v)


def test_format_type():
    from validator.rules.oecd_rules import evaluate
    ns = {"globe": "urn:oecd:ties:globe:v2", "stf": "urn:oecd:ties:globestf:v5"}
    root = _root(b'<g:R xmlns:g="urn:oecd:ties:globe:v2" xmlns:s="urn:oecd:ties:globestf:v5">'
                 b'<s:X>dk123</s:X><s:X>DK123</s:X></g:R>')
    rs = {"namespaces": ns, "rules": [
        {"id": "F", "level": "file", "name_da": "fmt", "message_da": "fejl {value}",
         "check": {"type": "format", "xpath": "//stf:X", "pattern": "[A-Z]{2}[0-9]+"}}]}
    v = evaluate(root, rs)
    assert len(v) == 1 and v[0]["detail"].endswith("dk123")


def test_value_range_type():
    from validator.rules.oecd_rules import evaluate
    ns = {"globe": "urn:oecd:ties:globe:v2", "stf": "urn:oecd:ties:globestf:v5"}
    root = _root(b'<g:R xmlns:g="urn:oecd:ties:globe:v2" xmlns:s="urn:oecd:ties:globestf:v5">'
                 b'<s:N>0</s:N><s:N>5</s:N></g:R>')
    rs = {"namespaces": ns, "rules": [
        {"id": "V", "level": "record", "name_da": "rng", "message_da": "ugyldig {value}",
         "check": {"type": "value_range", "xpath": "//stf:N", "exclude": 0}}]}
    v = evaluate(root, rs)
    assert len(v) == 1 and v[0]["detail"].endswith("0")


def test_all_noncalc_categories_have_type():
    """Vokabular-dækning: hver ikke-beregnings-kategori i kataloget skal kunne
    udtrykkes af en understøttet check-type."""
    import json
    from validator.rules.oecd_rules import _REFERENCE_DIR, _VALID_TYPES
    cat = json.load(open(os.path.join(_REFERENCE_DIR, "oecd_validation_rules_catalogue.json")))
    cats = set(cat["category_counts"]) - {"calculation", "other"}
    # required/forbidden udtrykkes af conditional/required_if/forbidden_if.
    expressible = _VALID_TYPES | {"required", "forbidden"}
    assert cats <= expressible, f"ikke-dækkede: {cats - expressible}"


# --- Uafhængig valideringssuite som CI-port --------------------------------
def test_validation_suite_all_pass():
    """Gate: den uafhængige valideringssuite skal have ren golden-base og
    bestå alle auto-scenarier (én planted defekt pr. eksekverbar kontrol)."""
    from validation.run_validation import run_all
    data = run_all()
    assert data["base_ok"], \
        f"golden-GIR gav fund: {data['base_fired']}"
    auto = [r for r in data["results"] if r["passed"] is not None]
    failed = [r["rule"] for r in auto if not r["passed"]]
    assert not failed, f"valideringsscenarier fejlede: {failed}"
    # Forventet: hver eksekverbar regel har et auto-scenarie.
    assert len(auto) == data["executable"]


# --- Scope-triage: ærligt dækningsbillede ----------------------------------
def test_scope_classification_complete():
    """Hver katalogregel har et scope, og summen rammer hele kataloget."""
    from validator.rules.oecd_rules import coverage
    c = coverage()
    assert sum(c["scope"].values()) == c["total_catalogue"] == 163
    # Eksekverbare i scope = eksekverbare i regelfilen.
    assert c["scope"].get("executable") == c["executable"]
    # Fil-validerbare = katalog − switched_off − out_of_scope.
    assert c["file_validatable"] == 163 - c["scope"].get("switched_off", 0) - c["out_of_scope"]
