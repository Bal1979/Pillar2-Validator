# Pillar II GIR-Validator — projektkontekst (agent hand-off)

> **Tværgående standarder (LÆS FØRST):** Ved nye værktøjer eller ændringer der
> rører login, design eller drift på tværs, læs `balai-platform/PLATFORM-BUILD-STANDARD.md`
> før du går i gang. Den fastlægger bl.a., at `SECRET_KEY` SKAL være **identisk**
> på tværs af alle værktøjer (delt login), at cookien deles på `.balai.dk`, og
> hvordan et værktøj kobles på den centrale brugerstyring.


Kontinuitets-/hand-off-note (samme stil som SAF-T-validatoren): hvor projektet
er, hvorfor valgene blev truffet, og hvad der er åbent. Hold den opdateret.

## Hvad er det

Et web-værktøj (Flask) der validerer en færdig **GloBE Information Return (GIR)**
mod OECD's officielle skema + nummererede valideringsregler + juni-2026-guidance
+ danske felt-regler. Søsterprodukt til SAF-T-validatoren på samme platform
(balai.dk), målrettet danske rådgivere og økonomifunktioner. Niche: validerings-/
kontrollaget (tag en færdig GIR, fortæl præcist hvad der er galt) — modsat de
store, der spiller end-to-end. Se `ARCHITECTURE.md` for fuld baggrund.

## Status — lag 1-4 kører, beregningsmotor aktiv

Pipeline lag 1-4 implementeret og testet. Nøgletal (version/regler/typer/tests)
holdes ajour af `tools/update_docs.py` — se blokken nedenfor:

<!-- STATS:START -->
**Nøgletal (katalog 0.18.0):** 92/163 OECD-regler eksekverbare (heraf 19 beregningsregler) · 14 check-typer · 80 tests grønne.
<!-- STATS:END -->

- **Regelgrundlag (komplet).** `reference/oecd_validation_rules_catalogue.json` =
  ALLE 163 officielle regler (39 file / 124 record) udtrukket fra GIR *Status
  Message* User Guide (juli 2025) Part 4, m. fulde XPaths, `switched_off_2026`
  (60025/60026/70092/70028) og check-type-klassificering. `guidance_deviations_2026-06.json`
  = de 14 juni-2026-issues. Kilde-PDF'er i `docs/oecd_sources/` (git-ignoreret).
- **Eksekverbare regler.** `reference/oecd_validation_rules.json` (antal: se nøgletal).
  `validator/rules/oecd_rules.py` evaluerer + respekterer switched_off. Umbrella-
  regler P2-030 (file) / P2-040 (record). `tools/sync_oecd_rules.py --check/--list`
  rapporterer dækning.
- **Check-typer (14):** unique, unique_in, required_if, forbidden_if, not_equal,
  mutually_exclusive, conditional (if/then m. element+attribut), conditional_ref,
  ref_integrity, format, value_range, compare, cardinality, **calculation**
  (aritmetisk formel: beregnet vs. rapporteret; subtract/sum/multiply/divide/sum_all,
  rekursivt). Dækker ALLE katalog-kategorier.
- **Golden-fixtur** `tests/fixtures/gir_valid_rich.xml`: komplet, skemagyldig GIR
  (GeneralSection/CorporateStructure + JurisdictionSection/GLoBETax/ETR/
  OverallComputation), fuldt godkendt — regressions- og demo-facit, også end-to-end
  for beregningsmotoren. Plus minimal `gir_valid.xml`.
- **VIGTIGT — disciplin der har fanget ægte fejl:** hver ny regel verificeres med
  (a) en negativ case der bekræfter at den fyrer, og (b) golden-fixturen (ingen
  falsk positiv). Det har fanget bl.a.: forkert element-navn `GloBEStatus` vs
  `GlobeStatus`; `OwnershipPercentage` er en fraktion 0-1 (ikke 0-100);
  `present`/`absent` skulle tjekke eksistens ikke tekst. **Behold denne disciplin.**
- **Aktuel status/tal:** se `docs/Regel-sporbarhedsmatrix.md` (auto-genereret),
  `docs/CHANGELOG.md`, `docs/Godkendelses-overblik.md`, `docs/OECD_regelgrundlag.md`.
- **Vej frem (ren data-kodning):** resten af beregningsreglerne + de øvrige
  conditional/compare/SafeHarbour-regler — alle udtrykkelige og testbare mod golden-fixturen.

### Tidligere

- **Officielle OECD-skemaer hentet** og i `schemas/gir/` + `schemas/status/`
  (GIR: GLOBEXML_v1.0 + isoglobetypes_v1.1 + oecdglobetypes_v5.0; Status:
  GIRStatusMessageXML_v1.0 + isocsmtypes_v1.1), verificeret well-formed m. provenance.
- **Kerne kopieret fra SAF-T** (bevidst tæt på, så senere konsolidering til delt
  bibliotek bliver mekanisk): `validator/rules/` = finding, severity (5 niveauer),
  profiles, catalog + `build_finding()`-fabrik.
- **Regelkatalog** `validator/rules/P2-Validation-Rules.json` (v0.1.0): 8 lag,
  3 profiler. Regler: P2-001 (XSD), P2-002 (XML), P2-010 (rod), P2-011 (MessageSpec),
  P2-012 (GLOBEBody), P2-013 (JurisdictionSection).
- **Motor** `validator/engine.py` + `validator/xsd_validator.py`:
  **Lag 1** = well-formed (P2-002) + XSD-validering DIREKTE mod `schemas/gir/`
  (P2-001, XXE fra, skema cachet). **Lag 2** = struktur (P2-010..013) + udtræk af
  `CompanyContext` (MessageRefId, MessageTypeIndic, periode, koncernnavn/TIN).
  Namespace `urn:oecd:ties:globe:v2`, rod `GLOBE_OECD`.
- **Rapport** `validator/presentation.py` + `templates/rapport.html`: dansk dom
  (afvist/betinget/godkendt), severity-chips, fund grupperet pr. lag m. forslag + sted.
- **Flask-app** `app.py`: `/`, `/sundhed`, `/valider` (HTML-rapport; `?format=json`
  for JSON) + sikkerhedsheaders, kildefil slettes straks efter kørsel.
- **Tests** `tests/test_smoke.py` (16) + fixture `tests/fixtures/gir_valid.xml`
  (minimal skemagyldig GIR). Alle grønne.

## Central brugerstyring (balai_auth) — login deles på tværs af *.balai.dk

Pillar II er koblet på den fælles BALAI-brugerstyring, præcis som SAF-T:

- **Pakke:** `balai_auth/` (kopi af den delte pakke) + `auth.py`-shim med
  `TOOL_SLUG = "pillar2"`. `app.py` kalder `auth_module.init_app(app)` og gater
  ruterne med `@requires_auth` (kræver BÅDE login OG adgang til slug `pillar2`).
  `/sundhed` er bevidst offentlig (health check). Ikke-loggede sendes til
  `AUTH_BASE_URL` (auth.balai.dk).
- **Slug registreret centralt:** `pillar2` er tilføjet i `balai-auth`'s
  `balai_auth/config.py` TOOLS — så admin-UI'et på auth.balai.dk kan tildele
  adgang. **Kræver redeploy af balai-auth** for at slå igennem i admin.
- **Env-variable (Railway, SKAL matche SAF-T for delt login):** `SECRET_KEY`,
  `SESSION_COOKIE_DOMAIN=.balai.dk`, `AUTH_BASE_URL=https://auth.balai.dk`,
  `DATABASE_URL` (delt Postgres = central brugerdb), `FLASK_ENV=production`.
  Pillar II har endnu ingen egen datalagring, så `RUNS_DB_PATH`/`AUTH_DB_PATH`
  er ikke i brug. Pillar II skal serveres på et `*.balai.dk`-subdomæne, ellers
  deles cookien ikke.
- **Afhængigheder:** `SQLAlchemy` + `psycopg[binary]` i `requirements.txt`
  (kør `pip install -r requirements.txt` før pytest første gang).
- **Tests:** `conftest.py` sætter en isoleret temp-SQLite som auth-DB (ingen
  delt Postgres i test). `test_app_requires_login` bekræfter gating;
  `_login_pillar2()` opretter en all_access-bruger og logger ind via
  session_transaction. Landing-kort på balai.dk tilføjes når subdomænet er live.

## Uafhængig valideringssuite + godkendelsespakke (EY-ramme)

- **Valideringssuite** `validation/`: `synth.py` planter ÉN målrettet defekt pr.
  eksekverbar OECD-regel ud fra dens `check`-definition (defekt-synthesizer);
  `run_validation.py` bekræfter at netop den regel fyrer + at golden-GIR er ren.
  **Alle eksekverbare regler består** (antal: se STATS-nøgletal), gated i CI
  (`python -m validation.run_validation`; også som
  pytest `test_validation_suite_all_pass`). Ny regel → automatisk dækket.
- **Godkendelsespakke** `docs/` (1:1 med SAF-T): 4 docx + sporbarhedsmatrix.xlsx +
  valideringsrapport.md + README + CHANGELOG, alle med `Pillar2-Validator_`-præfiks.
  Generatorer: `tools/build_approval_docs.js` (docx-js; kør `npm install docx` —
  `node_modules` gitignored) og `tools/build_traceability.py` (xlsx fra regel-JSON).
  De gamle uprefiksede `.md` er bevaret som arbejdskilde. Auth = **Dækket**.
- **Regenerér pakken:** `python -m validation.run_validation` → rapport;
  `python tools/build_traceability.py` → xlsx; `node tools/build_approval_docs.js`
  → docx; `python tools/update_docs.py` → STATS + matrix.md.

## Genoptag hurtigt

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
pytest                                   # smoke-tests + valideringssuite-port
python app.py                            # kør lokalt → http://127.0.0.1:5000
python tools/sync_oecd_schemas.py --import \
  --gir-zip ~/Downloads/globe-xsd.zip \
  --status-zip ~/Downloads/xml-schema-gir-status-message.zip   # opdatér skemaer
```

OECD's CDN afviser automatiseret download (HTTP 403), så skemaer hentes i
browseren og importeres med `--import`. `--check`/`--apply` virker fra miljøer
hvor CDN'en ikke blokerer.

## Arkitektur i korte træk

- **Data-drevet regelmotor** (delt design m. SAF-T): kataloget er source of truth;
  motoren læser det. Ny/ændret regel → opdatér JSON, bump `catalog_version`, tests.
- **Skemaer = source of truth** i `schemas/` (officielle OECD-XSD'er), holdt friske
  af `tools/sync_oecd_schemas.py`.
- **8-lags pipeline**: 1 Skema · 2 Struktur · 3 OECD file-level · 4 OECD record-level
  · 5 Guidance-afvigelser (juni 2026) · 6 GIR/QDMTT-kryds · 7 Danske felt-regler
  · 8 Referenceintegritet. (Fase 0: kun lag 1.)
- **To skemaer**: GIR (input vi validerer) + Status Message (output-format, Fase 6).
- **Kilde-agnostisk QDMTT** (ARCHITECTURE §8.1): embedded | separat fil | dataudtræk.

## Konventioner (vigtige)

- Skriv dansk, klart og konkret. Slet aldrig filer uden tilladelse.
- Kopierede kerne-moduler holdes tæt på SAF-T (kun navne/tekster afviger), så de
  senere kan udtrækkes til ét delt bibliotek.
- `BalSeverity` = BALAI-platformens fælles severity (ikke SAF-T-specifik).

### Regel-batch-rutine (FØLG denne — den har fanget ægte fejl)

1. **Verificér FØR commit:** hver ny regel testes mod (a) et negativt fragment der
   bekræfter at den fyrer, og (b) golden-fixturen `tests/fixtures/gir_valid_rich.xml`
   (skal forblive ren — ingen falsk positiv). Ship kun regler der består begge.
2. Tilføj reglen i `reference/oecd_validation_rules.json`, markér `executable` i
   kataloget, og tilføj en pytest-case.
3. Bump `catalog_version` + tilføj en `docs/CHANGELOG.md`-entry.
4. **Kør `python3 tools/update_docs.py`** — regenererer sporbarhedsmatrix +
   regelgrundlag og opdaterer STATS-markører i prosa-docs. Så driver dokumentationen aldrig.
5. Kør `pytest` (skal være grøn) + `python3 tools/sync_oecd_rules.py --check`.

Fabrikér aldrig OECD-regelnumre — seed kun verificeret semantik. Beregningsregler
(`calculation`) bruger fraktioner 0-1 for procenter; element-navne staves *præcist*
som i skemaet (fx `GlobeStatus`, ikke `GloBEStatus`).

## Næste faser (se ARCHITECTURE.md §9)

- **Fase 1**: LEVERET (lag 1-2 + rapport).
- **Fase 2**: Lag 3-4 — katalogisér OECD's nummererede regler (`sync_oecd_rules.py`
  + reference/oecd_validation_rules_*.json), XPath-pointers.
- **Fase 3**: Lag 5 — guidance-afvigelser (juni 2026).
- **Fase 4**: Lag 6 — GIR/QDMTT-kryds. **Fase 5**: Lag 7-8 (efter DK-afklaring).
- **Fase 6**: Status Message-output. **Fase 7**: dataudtræk-input.

## Åbne danske krav (skal verificeres før lag 7) — se ARCHITECTURE.md §7

MessageTypeIndic-/korrektionsregler, evt. dansk skema/extension, indsendelseskanal,
frister, DAC9-udveksling, valuta/sprog. Verificeres mod skat.dk + Den juridiske
vejledning C.K. + DAC9.
