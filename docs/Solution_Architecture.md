# Løsnings- og arkitekturbeskrivelse — Pillar II GIR-Validator

**Version:** følger katalogversion i `validator/rules/P2-Validation-Rules.json`.
**Klassifikation:** Fortroligt — internt.
**Formål med dokumentet:** Beskrive løsningen til brug for intern EY tool-governance
og godkendelse. Komplementeres af `Godkendelses-overblik.md` (status/åbne punkter),
`Regel-sporbarhedsmatrix.md` (sporbarhed) og `Sikkerhed_og_databehandling.md`.

## 1. Formål og afgrænsning

Værktøjet **validerer en færdig GloBE Information Return (GIR)** mod OECD's
officielle XML-skema og de officielle valideringsregler, og rapporterer præcist
hvad der er galt, hvor (XPath/linje) og hvor alvorligt — på dansk. Det er et
**kontrol-/valideringslag**, ikke en beregnings- eller indberetningsmotor.

**Afgrænsning (bevidst):** Værktøjet beregner ikke top-up tax og indsender ikke.
Det tager en fil, andre har produceret, og auditerer den. Positionering bekræftet
ved benchmark mod PwC, KPMG og Deloitte, der alle spiller end-to-end (data →
beregning → filing) og ikke tilbyder et selvstændigt valideringslag.

## 2. Teknologistack

Python 3.13, Flask (web), lxml (streaming XML + XSD), pytest (testsuite). Samme
stack og konventioner som SAF-T-validatoren, så drift og governance kan genbruges.
Ingen tredjepartsafhængigheder i regelmotoren ud over lxml.

## 3. Arkitektur i korte træk

- **Data-drevet regelmotor.** Reglerne er data (JSON), ikke kode. Motoren
  (`validator/rules/oecd_rules.py` + `engine.py`) læser katalogerne og evaluerer.
  Ny/ændret regel = dataændring + test, ikke motorændring.
- **Skemaer som source of truth.** OECD's officielle XSD'er ligger i `schemas/`
  og valideres direkte imod (ikke en gengivelse). Holdes friske af
  `tools/sync_oecd_schemas.py`.
- **To regelkilder.** `oecd_validation_rules_catalogue.json` = hele den officielle
  regelliste (163, referencegrundlag). `oecd_validation_rules.json` = den
  eksekverbare delmængde motoren evaluerer i dag.
- **Findings-model.** Hvert fund: rule_id, lag (1-8), severity (5 niveauer),
  dansk besked + forslag, og en Location (linje/XPath/element). Samlet dom:
  afvist / betinget godkendt / godkendt.
- **Output.** Dansk HTML-rapport (og JSON via `?format=json`). OECD Status
  Message-XML som output-format er planlagt (Fase 6).

## 4. Dataflow

1. Bruger uploader en GIR-XML (fremtid: input fra dataudtræk-værktøjet via et
   kilde-agnostisk interface).
2. Filen gemmes midlertidigt, pipelinen kører (lag 1-8), kildefilen **slettes
   straks efter kørsel**.
3. Resultatet (EngineOutcome) renderes som rapport. Ingen klientdata persisteres
   i nuværende fase (historik/revisionslog kan tilføjes som i SAF-T).

## 5. Den 8-lags valideringsmodel

| Lag | Navn | Status |
|-----|------|--------|
| 1 | Skema & syntaks (well-formed + XSD mod GIR-skema) | **Aktiv** |
| 2 | Strukturel integritet (rod, MessageSpec, GLOBEBody, sektioner) | **Aktiv** |
| 3 | OECD-regler, file-level (nummererede) | **Aktiv** (delmængde) |
| 4 | OECD-regler, record-level (nummererede) | **Aktiv** (delmængde) |
| 5 | Guidance-afvigelser (juni 2026) | Delvist (switched-off respekteres) |
| 6 | GIR/QDMTT-kryds | Planlagt |
| 7 | Danske felt-regler | Planlagt (afventer afklaring) |
| 8 | Referenceintegritet | Delvist (ref_integrity-type findes) |

Lag 1-2 er blokerende (fejl her gør dybere lag meningsløse). Severity-modellen og
dommen er fælles med SAF-T (Kritisk/Væsentlig/Medium/Lav/Info).

## 6. Regelmotorens vokabular (check-typer)

Motoren kan i dag udtrykke følgende kontroltyper, der tilsammen dækker **alle
kategorier** i det officielle katalog (inkl. beregning):

`unique`, `required_if`, `forbidden_if`, `not_equal`, `mutually_exclusive`,
`conditional` (if/then med element + attributter, operatorer in/equals/contains/
absent…), `ref_integrity`, `conditional_ref` (betinget reference-integritet),
`format` (regex), `value_range`, `compare` (dato/tal-ordning), `cardinality`
(antalsbegrænsning) og **`calculation`** — en beregningsmotor der evaluerer
aritmetiske formler (subtract/sum/multiply/divide/sum_all, rekursivt) over GIR'ens
integer-felter og sammenligner beregnet mod rapporteret værdi. Beregningsmotoren
er aktiv for en delmængde af ETR-/top-up-reglerne; resten kodes batch-vis.

## 7. Referencedata og provenance

- **Skemaer:** OECD GIR XML Schema + Status Message Schema, udpakket i `schemas/`
  med `_provenance.json` (kilde-URL, sha256, dato). Manifest i
  `schemas/SCHEMA_SOURCES.md`.
- **Regler:** udtrukket fra OECD GIR Status Message User Guide (juli 2025) Part 4
  og guidance (juni 2026). Kilde-PDF'er i `docs/oecd_sources/`. Overblik i
  `OECD_regelgrundlag.md`.
- OECD opdaterer løbende skema og regler; en forældet lokal kopi kan afvise
  gyldige filer → sync-/selvtjek-mekanik som i SAF-T.

## 8. Sikkerhed og GDPR (resumé)

XXE slået fra (ingen entitetsopløsning/netværk i parseren), kildefil slettes
straks efter kørsel, sikkerhedsheaders i `app.py`, `SECRET_KEY` påkrævet i prod.
Uddybes i `Sikkerhed_og_databehandling.md`. GIR indeholder følsomme koncerntal →
samme eller strammere databehandling end SAF-T.

## 9. Kvalitetssikring

- Automatiseret testsuite (pytest) — pr. nuværende **58 tests**: katalogindlæsning,
  severity/dom, XSD-validering (valid + planted-invalid fixture), strukturkontroller,
  hver check-type, switched-off-respekt, app-endpoints.
- Lint af regelfilen (`tools/sync_oecd_rules.py --check`) — struktur + at hver
  XPath kompilerer; rapporterer dækning. CI-port: tests + lint.
- To **skemagyldige GIR-fixturer**: en minimal (`gir_valid.xml`) og en komplet
  golden-fixtur (`gir_valid_rich.xml`) med GeneralSection/CorporateStructure +
  JurisdictionSection/GLoBETax/ETR/OverallComputation. Begge bygget fra de
  faktiske skema-krav; golden-fixturen er fuldt godkendt og fungerer som
  regressions- og demo-facit (også end-to-end for beregningsmotoren).

## 10. Ændringsstyring

Ny/ændret kontrol → opdatér regel-JSON (+ bump `catalog_version`), tests,
`CHANGELOG.md` og sporbarhedsmatrix. Markdown-dokumenterne versioneres med koden.

## 11. Begrænsninger og åbne punkter

- Eksekverbar regeldækning er pr. nu en delmængde (se sporbarhedsmatrix);
  resten kodes batch-vis. Beregningsmotoren (`calculation`) er aktiv; de øvrige
  beregningsregler kodes løbende.
- Lag 6 (GIR/QDMTT) og lag 7 (danske felt-regler) er planlagte; danske
  udfyldningsregler skal verificeres mod Skattestyrelsen/DAC9.
- Persistens/historik/revisionslog og Status Message-output er planlagt (som i
  SAF-T-modellen).
- Hosting, penetrationstest, SOC 2/ISO og DPA følger EY-platformen (jf. SAF-T).

Se `Godkendelses-overblik.md` for status pr. område og næste skridt.
