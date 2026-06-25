# Pillar II GIR-validator — arkitektur (forslag til review)

> **Status (pr. katalog 0.7.1):** Dette er det oprindelige design-dokument. Den
> besluttede arkitektur er nu **implementeret og kører**: lag 1-2 (XSD + struktur),
> lag 3-4 (data-drevet OECD-regelmotor med 13 check-typer inkl. beregningsmotor),
> 35/163 regler eksekverbare, komplet golden-fixtur, 58 tests grønne. De tre
> arkitekturvalg fra §8 er afklaret og fulgt. For **aktuel status** se
> `docs/Godkendelses-overblik.md`, `docs/CHANGELOG.md`, `docs/Regel-sporbarhedsmatrix.md`
> og `CLAUDE.md`. Officielle OECD-skemaer ligger i `schemas/` (well-formed, provenance/sha256).

## 0. Formål og positionering

Et web-værktøj der **validerer en færdig GloBE Information Return (GIR)** mod
OECD's officielle skema, OECD's nummererede valideringsregler, juni-2026-guidance
og danske felt-regler — og fortæller præcist hvad der er galt, hvor (XPath) og
hvor alvorligt. Samme produktfamilie og stil som SAF-T-validatoren (danske
rådgivere og økonomifunktioner), side om side med VAT/customs analytics,
VIES-validering og dataudtræk.

**Niche (bekræftet af benchmark mod PwC, KPMG, Deloitte):** De store spiller
end-to-end (data → beregning → GIR-produktion → filing) inde i egne platforme
(PwC Sightline/Beacon, KPMG KBAT/Digital Gateway, Deloitte Intela/Pillar Two
Agent). Ingen af dem sælger et **selvstændigt kontrol-/valideringslag**, der tager
en *færdig* GIR-fil — uanset hvem der har lavet den — og auditerer den. Det er
vores plads.

**Vigtig nuance fra benchmarken:** Nichen er ikke tom. Authority Software
("XML Authority") laver allerede *skema-niveau* validering af færdige GIR-filer,
og bredere vendors (Orbitax, Wolters Kluwer) genererer GIR-XML. Vores forsvarlige
kile er derfor **dyb semantisk regel-validering** — de nummererede OECD-regler +
juni-2026-afvigelser + **danske** felt-regler, med præcis "hvilken regel fejlede
og hvorfor" — ikke bare "filen matcher XSD". Det er nøjagtig samme styrke som
SAF-T-validatoren allerede har (XSD + nummererede, lagdelte forretningskontroller).

## 1. Fem ting Pillar II kræver ud over SAF-T

| # | Krav | Konsekvens for arkitekturen |
|---|------|------------------------------|
| 1 | **To skemaer**: GIR XML Schema + GIR Status Message XML Schema | GIR-skemaet er **input** vi validerer (lag 1). Status Message-skemaet er et **output-format** til struktureret fejlrapportering — ny byggesten (`validator/status_message/`). |
| 2 | **Nummererede OECD-regler** (file-level + record-level, fx 70028, 70092, 70106) | Nyt regel-lag oven på XSD. Reglerne katalogiseres som data (XPath-pointers, rule_type, scope), motoren læser dem — samme mønster som SAF-T's BAL-katalog. |
| 3 | **Guidance-afvigelser (juni 2026)** | Validatoren skal *kende* de 14 rettelser: anerkende foreskrevne workarounds som gyldige (fx `AdditionalDataPoint`), og **ikke** fyre regler OECD har slået fra. Eget lag (lag 5) + referencedata. |
| 4 | **GIR/QDMTT-krydsvalidering** | Afstem tal mellem GIR og QDMTT. Forbillede findes: SAF-T's `phase2/reconciliation.py` og `period_compare.py`. Nyt modul `validator/crosscheck/gir_qdmtt.py`. |
| 5 | **Input fra dataudtræk på sigt** | Input-interface skal abstrahere kilden, så en GIR kan komme fra manuel upload *eller* (senere) fra websitets dataudtræk-værktøj. `validator/input/sources.py`. |

## 2. Genbrug fra SAF-T (ingen gentænkning — kun udvidelse)

Disse byggesten kopieres stort set 1:1 og er produktets fundament:

- **Data-drevet regelkatalog** som single source of truth (`rules/*.json` →
  `catalog.py` → `build_finding()`-fabrik). Vi laver et nyt katalog, ikke en ny motor.
- **Streaming-regelmotor** (`engine_streaming.py`, lxml `iterparse`, bundet
  hukommelse, XXE slået fra). Én motor, der læser kataloget.
- **Finding-model**: `rule_id`, `layer`, `severity`, `message_da`,
  `suggested_fix_da`, `Location` (linje/**xpath**/element/element_id), `diff`.
  GIR-regler er XPath-baserede → `Location.xpath` passer perfekt (OECD's egne
  fejlrapporter peger netop med XPath + instance_id).
- **5-niveau severity** (Kritisk/Væsentlig/Medium/Lav/Info) + dom
  (afvist/betinget godkendt/godkendt) + materialitetsprofiler.
- **Caps + ucappede aggregater** (sande totaler bæres uafhængigt af findings-cap).
- **XSD som source of truth** i `schemas/`, holdt frisk af sync-script +
  månedlig GitHub Action med selvtjek.
- **Persistens**: SQLite (historik/revisionslog/eksport), kildefil slettes straks
  efter kørsel. Sikkerhedsheaders, `SECRET_KEY` i prod.
- **Uafhængig valideringssuite**: én planted defekt pr. regel + rapport.
- **Dokumentationspakke** i `docs/` (godkendelses-overblik, arkitektur,
  sporbarhedsmatrix), dansk tone.

## 3. Mappestruktur (forslag)

Selvstændigt repo `pillar2-validator/` ved siden af `saf-t-validator/`, samme
konventioner. (Alternativ: et delt internt bibliotek for `rules/`, `severity`,
`finding`, `presentation` — se §8.)

```
pillar2-validator/
├── app.py                       # Flask: ruter, upload, headers (mirror SAF-T)
├── CLAUDE.md                    # hand-off-note (oprettes når vi bygger)
├── ARCHITECTURE.md              # dette dokument
├── SECURITY.md
├── requirements.txt · Procfile · .python-version
│
├── schemas/                     # SOURCE OF TRUTH — officielle OECD-skemaer
│   ├── gir/                     # GIR XML Schema (udpakket ZIP)
│   ├── status/                  # GIR Status Message XML Schema (udpakket ZIP)
│   └── SCHEMA_SOURCES.md        # manifest: URLs, versioner, datoer  ✓ oprettet
│
├── reference/                   # synket referencedata (holdes frisk)
│   ├── oecd_validation_rules_YYYY-MM-DD.json   # nummererede regler (file/record)
│   ├── guidance_deviations_2026-06.json        # juni-2026-afvigelser
│   └── dk_field_rules.json                     # danske felt-regler (når afklaret)
│
├── validator/
│   ├── engine.py                # run_pipeline() + EngineOutcome (offentlig indgang)
│   ├── engine_streaming.py      # ENESTE regelmotor (lxml iterparse)
│   ├── xsd_validator.py         # lag 1: GIR-XSD (+ Status Message-XSD til output)
│   ├── rules/
│   │   ├── P2-Validation-Rules.json   # VORES katalog: lag, severity, danske tekster
│   │   ├── catalog.py · finding.py · severity.py · profiles.py   # genbrug fra SAF-T
│   │   ├── oecd_rules.py        # loader: OECD's nummererede regler → interne checks
│   │   └── guidance.py          # juni-2026-afvigelser (anerkend/undertryk)
│   ├── crosscheck/
│   │   ├── gir_qdmtt.py         # lag 6: GIR/QDMTT-afstemning (kilde-agnostisk)
│   │   └── qdmtt_source.py      # QDMTT-input: embedded | separat fil | dataudtræk
│   ├── status_message/
│   │   └── builder.py           # OUTPUT: byg OECD Status Message XML af fund
│   ├── input/
│   │   └── sources.py           # input-interface: upload | dataudtræk (fremtid)
│   ├── export/                  # pdf_executive, pdf_compact, audit_export (genbrug)
│   ├── presentation.py · report.py · conclusion.py · models.py · helpers.py · i18n.py
│   ├── runs_store.py · audit_log.py   # persistens (genbrug)
│
├── tools/
│   ├── sync_oecd_schemas.py     # hent+udpak GIR+Status ZIP → schemas/ (kør lokalt)
│   └── sync_oecd_rules.py       # hent nummererede valideringsregler → reference/
│
├── templates/ · static/         # dansk UI, samme stil som SAF-T
├── tests/                       # enhedstests (mirror SAF-T's testkultur)
├── validation/                  # uafhængig suite: én planted defekt pr. regel
└── docs/                        # godkendelses-pakke (dansk)
```

## 4. Valideringspipeline (lagdelt — mirror SAF-T's 8 lag)

Pipelinen er sekventiel og lagdelt som SAF-T. Lag 1-2 er "blokerende" (fejler de
hårdt, giver dybere lag ikke mening). Hvert fund er en `Finding` med dansk tekst,
severity og XPath-pointer.

| Lag | Navn | Indhold |
|-----|------|---------|
| **1** | **Skema & syntaks** | Well-formed XML + validering mod **GIR XSD** (`schemas/gir/`). Direkte mod det officielle skema, ikke en fortolkning. Kritiske fund. |
| **2** | **Strukturel integritet** | Obligatoriske sektioner findes: `MessageSpec`, `GLOBEBody` (FilingConstituentEntity, GeneralSection, Summary, JurisdictionSection, evt. UTPRAttribution). `MessageTypeIndic`-værdi, `DocTypeIndic`/`DocRefId`-tilstedeværelse. |
| **3** | **OECD-regler — file-level** | Nummererede regler der gælder filen som helhed (fx dublet-`DocRefId`, MessageSpec-konsistens). Indlæst fra `reference/oecd_validation_rules_*.json`. |
| **4** | **OECD-regler — record-level** | Nummererede regler pr. post med XPath-pointer (fx 70106: `OtherTIN` ≠ `TIN`; required_if; not_equal; bounded values). Rule_type + scope (fx `same_container_instance`) bæres med i kataloget. |
| **5** | **Guidance-afvigelser (juni 2026)** | (a) Anerkend foreskrevne workarounds som **gyldige** (Recast/Art. 7.1.2 via GIR1910 + `AdditionalDataPoint` "ADT1 Basis"; Equity Investment Inclusion Election → "ADT2 EquityGain"; Unclaimed Accrual → AdditionalDataPoint). (b) **Undertryk** regler OECD har slået fra, så vi ikke fejler korrekt udfyldte filer. (c) Tjek bounded/dummy-værdier hvor foreskrevet. |
| **6** | **GIR/QDMTT-kryds** | Afstem top-up tax og jurisdiktionstal mellem GIR og QDMTT mod en **normaliseret QDMTT-model** (kilde-agnostisk — se §8.1). Uoverensstemmelser flagges (severity dynamisk på materialitet). Springes over m. tydelig besked hvis ingen QDMTT-kilde. Forbillede: SAF-T `reconciliation.py`. |
| **7** | **Danske felt-regler** | DK-specifikke krav: `MessageTypeIndic`/korrektionshåndtering, CVR/TIN-format, indsendelseskanal, sprog/valuta. **Mange punkter uafklarede — se §7.** Datadrevet via `reference/dk_field_rules.json`. |
| **8** | **Referenceintegritet** | Konsistens på tværs: `DocRefId` unik, `CorrDocRefId` peger på eksisterende post, ConstituentEntity-referencer, ISO-jurisdiktions-/valutakoder, enum-værdier. |

**Severity-mapping:** OECD's file-level fejl → typisk Kritisk (afvisning);
record-level → Væsentlig/Medium afhængig af regel; guidance/danske → pr. regel.
Mapping fastlægges i `P2-Validation-Rules.json` som i SAF-T.

**Output:** `EngineOutcome` (uændret form: findings, lag kørt, dom, counts,
aggregater) → dansk rapport (HTML/PDF) **og** valgfrit en **OECD Status Message
XML** (lag-1/2-fejl som file-level, regel-fund som record-level), bygget af
`status_message/builder.py`. Det gør værktøjet interoperabelt: vores fund kan
afleveres i OECD's eget fejlformat.

## 5. Input-interface (manuel upload + fremtidigt dataudtræk)

Kilden abstraheres bag ét lille interface, så motoren er ligeglad med hvor GIR'en
kommer fra. Motoren arbejder altid på en **GIR XML-strøm** (eller en sti).

```
validator/input/sources.py

class InputSource(Protocol):
    def open_xml(self) -> BinaryIO: ...      # returnér en GIR XML-strøm
    def descriptor(self) -> dict: ...        # metadata: kilde, navn, periode, CVR

class UploadedFileSource(InputSource):       # NU: manuel upload (app.py)
class DataExtractSource(InputSource):        # SENERE: websitets dataudtræk-værktøj
```

- **Nu:** `UploadedFileSource` — brugeren uploader en `.xml` GIR-fil.
- **Senere:** `DataExtractSource` — dataudtræk-værktøjet leverer enten en færdig
  GIR-XML eller et normaliseret mellemformat, som en tynd adapter renderer til
  GIR-XML, før motoren kører. **Kontrakt:** dataudtræk skal producere en strøm,
  der opfylder GIR-skemaet; al validering forbliver ét sted (motoren). Integration
  bygges ikke nu, men interfacet reserverer pladsen, så det ikke kræver
  omskrivning senere.

## 6. Hvordan det matcher SAF-T-konventionerne

- **Regler som data:** `P2-Validation-Rules.json` med `catalog_version`,
  lag-definitioner, severity-niveauer, materialitetsprofiler, danske
  besked-/fix-skabeloner — samme skema som `BALAI-Validation-Rules.json`.
- **Sporbarhed:** hver regel → autoritativ kilde (OECD-regelnummer/guidance/dansk
  hjemmel), modul, testdækning (sporbarhedsmatrix i `docs/`).
- **CI-port:** ny/ændret regel → opdatér katalog (+bump version), tests,
  CHANGELOG, sporbarhedsmatrix og valideringssuite — præcis SAF-T-disciplinen.
- **Drift:** sync-script + GitHub Action holder skema og regler friske (OECD
  opdaterer løbende; en forældet kopi kan afvise gyldige filer).
- **Sikkerhed/GDPR:** XXE fra, kildefil slettes efter kørsel, retention
  env-styret, headers i `app.py`. GIR indeholder følsomme koncerntal → samme
  eller strammere databehandling end SAF-T.

### 6.1 Trin 4.1 — skema-download (status og plan)

Sandboxen må ikke hente binære filer (ingen curl/wget/programmatisk download).
OECD lægger skemaerne som ZIP bag en JS-download-knap, så de kan ikke trækkes ind
herfra. Leveret nu: scaffold (`schemas/gir/`, `schemas/status/`) + manifest
(`schemas/SCHEMA_SOURCES.md`) med præcise officielle URLs. **Faktisk hentning** sker
via `tools/sync_oecd_schemas.py`, som *du* kører lokalt (samme model som
`sync_erst_reference.py`, hvor du kører og committer). Scriptet bygges i Fase 0.

## 7. Åbne danske felt-specifikke krav (skal verificeres)

Det er **uafklaret**, om Skattestyrelsen publicerer danske udfyldnings-/skemaregler
ud over OECD's. Følgende skal verificeres mod skat.dk (GloBE), Den juridiske
vejledning C.K., minimumsbeskatningsloven og DAC9 — **før lag 7 kodes**:

1. **Eget dansk skema/extension?** Bruger DK OECD-skemaet rent, eller med danske
   felter/wrapper (jf. NL, der har eget skema)? Afgør om `schemas/` skal rumme en
   dansk variant.
2. **`MessageTypeIndic`:** Tilladte værdier i DK (OECD: "GIR"). Findes der danske
   krav til notifikation vs. fuld GIR?
3. **Korrektionshåndtering:** `DocTypeIndic` (ny/korrektion/sletning),
   `CorrMessageRefId`/`CorrDocRefId`-krav ved rettelser — danske regler og
   rækkefølge. Hvordan korrigeres en `AdditionalDataPoint`-workaround dansk?
4. **Indsendelseskanal/-format:** TastSelv/portal, encoding, filstørrelse, evt.
   transport-wrapper, signering.
5. **Frister:** Første GIR (transition: 30/6 2026?) og notifikationsfrister i DK.
6. **Central vs. lokal indsendelse + DAC9-udveksling:** Skal DK-koncerner indsende
   lokalt, og hvilke felter udveksles via DAC9? Påvirker hvilke sektioner vi
   kræver.
7. **Sprog, valuta, afrunding:** Krav til fritekst, præsentationsvaluta og
   afrunding i danske indberetninger.
8. **Materialitet/severity for danske formål:** Profiler (revisor vs. egen
   kontrol) som i SAF-T — skal de danske tærskler kalibreres?

**Næste skridt:** Læs skat.dk + C.K. + DAC9-implementering, og bekræft med en
dansk Pillar II-kilde/Skattestyrelsen. Indtil afklaret kodes lag 7 minimalt
(kun det OECD-garanterede), og åbne punkter spores i `docs/` som i SAF-T.

## 8. Afklarede arkitekturvalg (besluttet)

- **Selvstændigt repo med kopieret kerne — konsolidér senere.** Vi starter som eget
  `pillar2-validator/`-repo med kernen (`rules/`, `severity`, `finding`,
  `profiles`, `presentation`, persistens) kopieret fra SAF-T. Når mønstret er
  stabilt på tværs af begge værktøjer, udtrækkes den fælles kerne til et delt
  internt bibliotek. **Konsekvens:** hold kopierede kerne-moduler så uændrede som
  muligt (kun navne/tekster afviger), så et senere udtræk bliver mekanisk, ikke en
  refaktorering.
- **Status Message-output: tidligt, men separat lag (Fase 6).** Kernen leverer
  værdi (lag 1-5) før, og `status_message/builder.py` bygges som et isoleret
  output-lag uden at gribe ind i motoren.
- **QDMTT-input: kilde-agnostisk (kan tage højde for alle tre veje).** Da det er
  uafklaret, om QDMTT-tallene kommer som separat fil, som sektion i selve GIR'en,
  eller fra dataudtræk, abstraherer vi kilden bag samme mønster som
  input-interfacet — se §8.1. Crosscheck-modulet er ligeglad med oprindelsen.

### 8.1 Kilde-agnostisk QDMTT-input

`crosscheck/gir_qdmtt.py` afstemmer mod en **normaliseret** QDMTT-model, ikke mod
en bestemt filtype. Én resolver-kontrakt, tre implementeringer (mere kan tilføjes):

```
validator/crosscheck/qdmtt_source.py

class QdmttFigures:                      # normaliseret facit: pr. jurisdiktion
    by_jurisdiction: dict[str, JurisdictionQdmtt]   # top-up tax, ETR, covered tax …
    origin: str                          # "embedded" | "separate_file" | "dataextract"

class QdmttSource(Protocol):
    def figures(self) -> QdmttFigures: ...
    def available(self) -> bool: ...     # er der overhovedet QDMTT-data ad denne vej?

class EmbeddedGirQdmtt(QdmttSource):     # QDMTT-tal læst ud af GIR'ens egen JurisdictionSection
class SeparateFileQdmtt(QdmttSource):    # separat uploadet QDMTT-fil (XML/normaliseret)
class DataExtractQdmtt(QdmttSource):     # SENERE: fra websitets dataudtræk-værktøj
```

**Resolutions-rækkefølge (konfigurerbar):** brug en eksplicit separat
QDMTT-kilde hvis givet; ellers udtræk de indlejrede tal fra GIR'en; ellers
spring lag 6 over og rapportér *"ingen QDMTT-kilde tilgængelig — krydsvalidering
ikke udført"* (i stedet for en falsk grøn dom). Den anvendte kilde (`origin`)
vises altid i rapporten, så det er sporbart hvad der blev afstemt mod hvad.

Dermed kan lag 6 leveres nu mod den indlejrede vej, og separat-fil/dataudtræk
tilkobles uden at røre selve afstemningslogikken.

## 9. Faseinddelt opbygningsplan

> Hver fase er selvstændigt leverbar og afsluttes med tests + opdateret
> sporbarhed, som i SAF-T. CI-porten (tests + valideringssuite) gælder fra Fase 1.

**Fase 0 — Fundament & skemaer.**
Repo-scaffold; kopiér kerne fra SAF-T (`rules/`, `finding`, `severity`,
`profiles`, `presentation`, persistens, sikkerhedsheaders). Byg
`tools/sync_oecd_schemas.py` + `sync_oecd_rules.py`. Du kører dem lokalt og
committer GIR+Status-XSD til `schemas/`. Tomt `P2-Validation-Rules.json`-skelet.

**Fase 1 — Skema-MVP (lag 1-2).**
GIR-XSD-validering + strukturkontrol, upload-UI, `EngineOutcome`, dansk
HTML-rapport + dom. Leverbar værdi: *"overholder filen GIR-skemaet og har den de
obligatoriske sektioner?"* Uafhængig valideringssuite startes.

**Fase 2 — OECD-regler (lag 3-4).**
Katalogisér de nummererede file-/record-level regler i `reference/` +
`P2-Validation-Rules.json`. XPath-pointers i `Location`. Dette er kerne-IP'en.

**Fase 3 — Guidance-afvigelser (lag 5).**
`reference/guidance_deviations_2026-06.json` + `guidance.py`: anerkend workarounds,
undertryk afslåede regler, tjek bounded/dummy-værdier.

**Fase 4 — GIR/QDMTT-kryds (lag 6).**
`crosscheck/gir_qdmtt.py` afstemmer tal; dynamisk severity på materialitet.

**Fase 5 — Danske felt-regler (lag 7-8).**
Efter §7-afklaring: `dk_field_rules.json` + referenceintegritet. Materialitets-
profiler kalibreres til danske formål.

**Fase 6 — Status Message-output.**
`status_message/builder.py`: eksportér fund som OECD GIR Status Message XML
(file-level + record-level), valideret mod `schemas/status/`.

**Fase 7 — Dataudtræk-input.**
Implementér `DataExtractSource` mod websitets dataudtræk-værktøj.

**Tværgående hele vejen:** enhedstests, uafhængig valideringssuite (én planted
defekt pr. regel), dansk dokumentationspakke i `docs/`, sikkerheds-/GDPR-review,
sync-GitHub Action med selvtjek.
