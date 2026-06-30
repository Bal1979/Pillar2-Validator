#!/usr/bin/env node
/* =========================================================================
 * build_approval_docs.js — genererer godkendelses-dokumentationspakken (4 docx)
 * for Pillar II GIR-Validator, efter SAF-T/VIES/Data-Extract-skabelonen.
 *
 * Output (docs/):
 *   Pillar2-Validator_Godkendelses-overblik.docx        (START HER)
 *   Pillar2-Validator_Solution_Architecture.docx
 *   Pillar2-Validator_Sikkerhed_og_databehandling.docx
 *   Pillar2-Validator_Hosting_og_drift.docx
 *
 * Kør (mest pålideligt — lokal install):
 *   cd <repo> && npm install docx && node tools/build_approval_docs.js
 * (node_modules er gitignored; docx resolves automatisk fra lokal node_modules)
 * ========================================================================= */

const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  AlignmentType, LevelFormat, HeadingLevel, BorderStyle, WidthType,
  ShadingType, PageBreak,
} = require("docx");

const DOCS = path.resolve(__dirname, "..", "docs");
const DATE = "30. juni 2026";
const CONTENT_W = 9360;
const NAVY = "1B365D";

// --- Nøgletal beregnes fra kataloget, så docx aldrig driver ----------------
const REF = path.resolve(__dirname, "..", "reference");
const CAT = JSON.parse(fs.readFileSync(path.join(REF, "oecd_validation_rules_catalogue.json"), "utf8"));
const RULESET = JSON.parse(fs.readFileSync(path.join(REF, "oecd_validation_rules.json"), "utf8"));
const SCOPE = {};
for (const r of CAT.rules) { const s = r.scope || "candidate"; SCOPE[s] = (SCOPE[s] || 0) + 1; }
const TOTAL = CAT.rules.length;
const EXEC = RULESET.rules.length;
const N_CALC = RULESET.rules.filter((r) => r.check && r.check.type === "calculation").length;
const COVERED = SCOPE.covered_by || 0;
const OOS = SCOPE.out_of_scope || 0;
const CAND = SCOPE.candidate || 0;
const OFF = SCOPE.switched_off || 0;
const FILEVAL = TOTAL - OFF - OOS;
const EFFECTIVE = EXEC + COVERED;
const PCT = FILEVAL ? Math.round((100 * EFFECTIVE) / FILEVAL) : 0;

// --- Byggehjælpere ---------------------------------------------------------
const H1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(t)] });
const H2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(t)] });
const P = (t, opts = {}) => new Paragraph({ spacing: { after: 120 }, children: [new TextRun({ text: t, ...opts })] });

function bullets(items) {
  return items.map((t) => new Paragraph({
    numbering: { reference: "bullets", level: 0 }, spacing: { after: 60 },
    children: [new TextRun(t)],
  }));
}
function numbered(items, ref) {
  return items.map((t) => new Paragraph({
    numbering: { reference: ref, level: 0 }, spacing: { after: 60 },
    children: [new TextRun(t)],
  }));
}
const BORD = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const BORDERS = { top: BORD, bottom: BORD, left: BORD, right: BORD };
function cell(text, width, { head = false, bold = false } = {}) {
  return new TableCell({
    borders: BORDERS, width: { size: width, type: WidthType.DXA },
    shading: head ? { fill: NAVY, type: ShadingType.CLEAR, color: "auto" } : undefined,
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    children: [new Paragraph({ children: [new TextRun({ text, bold: head || bold, color: head ? "FFFFFF" : undefined })] })],
  });
}
function table(headers, rows, widths) {
  const headRow = new TableRow({ tableHeader: true, children: headers.map((h, i) => cell(h, widths[i], { head: true })) });
  const bodyRows = rows.map((r) => new TableRow({ children: r.map((c, i) => cell(String(c), widths[i])) }));
  return new Table({ width: { size: CONTENT_W, type: WidthType.DXA }, columnWidths: widths, rows: [headRow, ...bodyRows] });
}
function titleBlock(title, subtitle, note) {
  const out = [
    new Paragraph({ spacing: { after: 60 }, children: [new TextRun({ text: "BALAI · Pillar II GIR-Validator", bold: true, color: NAVY, size: 28 })] }),
    new Paragraph({ spacing: { after: 60 }, children: [new TextRun({ text: title, bold: true, size: 44, color: NAVY })] }),
    new Paragraph({ spacing: { after: 200 }, children: [new TextRun({ text: subtitle, italics: true, size: 24, color: "555555" })] }),
  ];
  if (note) out.push(new Paragraph({ spacing: { after: 120 }, children: [new TextRun({ text: note, size: 20, color: "555555" })] }));
  out.push(new Paragraph({ spacing: { after: 60 }, children: [new TextRun({ text: "Klassifikation: Fortroligt — internt.", size: 20, color: "777777" })] }));
  out.push(new Paragraph({ spacing: { after: 120 }, children: [new TextRun({ text: `BALAI · ${DATE}`, size: 20, color: "777777" })] }));
  out.push(new Paragraph({ children: [new PageBreak()] }));
  return out;
}
function makeDoc(children) {
  return new Document({
    styles: {
      default: { document: { run: { font: "Arial", size: 22 } } },
      paragraphStyles: [
        { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
          run: { size: 30, bold: true, font: "Arial", color: NAVY }, paragraph: { spacing: { before: 280, after: 140 }, outlineLevel: 0 } },
        { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
          run: { size: 25, bold: true, font: "Arial", color: "2E5C8A" }, paragraph: { spacing: { before: 180, after: 100 }, outlineLevel: 1 } },
      ],
    },
    numbering: {
      config: [
        { reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
        ...["n1", "n2", "n3", "n4"].map((ref) => ({ reference: ref, levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] })),
      ],
    },
    sections: [{ properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } }, children }],
  });
}

// ===========================================================================
// 1) GODKENDELSES-OVERBLIK
// ===========================================================================
const overblik = makeDoc([
  ...titleBlock("Godkendelses-overblik", "Forside- og statusdokument for værktøjsgodkendelse",
    "Indgangen til pakken: hvad findes, hvad er dækket, og hvad udestår. Skrevet efter best practice og skal indpasses i EY's konkrete godkendelsesskabelon. Værktøjet er på research-preview-niveau."),

  H1("1. Produktet kort fortalt"),
  P("Pillar II GIR-Validator er et webbaseret kontrolværktøj, der validerer en færdig GloBE Information Return (GIR) mod OECD's officielle XML-skema og de officielle, nummererede valideringsregler, og rapporterer præcist hvad der er galt, hvor (XPath/linje) og hvor alvorligt — på dansk. Det er et selvstændigt valideringslag, ikke en beregnings- eller indberetningsmotor: det tager en fil, andre har produceret, og auditerer den."),
  P("Positioneringen er bekræftet ved benchmark mod PwC, KPMG og Deloitte, der alle spiller end-to-end (data → beregning → filing) og ikke tilbyder et frittstående valideringslag. Værktøjet er søsterprodukt til SAF-T-validatoren på samme platform (balai.dk) og deler arkitektur, severity-model, central brugerstyring og driftsmodel."),

  H1("2. Dokumentationspakke"),
  P("Alle artefakter ligger versionsstyret i repoets docs/-mappe (koden i validator/, validation/ og tools/):"),
  table(["Fil", "Indhold"], [
    ["Pillar2-Validator_Godkendelses-overblik.docx", "Dette dokument — status og indgang til pakken."],
    ["Pillar2-Validator_Solution_Architecture.docx", "Formål, scope, arkitektur, 8-lags model, regelmotor, referencedata, QA, hosting, åbne punkter."],
    ["Pillar2-Validator_Sikkerhed_og_databehandling.docx", "Datakategorier, dataflow, inputhærdning, app-sikkerhed, trusselsmodel, GDPR."],
    ["Pillar2-Validator_Hosting_og_drift.docx", "Nuværende vs. EY-platform, migrationsplan, env-inventar, backup, roller, support."],
    ["Pillar2-Validator_Regel-sporbarhedsmatrix.xlsx", "Hver kontrol → OECD-kilde → modul → testdækning; fuldt katalog; referencedata-provenance; severity."],
    ["Pillar2-Validator_Valideringsrapport.md", "Auto-genereret resultat af den uafhængige valideringssuite."],
  ], [4200, 5160]),
  P("«Udkast» = skrevet efter best practice, men skal gennemgås/godkendes af de relevante funktioner og indpasses i EY's skabelon.", { italics: true }),

  H1("3. Godkendelsesparathed pr. område"),
  table(["Område", "Status", "Bemærkning"], [
    ["Skema-validering (lag 1)", "Dækket", "Direkte mod OECD's officielle GIR-XSD; XXE slået fra; testet."],
    ["Strukturel integritet (lag 2)", "Dækket", "Rod/MessageSpec/GLOBEBody/sektioner + CompanyContext-udtræk."],
    ["OECD-regelgrundlag (dokumentation)", "Dækket", "Alle 163 officielle regler udtrukket og klassificeret; 4 switched-off respekteres; provenance."],
    ["OECD-regelmotor (lag 3-4)", "Dækket (voksende)", `${EXEC}/${TOTAL} regler eksekverbare (${N_CALC} beregningsregler); datadrevet motor dækker alle check-kategorier.`],
    ["Auth & adgang", "Dækket", "Central BALAI-brugerstyring (balai_auth): delt SSO på *.balai.dk, per-tool-adgang via slug 'pillar2', session/CSRF/rate-limit."],
    ["Uafhængig validering", "Dækket", "Valideringssuite: én planted defekt pr. eksekverbar kontrol (78/78 består), golden-GIR ren, gated i CI."],
    ["Sikkerhed (HTTP/input)", "Dækket (review udestår)", "Stram CSP uden CDN'er, HSTS, fuld header-pakke, XXE fra, parametreret. Fuld databehandlingsbeskrivelse skal review'es."],
    ["Guidance-afvigelser (lag 5)", "Udkast", "Switched-off-regler respekteres; AdditionalDataPoint-anerkendelse udestår."],
    ["GIR/QDMTT-kryds (lag 6)", "Åbent", "Kilde-agnostisk design klar; ikke implementeret."],
    ["Danske felt-regler (lag 7)", "Åbent", "Afventer afklaring mod Skattestyrelsen/DAC9."],
    ["Hosting", "Udkast", "Kører på pillar2.balai.dk (Railway, midlertidig dev/demo); EY-platform er forudsætning for klientdata."],
    ["Testsuite", "Dækket (voksende)", "74 enhedstests + valideringssuite + lint-port."],
  ], [2900, 1700, 4760]),

  H1("4. Regeldækning (ærligt billede)"),
  P(`Det officielle katalog rummer ${TOTAL} regler. De er ikke alle beregnet til et fil-valideringsværktøj: en del er transmissions-/modtagerstatus eller afhænger af besked-/korrektionshistorik på tværs af indsendelser. Fordelingen er:`),
  table(["Kategori", "Antal", "Forklaring"], [
    ["Eksekverbare kontroller", String(EXEC), "Kodet i regelmotoren og verificeret af valideringssuiten (én planted defekt pr. kontrol)."],
    ["Dækket af ækvivalent regel", String(COVERED), "Samme semantik håndhæves allerede af en eksekverbar regel."],
    ["Kandidater (kan kodes)", String(CAND), "Fil-validerbare regler der endnu ikke er kodet; kodes batch-vis."],
    ["Uden for scope (fil-validering)", String(OOS), "Transmissions-/modtagerstatus, kryds-besked-/korrektionshistorik eller eksternt register."],
    ["Slået fra (2026-guidance)", String(OFF), "Fyres aldrig jf. juni-2026-guidance."],
  ], [3100, 1000, 5260]),
  P(`Fil-validerbare regler i alt: ${FILEVAL} (katalog minus switched-off og uden-for-scope). Effektivt dækket: ${EFFECTIVE} (eksekverbare + ækvivalent) = ${PCT} %. De resterende ${CAND} kandidater kodes batch-vis. Den fulde klassifikation pr. regel ligger i sporbarhedsmatrixen (fane "Dækningsoverblik" + "Fuldt katalog").`, { bold: true }),

  H1("5. Åbne punkter (kræver EY / eksterne beslutninger)"),
  P("Disse kan ikke lukkes i koden alene — de kræver beslutninger, adgang eller eksterne parter:"),
  ...bullets([
    "Mapning mod EY's konkrete godkendelsesskabelon (denne pakke er skrevet efter best practice).",
    "Platformsflytning til EY-godkendt infrastruktur (EU-dataplacering) + databehandleraftale (DPA).",
    "Lag 5: AdditionalDataPoint-workarounds anerkendes som gyldige (juni-2026-guidance).",
    "Lag 6 (GIR/QDMTT-kryds) mod en normaliseret QDMTT-model.",
    "Lag 7 (danske felt-regler) verificeret mod Skattestyrelsen/Den juridiske vejledning C.K./DAC9.",
    "Penetrationstest / sikkerhedsgennemgang af en uafhængig part; SOC 2 / ISO 27001 fra driftsplatformen.",
    "Stress-test på rigtige klientfiler afstemt mod OECD's egen validator som facit.",
    "Support- og vedligeholdelsesmodel samt rolle-/ansvarsbeskrivelse.",
  ]),

  H1("6. Anbefalet rækkefølge mod godkendelse"),
  ...numbered([
    "Forelæg pakken for EY's tool-governance og få den konkrete godkendelsesskabelon.",
    "Indpas de fire dokumenter + matrix/rapport i EY's skabelon og afklar manglende afsnit.",
    "Aftal driftsplatform og igangsæt platformsflytning + DPA parallelt.",
    "Kod de resterende eksekverbare regler batch-vis (matrix + valideringssuite holder sig selv ajour).",
    "Stress-test mod rigtige GIR-filer; ret driftsfund ved roden.",
    "Bestil penetrationstest og indstil til formel godkendelse, når åbne punkter er lukket eller planlagt.",
  ], "n1"),
  P(`Status pr. ${DATE}: Værktøjet er på research-preview-niveau. Alt der kan lukkes i kode og dokumentation internt, er på plads (lag 1-4, central login, uafhængig valideringssuite). De resterende punkter er bevidst markeret som åbne, fordi de kræver EY-beslutninger, fagafklaring eller eksterne parter.`, { bold: true }),
]);

// ===========================================================================
// 2) SOLUTION ARCHITECTURE
// ===========================================================================
const arch = makeDoc([
  ...titleBlock("Løsnings- og arkitekturbeskrivelse", "Grundlag for produkt-/værktøjsgodkendelse",
    "Best practice-grundlag; endnu ikke mappet mod EY's konkrete godkendelsesskabelon. Afsnit 11 lister åbne punkter."),

  H1("1. Formål og afgrænsning"),
  P("Pillar II GIR-Validator validerer en færdig GloBE Information Return (GIR) mod OECD's officielle XML-skema og de officielle valideringsregler, og rapporterer præcist hvad der er galt, hvor og hvor alvorligt — på dansk. Det er et kontrol-/valideringslag, ikke en beregnings- eller indberetningsmotor."),
  P("Afgrænsning (bevidst): Værktøjet beregner ikke top-up tax og indsender ikke. Det auditerer en fil, andre har produceret. Dette dokument beskriver arkitektur, regelmodel, datahåndtering, sikkerhed, kvalitetssikring og drift som grundlag for en formel værktøjsgodkendelse, og ledsages af en regel-sporbarhedsmatrix (Excel)."),

  H1("2. Teknologistack"),
  P("Python 3.13, Flask (web), lxml (streaming XML + XSD), pytest (testsuite), SQLAlchemy + psycopg til central brugerstyring. Samme stack og konventioner som SAF-T-validatoren, så drift og governance kan genbruges. Ingen tredjepartsafhængigheder i selve regelmotoren ud over lxml."),

  H1("3. Arkitektur i korte træk"),
  ...bullets([
    "Data-drevet regelmotor: reglerne er data (JSON), ikke kode. Motoren (validator/rules/oecd_rules.py + engine.py) læser katalogerne og evaluerer. Ny/ændret regel = dataændring + test, ikke motorændring.",
    "Skemaer som source of truth: OECD's officielle XSD'er ligger i schemas/ og valideres direkte imod. Holdes friske af tools/sync_oecd_schemas.py.",
    "To regelkilder: oecd_validation_rules_catalogue.json = hele den officielle regelliste (163, referencegrundlag); oecd_validation_rules.json = den eksekverbare delmængde (78) motoren evaluerer.",
    "Findings-model: hvert fund har rule_id, lag (1-8), severity (5 niveauer), dansk besked + forslag og en Location (linje/XPath/element). Samlet dom: afvist / betinget godkendt / godkendt.",
    "Output: dansk HTML-rapport (og JSON via ?format=json). OECD Status Message-XML som output-format er planlagt (Fase 6).",
  ]),

  H1("4. Dataflow"),
  ...numbered([
    "Bruger logger ind via central BALAI-login og uploader en GIR-XML (fremtid: input fra dataudtræk-værktøjet via et kilde-agnostisk interface).",
    "Filen gemmes midlertidigt, pipelinen kører (lag 1-8), og kildefilen slettes straks efter kørsel.",
    "Resultatet (EngineOutcome) renderes som rapport. Ingen klientdata persisteres i nuværende fase (historik/revisionslog kan tilføjes som i SAF-T).",
  ], "n2"),

  H1("5. Den 8-lags valideringsmodel"),
  table(["Lag", "Navn", "Status"], [
    ["1", "Skema & syntaks (well-formed + XSD mod GIR-skema)", "Aktiv"],
    ["2", "Strukturel integritet (rod, MessageSpec, GLOBEBody, sektioner)", "Aktiv"],
    ["3", "OECD-regler, file-level (nummererede)", "Aktiv (delmængde)"],
    ["4", "OECD-regler, record-level (nummererede)", "Aktiv (delmængde)"],
    ["5", "Guidance-afvigelser (juni 2026)", "Delvist (switched-off respekteres)"],
    ["6", "GIR/QDMTT-kryds", "Planlagt"],
    ["7", "Danske felt-regler", "Planlagt (afventer afklaring)"],
    ["8", "Referenceintegritet", "Delvist (ref_integrity-type findes)"],
  ], [700, 6260, 2400]),
  P("Lag 1-2 er blokerende (fejl her gør dybere lag meningsløse). Severity-modellen og dommen er fælles med SAF-T (Kritisk/Væsentlig/Medium/Lav/Info)."),

  H1("6. Regelmotorens vokabular (check-typer)"),
  P("Motoren udtrykker i dag 14 kontroltyper, der tilsammen dækker alle kategorier i det officielle katalog (inkl. beregning): unique, unique_in, required_if, forbidden_if, not_equal, mutually_exclusive, conditional (if/then med element + attributter; operatorer present/absent/equals/not_equals/in/not_in/contains/lt/gt/le/ge/eq/ne — med dato-/år-/tal-coercion, sammenligning mod et andet elements værdi (ref) og år-offset, fx 'år ≥ periodeslut − 4'), ref_integrity, conditional_ref, format (regex), value_range, compare (dato/år/tal-ordning), cardinality, og calculation."),
  P("calculation er en beregningsmotor, der evaluerer aritmetiske formler (subtract/sum/multiply/divide/sum_all, rekursivt, med litteral-konstanter og tolerance) over GIR'ens felter og sammenligner beregnet mod rapporteret værdi. 15 beregningsregler er aktive; resten kodes batch-vis."),

  H1("7. Referencedata og provenance"),
  ...bullets([
    "Skemaer: OECD GIR XML Schema (GLOBEXML_v1.0 + isoglobetypes + oecdglobetypes) + GIR Status Message Schema, udpakket i schemas/ med _provenance.json (kilde, sha256, dato). Manifest i schemas/SCHEMA_SOURCES.md.",
    "Regler: udtrukket fra OECD GIR Status Message User Guide (juli 2025) Part 4 og guidance (juni 2026). Kilde-PDF'er i docs/oecd_sources/. Overblik i OECD_regelgrundlag.md.",
    "OECD opdaterer løbende skema og regler; en forældet lokal kopi kan afvise gyldige filer → sync-/selvtjek-mekanik som i SAF-T (månedlig GitHub Action).",
  ]),

  H1("8. Central brugerstyring og adgang"),
  P("Værktøjet er koblet på den fælles BALAI-brugerstyring (pakken balai_auth), præcis som SAF-T. Login sker centralt på auth.balai.dk; sessionscookien deles på tværs af *.balai.dk (delt SECRET_KEY + SESSION_COOKIE_DOMAIN), så ét login gælder alle værktøjer. Adgang til netop dette værktøj styres per bruger via tool-sluggen 'pillar2' (entitlements i en delt PostgreSQL). Alle ruter undtagen sundhedstjek er beskyttet med login + adgangstjek; uautoriserede sendes til central login. Session er browser-session-cookie med absolut 12-timers grænse, CSRF-beskyttelse og databaseunderstøttet login-rate-limit."),

  H1("9. Kvalitetssikring"),
  ...bullets([
    "Automatiseret enhedstest-suite (pytest), pr. nu 74 tests: katalogindlæsning, severity/dom, XSD-validering (valid + planted-invalid), strukturkontroller, hver check-type, switched-off-respekt, login-gating og app-endpoints.",
    "Uafhængig valideringssuite (validation/): for hver eksekverbar OECD-kontrol plantes ÉN målrettet defekt, og det bekræftes, at netop den kontrol fyrer — og at den rene golden-GIR ikke giver fund. 78/78 består; gated i CI (python -m validation.run_validation).",
    "Lint af regelfilen (tools/sync_oecd_rules.py --check): struktur + at hver XPath kompilerer; rapporterer dækning.",
    "To skemagyldige GIR-fixturer: en minimal (gir_valid.xml) og en komplet golden-fixtur (gir_valid_rich.xml), bygget fra de faktiske skema-krav. Golden-fixturen er fuldt godkendt og fungerer som regressions- og demo-facit, også end-to-end for beregningsmotoren.",
  ]),

  H1("10. Ændringsstyring"),
  P("Ny/ændret kontrol → opdatér regel-JSON (+ bump catalog_version), tests, CHANGELOG.md, sporbarhedsmatrix og valideringssuite. Sporbarhedsmatrix og valideringsrapport regenereres deterministisk fra kataloget (tools/build_traceability.py, validation/run_validation.py), så de aldrig kommer ud af sync. Markdown-/docx-dokumenterne versioneres med koden."),

  H1("11. Begrænsninger og åbne punkter"),
  ...bullets([
    "Eksekverbar regeldækning er 78/163 (se sporbarhedsmatrix); resten kodes batch-vis. Beregningsmotoren er aktiv; øvrige beregningsregler kodes løbende.",
    "Lag 6 (GIR/QDMTT) og lag 7 (danske felt-regler) er planlagte; danske udfyldningsregler skal verificeres mod Skattestyrelsen/DAC9.",
    "Persistens/historik/revisionslog og Status Message-output er planlagt (som i SAF-T-modellen).",
    "Hosting, penetrationstest, SOC 2/ISO og DPA følger EY-platformen (jf. SAF-T).",
  ]),
]);

// ===========================================================================
// 3) SIKKERHED OG DATABEHANDLING
// ===========================================================================
const sec = makeDoc([
  ...titleBlock("Sikkerheds- og databehandlingsbeskrivelse", "Grundlag for godkendelse — skal review'es af jura/databeskyttelse og sikkerhed",
    "Udkast: app- og inputsikkerhed er på plads; den fulde databehandlingsbeskrivelse (DPA, dataplacering, logning) skal gennemgås af de relevante funktioner."),

  H1("1. Datakategorier"),
  P("En GIR indeholder følsomme koncern-/skatteoplysninger: enheds- og koncernnavne, TIN'er, jurisdiktioner, regnskabstal, effektiv skattesats og top-up tax. Behandles som fortroligt forretningsdata. Værktøjet behandler ikke persondata om privatpersoner som kerneformål, men TIN/navne kan forekomme. Den centrale brugerstyring behandler desuden persondata om brugerne (e-mail, login-/hændelseslog)."),

  H1("2. Dataflow og dataminimering"),
  ...numbered([
    "Bruger logger ind via central BALAI-login og uploader en GIR-XML.",
    "Filen gemmes midlertidigt under kørsel og slettes straks efter (ingen varig lagring af kildefilen i nuværende fase).",
    "Resultatet vises som rapport i brugerens session. Der persisteres ikke klientdata i nuværende fase (historik/revisionslog kan tilføjes som i SAF-T, med retention-styring).",
    "Ingen klientdata sendes til tredjeparter. Referencedata (skema/regler) er statiske, lokale filer — ingen eksterne opslag under validering.",
  ], "n3"),

  H1("3. Inputhærdning"),
  ...bullets([
    "XXE slået fra: XML-parseren kører med resolve_entities=False og no_network=True — ingen ekstern entitetsopløsning, ingen netværksadgang fra parseren. Gælder well-formedness-, XSD- og regel-parsing.",
    "Størrelse: upload-grænse via MAX_UPLOAD_MB; lxml huge_tree bruges kontrolleret.",
    "Skema fra disk: XSD'er valideres fra lokale, versionerede filer (provenance m. sha256) — ikke fra netværket.",
  ]),

  H1("4. Applikationssikkerhed"),
  ...bullets([
    "Content-Security-Policy uden CDN'er (kun 'self'; ingen ekstern script/style), samt X-Content-Type-Options, X-Frame-Options (DENY), Referrer-Policy, Permissions-Policy og HSTS.",
    "Central login (balai_auth) på alle ruter undtagen sundhedstjek; per-tool-adgangstjek (slug 'pillar2'); CSRF-beskyttelse og databaseunderstøttet login-rate-limit.",
    "SECRET_KEY påkrævet i produktion (fejler hurtigt hvis ikke sat); delt på tværs af *.balai.dk for SSO.",
    "Ingen råt brugerinput i filstier (midlertidige filer via tempfile).",
  ]),

  H1("5. Trusselsmodel (resumé)"),
  table(["Trussel", "Modforanstaltning"], [
    ["XXE / XML-bomber", "resolve_entities=False, no_network, upload-grænse"],
    ["Skadelig upload", "Validering før behandling; kildefil slettes straks"],
    ["Uautoriseret adgang", "Central login + per-tool-adgangstjek; session m. 12t-grænse; rate-limit"],
    ["Datalækage til tredjepart", "Ingen eksterne kald under validering; statiske referencedata"],
    ["Forældet skema afviser gyldige filer", "Sync + provenance + selvtjek"],
    ["Clickjacking/MIME-sniffing/XSS", "Sikkerhedsheaders + stram CSP uden CDN'er"],
  ], [3400, 5960]),

  H1("6. Åbne punkter (til review)"),
  ...bullets([
    "Behandlingsgrundlag/DPA og dataplacering (EU) — jura/DPO. Den delte brugerdatabase (persondata) skal ligge i EU-region.",
    "Persistens/retention hvis historik tilføjes (env-styret, som SAF-T).",
    "Penetrationstest, SOC 2 / ISO 27001 — fra driftsplatformen.",
    "Logning/hændelseshåndtering — defineres med driftsplatformen.",
  ]),
]);

// ===========================================================================
// 4) HOSTING OG DRIFT
// ===========================================================================
const hosting = makeDoc([
  ...titleBlock("Hosting, drift og support", "Driftsgrundlag for godkendelse",
    "Udkast: nuværende drift er midlertidig (dev/demo). EY-platform er en forudsætning for produktionsbrug med klientdata."),

  H1("1. Nuværende drift vs. mål"),
  P("Værktøjet kører i dag på pillar2.balai.dk via Railway (kontinuerlig deploy fra privat GitHub-repo), som midlertidig dev-/demo-platform — på linje med de øvrige BALAI-værktøjer. Målet er en flytning til EY-godkendt infrastruktur (EU-dataplacering) før produktionsbrug med klientdata. Appen er platform-agnostisk (WSGI + Flask) og kan flyttes uden ændringer i kontrol-logikken."),

  H1("2. Migrationsplan til EY-platform"),
  ...numbered([
    "Aftal EY-godkendt driftsmiljø (EU-region) + databehandleraftale.",
    "Provisionér miljø: WSGI-app (gunicorn), miljøvariabler, og — hvis historik tilføjes — persistent lagring/DB.",
    "Flyt den centrale brugerstyrings PostgreSQL til EU-region (delt med de øvrige værktøjer).",
    "Verificér delt login (SECRET_KEY + SESSION_COOKIE_DOMAIN + AUTH_BASE_URL) og per-tool-adgang efter flytning.",
    "Kør valideringssuiten + enhedstests som accepttest i målmiljøet; flyt DNS.",
  ], "n4"),

  H1("3. Miljø- og konfigurationsinventar"),
  table(["Variabel", "Formål", "Note"], [
    ["SECRET_KEY", "Signerer session-cookie; delt SSO på *.balai.dk", "Påkrævet i prod; identisk på alle BALAI-værktøjer"],
    ["SESSION_COOKIE_DOMAIN", "Cookie-deling på tværs af subdomæner", "fx .balai.dk"],
    ["AUTH_BASE_URL", "Central login-/auth-tjeneste", "https://auth.balai.dk"],
    ["DATABASE_URL", "Delt brugerdatabase (entitlements)", "Samme delte Postgres som de øvrige værktøjer"],
    ["FLASK_ENV", "Miljø (production aktiverer sikre cookies + kræver SECRET_KEY)", "production"],
    ["MAX_UPLOAD_MB", "Upload-grænse", "Standard 200"],
  ], [2400, 4560, 2400]),

  H1("4. Backup, BCDR og overvågning"),
  ...bullets([
    "Kildefiler persisteres ikke (slettes straks), så der er ingen klientdata at sikkerhedskopiere i nuværende fase.",
    "Den delte brugerdatabase backes op på driftsplatformen (defineres ved EY-flytning).",
    "Genskabelse: appen er stateless (uden historik) og kan genudrulles fra git; mål-RTO/RPO fastlægges med EY-platformen.",
    "Overvågning/alarmering kobles til EY-platformens stack ved flytning.",
  ]),

  H1("5. CI og frigivelse"),
  ...bullets([
    "Tests og lint køres lokalt før push (pytest + valideringssuite + tools/sync_oecd_rules.py --check); Railway auto-deployer ved push.",
    "Runtime-afhængigheder er versionspinnede i requirements.txt; pip-audit kan køres på runtime-deps.",
    "Katalog, sporbarhedsmatrix, valideringsrapport og dokumentationspakke regenereres deterministisk via tools/-scripts.",
  ]),

  H1("6. Roller, support og åbne punkter"),
  ...bullets([
    "Rolle-/ansvarsbeskrivelse (drift, indholdsejer for regelkataloget, sikkerhed) fastlægges med EY.",
    "Support- og vedligeholdelsesmodel (SLA, opdatering af regler/skema ved OECD-ændringer) fastlægges.",
    "Penetrationstest, SOC 2 / ISO 27001 og DPA leveres fra driftsplatformen.",
  ]),
]);

// ---------------------------------------------------------------------------
const FILES = [
  ["Pillar2-Validator_Godkendelses-overblik.docx", overblik],
  ["Pillar2-Validator_Solution_Architecture.docx", arch],
  ["Pillar2-Validator_Sikkerhed_og_databehandling.docx", sec],
  ["Pillar2-Validator_Hosting_og_drift.docx", hosting],
];

fs.mkdirSync(DOCS, { recursive: true });
(async () => {
  for (const [name, doc] of FILES) {
    const buf = await Packer.toBuffer(doc);
    fs.writeFileSync(path.join(DOCS, name), buf);
    console.log("Skrev docs/" + name + " (" + buf.length + " bytes)");
  }
})();
