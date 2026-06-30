# Ændringslog — Pillar II GIR-Validator

Versionering følger regelkataloget (`validator/rules/P2-Validation-Rules.json`,
`catalog_version`). Dokumenterne versioneres sammen med koden.

## 0.18.0 — 2026-06-30

**CEComputation-conditionals + TIN-ulighed.**

- Dækning 87 → **92 regler** (+5): 70027 (GIR318 → 0% ejerskab, NOTIN-TIN,
  GIR806), 70058 (InvestmentEntityTIN ≠ CEComputation-TIN), 70106 (OtherTIN ≠
  CEComputation-TIN), 70116 (AdjustmentItem GIR2025 → IntShippingIncome i
  CEComputation), 70117 (AdjustmentItem GIR2024 → Art7.6 i CEComputation).
- Kandidater 51 → 46. Valideringssuite **92/92**, golden-GIR ren. Pakke regenereret.

## 0.17.0 — 2026-06-30

**Regel-triage: ærligt dækningsbillede (scope-klassifikation).**

- Alle 163 katalogregler er klassificeret med et `scope`-felt: **87 eksekverbare**,
  **5 dækket af ækvivalent regel** (70063/70080/70119/70121 → 70059; 70069 → 70067),
  **51 kandidater**, **16 uden for scope** (transmissions-/modtagerstatus 50001-50011,
  kryds-besked-/korrektionshistorik 60002/60008/60009/60014, eksternt TIN-register
  70004) og **4 slået fra** (2026-guidance). Hver markering har en begrundelse.
- `coverage()` eksponerer nu scope-fordeling: fil-validerbare = 143 (katalog − 4
  switched-off − 16 out-of-scope); **effektivt dækket = 92/143 ≈ 64 %**.
- Sporbarhedsmatrixen har ny fane "Dækningsoverblik" + scope-kolonner i "Fuldt
  katalog". Godkendelses-overblik-docx har nyt afsnit 4 "Regeldækning (ærligt
  billede)". Docx-nøgletal beregnes nu fra kataloget (ingen hardkodede tal → ingen drift).

## 0.16.0 — 2026-06-30

**Motor-udvidelse: dato-aware conditional + relativ år-grænse → 5 nye regler.**

- `conditional`-operatorerne kan nu coerce'e til dato/år (`as`), sammenligne mod
  et andet elements værdi (`ref`) og lægge en `offset` til år-/tal-grænsen (fx
  `End.year − 4`). Tilføjet `eq`/`ne`. Bagudkompatibelt.
- Dækning 82 → **87 regler** (+5): 70038/70039 (SafeHarbour-udløbsdatoer
  30/06/2028 og 31/12/2026), 70071 (Recapture-år inden for rapporteringsåret +
  3 foregående), 70094 (Articles GIR2605 → år ≥ 4 før periodeslut), 70095
  (Articles GIR2602 → femte år før periodeslut).
- Defekt-synthesizeren håndterer nu `as`/`ref`/`offset`. Valideringssuite
  **87/87**, golden-GIR ren. Governance-pakken regenereret.

## 0.15.0 — 2026-06-30

**Flere beregningsregler (substans, Art4.1.5, IIR-inklusionsratio).**

- Dækning 78 → **82 regler** (+4): 70087 (SubstanceExclusion/Total = PayrollCost×
  PayrollMarkUp + TangibleAssetValue×TangibleAssetMarkup), 70091
  (ExpectedAdjustedCoveredTax = GlobeLoss × 15 %), 70097 (InclusionRatio =
  (NetGlobeIncome − OtherOwnershipAllocation) / NetGlobeIncome), 70098
  (TopUpTaxShare = TopUpTax × InclusionRatio).
- Valideringssuiten dækker nu **82/82** (defekt-synthesizer bruger 1-fyld, så
  divide-formler ikke rammer nul-nævner). Golden-GIR forbliver ren.
- Governance-pakken (docx + sporbarhedsmatrix + valideringsrapport) regenereret.

## Drift, login & governance — 2026-06-30 (katalog 0.14.0)

**Central login, BALAI-UI, uafhængig valideringssuite og godkendelsespakke.**

- **Central brugerstyring:** koblet på den fælles `balai_auth` (slug `pillar2`).
  Delt SSO på `*.balai.dk`, per-tool-adgang, gatede ruter (`/`, `/valider`),
  CSRF + login-rate-limit. Registreret i det centrale tool-register på auth.balai.dk.
  Deployet på `pillar2.balai.dk` (Railway).
- **UI:** BALAI-skal (blåt B, top-bar med bruger/log-ud, header, footer) på linje
  med SAF-T. Forsidens regeltælling viser nu korrekt "8 strukturregler + 78
  OECD-kontroller". CSP strammet (Tailwind-CDN fjernet, kun lokal `style.css`).
- **Uafhængig valideringssuite (`validation/`):** planter ÉN målrettet defekt pr.
  eksekverbar OECD-kontrol og bekræfter, at netop den fyrer — golden-GIR forbliver
  ren. **78/78 består**; gated i CI (`python -m validation.run_validation`).
- **Godkendelses-/dokumentationspakke** (`docs/`, samme ramme som SAF-T): 4 docx
  (Godkendelses-overblik, Solution_Architecture, Sikkerhed_og_databehandling,
  Hosting_og_drift), sporbarhedsmatrix.xlsx (4 faner) og auto-genereret
  valideringsrapport. Generatorer: `tools/build_approval_docs.js`,
  `tools/build_traceability.py`. Auth markeret **Dækket**.
- Testsuite 73 → **74** (login-gating + valideringssuite-port).

## 0.14.0 — 2026-06-25

**År-mod-periode-sammenligninger + kryds-CE-eksistens.**

- Dækning 72 → **78 regler** (+6): 70066/70068 (DeferTaxAsset-/CoveredTaxRefund-år
  ≤ periodens startår), 70070 (Recapture-år ≤ periodens slutår), 70093
  (NONArt4.1.5-år ≤ periodens slutår), 70015 (GIR308 kræver en modsvarende GIR307),
  70019 (GIR305 kræver en modsvarende GIR306).
- Bruger `compare as:"year"` mod Period/Start og Period/End samt dokument-scopet
  `conditional` (eksistens af modsvarende CE).
- Alle verificeret i bulk (korrekt + plantet-forkert + golden ren).

## 0.13.0 — 2026-06-25

**Ny check-type `unique_in` + blandet conditional/calc/value_range-batch.**

- Ny container-scopet unikhedskontrol `unique_in` (14. check-type): en værdi må
  kun optræde én gang inden for hver beholder.
- Dækning 67 → **72 regler** (+5): 70059 (AdjustmentItem-kode unik pr. ETR),
  70067 (AmountAttributed-år unikke), 70090 (GlobeLoss = NetGlobeIncome/Total),
  70124 (CrossAllocation/Reductions ≤ 0), 70021 (GlobeStatus GIR316/318 →
  OwnershipChange påkrævet).
- Alle verificeret i bulk (korrekt + plantet-forkert + golden ren).

## 0.12.0 — 2026-06-25

**Flere beregningsregler + formel-udvidelser.**

- Formel-motoren har nu litteral-konstanter (fx × 0,15) og år-udtræk (`as:"year"`)
  til compare; nested `sum_all` og `local-name()`-paths til prikkede/hyphenerede navne.
- Dækning 63 → **67 regler** (14 beregningsregler): 60028 (AdjustedFANIL/Total),
  70074 (TotalDDT), 70077 (Recast-Total), 70055 (OutstandingBalance).
- Alle verificeret i bulk (korrekt + plantet-forkert + golden ren).

## 0.11.0 — 2026-06-25

**Numeriske operatorer + GlobeStatus/UTPR/AdjustmentItem-batch.**

- Motoren har nu numeriske operatorer i conditional (`lt/gt/le/ge`) og kan
  adressere prikkede/hyphenerede element-navne via `local-name()` (fx Art4.1.5).
- Dækning 54 → **63 regler** (+9): 70016/70017 (GlobeStatus co-krav), 70026
  (GIR305 → 100% ejerskab), 70062 (AdjustmentItem → ikke-negativ), 70088 (negativ
  NetGlobeIncome → Art4.1.5), 70101/70102/70103 (UTPR-betingelser), 70115 (UPEAdjustments).
- Alle verificeret i bulk (positiv + negativ + golden ren).

## 0.10.0 — 2026-06-25

**SafeHarbour-batch.**

- Dækning 48 → **54 regler**: 70045 (Transitional CbCR SH), 70047 (Revenue),
  70048 (IncomeTax), 70049 (UTPRSafeHarbour), 70051 (AggregateSimplified) — alle
  betinget af SafeHarbour-værdien (GIR12xx er selvscopende) — samt 70041
  (CFSofUPE GIR502/504 udelukker SafeHarbour GIR1207-1209).
- Alle verificeret i bulk. Bemærk: container `.` rammer rod-elementet (descendant-
  søgning `.//GLOBE_OECD` gør ikke). Hyphenerede element-navne (Non-MaterialCE)
  udskudt pga. XPath-parsing.

## 0.9.0 — 2026-06-25

**Stor conditional-batch (Basis/AdjustmentItem/Exception).**

- Dækning 39 → **48 regler** (+9 i én verificeret batch): 70108-70113 (Basis-
  betingede ejer-felter), 70060 (AdjustmentItem GIR2025 → IntShippingIncome),
  70107 (Exception=TRUE udelukker CrossBorderAdjustments), 70082 (DeferredTaxAssets
  → Start/Recast = 0).
- Alle verificeret i bulk med positiv + negativ case + golden-fixtur ren.
  Selvscopende `when`-betingelser (Basis GIR19xx) gør brede containere sikre.

## 0.8.0 — 2026-06-25

**Flere beregningsregler + doc-sync-automatisering.**

- Dækning 35 → **39 regler**: 70078 (BefRecastAdjust), 70079 (PreRecast),
  70064 (DeferTaxAsset/Total), 70065 (CoveredTaxRefund/Total) — alle beregningsregler,
  verificeret med korrekt + plantet-forkert case + golden-fixtur ren.
- Nyt værktøj `tools/update_docs.py`: regenererer de data-drevne docs
  (sporbarhedsmatrix, regelgrundlag) og opdaterer nøgletal i prosa-docs via
  STATS-markører. Kører som fast del af hver batch-afslutning, så dokumentationen
  ikke kan drive. 59 tests grønne.

## 0.7.1 — 2026-06-25

**Populeret ETR-fixtur + end-to-end beregningstest.**

- Golden-fixturen har nu en fuldt populeret JurisdictionSection/GLoBETax/ETR/
  ETRComputation/OverallComputation (FANIL, NetGlobeIncome, ETRRate,
  ExcessProfits, ExcessNegTaxExpense m.fl.) — XSD-gyldig og fuldt godkendt
  (alle tal internt konsistente).
- Beregningsmotoren verificeres nu også **end-to-end**: en test planter én forkert
  Remaining-værdi i den ellers gyldige fil, og 70083 fyrer gennem hele pipelinen
  (XSD ok, dom afvist). 58 tests grønne.

## 0.7.0 — 2026-06-25

**Beregningsmotor (calculation-check-type).**

- Ny check-type `calculation`: evaluerer en aritmetisk formel (operatorer subtract,
  sum, multiply, divide, sum_all; rekursive/indlejrede formler) over GIR'ens
  integer-felter og sammenligner beregnet mod rapporteret værdi. Springer over hvis
  felter mangler (ingen falsk positiv).
- Dækning 29 → **35 regler** med 6 beregningsregler: 70086 (ExcessProfits),
  70072 (EndAmount), 70083 (Remaining), 70105 (UTPRCarriedForward), 60027
  (IIR TopUpTax), 70076 (TransBlendCFC sum).
- Respekterer fortsat switched-off (60025/60026/70092 fyres aldrig).
- Alle verificeret med korrekt + plantet-forkert case + golden-fixtur ren. 57 tests grønne.

## 0.6.1 — 2026-06-25

**Komplet golden-fixtur (JurisdictionSection + GLoBETax).**

- Den righoldige fixture er nu strukturelt komplet: GeneralSection +
  CorporateStructure + JurisdictionSection med GLoBETax. XSD-gyldig og **fuldt
  godkendt** (ingen fund) — golden-fixtur for hele den aktive regelmængde.
- Fundament klar til beregningsmotoren: GLoBETax/ETR-rod findes; den populerede
  ETR/OverallComputation-struktur bygges sammen med beregningsmotor-check-typen
  (tæt koblet). 54 tests grønne.

## 0.6.0 — 2026-06-25

**Ownership-batch + conditional_ref-type.**

- Dækning 26 → **29 regler**: 70025 (nominee-PreOwnership kræver NOTIN), 70029/70030
  (Ownership-TIN skal matche en rapporteret enheds-TIN — ny `conditional_ref`-type:
  betinget reference-integritet dokument-bredt).
- Alle verificeret med negativ test + mod den righoldige fixture (Ownership/TIN
  matcher en rapporteret TIN → ingen falsk positiv).
- 54 tests grønne.

## 0.5.0 — 2026-06-25

**CorporateStructure-batch + ægte righoldig fixture (check-type cardinality).**

- Eksekverbar dækning 21 → **26 regler**: 70009 (ugyldig UPE-GlobeStatus),
  70010/70011 (kun ét ResCountryCode — ny `cardinality`-type), 70024
  (PreOwnership ved GIR719), 70032 (QIIR kræver Rules GIR201/202).
- **Righoldig fixture nu ægte:** komplet GeneralSection + CorporateStructure
  (UPE, CE, Ownership, TIN, GlobeStatus, Rules), XSD-gyldig, bekræftet ren — og en
  ny test sikrer at strukturen faktisk er til stede (værn mod tom fixture).
- Læringer fanget ved verifikation: (1) tidligere string-baseret fixture-indsætning
  fejlede stille; (2) `OwnershipPercentage` er en fraktion 0-1 (50% = 0.5), ikke 0-100.
- JurisdictionSection udskudt (kræver dyb påkrævet ETR-struktur). 52 tests grønne.

## 0.4.1 — 2026-06-25

**Righoldig fixture + vigtig regel-bugfix.**

- **Bugfix:** reglerne 70013/70014/70018 brugte element-navnet `GloBEStatus`, men
  skemaet hedder `GlobeStatus` — de ville aldrig have fyret på rigtige data. Rettet
  og verificeret. (Fundet netop ved at bygge den righoldige fixture.)
- Ny righoldig, fuldt skemagyldig fixture `tests/fixtures/gir_valid_rich.xml`
  (GeneralSection + CorporateStructure: UPE, CE, Ownership, TIN, GlobeStatus, Rules)
  — bekræftet ren (ingen XSD-fejl, ingen OECD-falske-positiver). Regressionsfacit
  for de dybe JurisdictionSection-/CorporateStructure-regler.
- 47 tests grønne.

## 0.4.0 — 2026-06-25

**Regel-batch 2 + bugfix.**

- Eksekverbar dækning 17 → **21 regler**: 70044 (ETRStatus skal have ETRException/
  ETRComputation), 70073/70104/70123 (ikke-negative beløb).
- Bugfix: `present`/`absent`-operatoren tjekker nu elementeksistens (tomme
  elementer tæller korrekt som til stede).
- 46 tests grønne. Bemærk: de resterende dybe JurisdictionSection-regler kræver
  en righoldigere valid-fixture for sikker verifikation (næste skridt).

## 0.3.0 — 2026-06-25

**Stor regel-batch + dato/krydssektions-checks.**

- Eksekverbar regeldækning udvidet fra 8 til **17 regler** (alle med bekræftet
  OECD-nummer): tilføjet 60021, 60023, 70003, 70005, 70013, 70014, 70018, 70022,
  70023 — TIN-attributregler, GloBEStatus-udelukkelser og dato-/krydssektions-
  sammenligninger.
- Hver ny regel verificeret med en test der bekræfter at den fyrer; valid-fixturen
  beriget (issuedBy) og bekræftet ren (ingen falske positiver).
- 43 tests grønne.

## 0.2.0 — 2026-06-25

**Fuldt OECD-regelgrundlag + udbygget motorvokabular.**

- Udtrak hele den officielle regelliste (**163 regler**) fra OECD GIR Status
  Message User Guide (juli 2025) Part 4 → `reference/oecd_validation_rules_catalogue.json`,
  med fulde XPaths, level, `switched_off_2026`-flag og klassificering pr. check-type.
- Udtrak de **14 guidance-issues** (juni 2026) → `reference/guidance_deviations_2026-06.json`.
- Regelmotoren respekterer nu **switched-off**-regler (60025, 60026, 70092, 70028).
- Check-type-vokabular udvidet til **10 typer** — dækker alle ikke-beregnings-
  kategorier: tilføjet `conditional`, `ref_integrity`, `format`, `value_range`,
  `compare`, `mutually_exclusive`.
- **8 eksekverbare regler** med bekræftede OECD-numre: 60004, 60006, 60007, 60012,
  60015, 60020, 70001, 70002.
- Etableret EY-governance-dokumentationspakke i `docs/`.
- 39 tests grønne; lint-værktøj rapporterer dækning (8/163).

## 0.1.0 — 2026-06-25

**Fase 0-1 + regelmotor-skelet.**

- Fase 0: repo-scaffold, kerne kopieret fra SAF-T (severity/finding/profiles/
  katalog), Flask-app, smoke-tests.
- Officielle OECD GIR- + Status Message-XSD'er hentet til `schemas/` m. provenance.
- Fase 1: lag 1 (well-formed + XSD-validering), lag 2 (strukturkontroller +
  CompanyContext), dansk HTML-rapport.
- Regelmotor (lag 3-4) med data-drevet katalog + check-typer unique/required_if/
  forbidden_if/not_equal; `tools/sync_oecd_rules.py`.
