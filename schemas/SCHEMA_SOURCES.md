# Skema-kilder (source of truth) — Pillar II GIR-validator

Dette er manifestet over de **officielle OECD-skemaer**, som valideringen kører
**direkte imod** — ikke mod en gengivelse. Samme princip som SAF-T-validatorens
`schemas/`-mappe (ERST-XSD som source of truth).

Skemaerne udpakkes i undermapperne her og holdes friske af
`tools/sync_oecd_schemas.py` (kør lokalt på din Mac — sandboxen må ikke hente
binære filer; se ARCHITECTURE.md §Trin 4.1). Læg **ikke** håndredigerede kopier
ind: kun det udpakkede, uændrede OECD-indhold.

## 1) GIR XML Schema (input vi validerer)

- **Rolle:** Definerer strukturen for selve GloBE Information Return. Vi validerer
  uploadede/genererede GIR-filer mod denne (pipeline-lag 1).
- **Landingsside:** https://www.oecd.org/en/publications/globe-information-return-pillar-two-xml-schema_c594935a-en.html
- **User Guide (PDF, jan. 2025):** https://www.oecd.org/content/dam/oecd/en/publications/reports/2025/01/globe-information-return-pillar-two-xml-schema_3980638f/c594935a-en.pdf
- **XML Schema (ZIP) — direkte:** https://www.oecd.org/content/dam/oecd/en/topics/policy-sub-issues/global-minimum-tax/globe-xsd.zip
- **Udpakkes til:** `schemas/gir/` (af `tools/sync_oecd_schemas.py`)
- **Version/dato ved seneste hentning:** _(udfyldes af sync-scriptet)_

## 2) GIR Status Message XML Schema (output-format til fejlrapportering)

- **Rolle:** Definerer den **strukturerede fejlrapportering** (file-level og
  record-level fejl) en kompetent myndighed sender retur. Vi bruger den som
  **output-format**: vores fund kan eksporteres som en OECD Status Message XML.
  Den valideres altså IKKE som input — den er målet for vores eksport.
- **Landingsside:** https://www.oecd.org/en/publications/globe-information-return-pillar-two-status-message-xml-schema_449e3cc3-en.html
- **User Guide (PDF, juli 2025):** https://www.oecd.org/content/dam/oecd/en/publications/reports/2025/07/globe-information-return-pillar-two-status-message-xml-schema_eb7bc5ca/449e3cc3-en.pdf
- **XML Schema (ZIP) — direkte:** https://www.oecd.org/content/dam/oecd/en/topics/policy-issues/tax-transparency-and-international-co-operation/xml-schema-gir-status-message.zip
- **Udpakkes til:** `schemas/status/` (af `tools/sync_oecd_schemas.py`)
- **Version/dato ved seneste hentning:** _(udfyldes af sync-scriptet)_

## 3) Guidance on the Use of the GIR XML Schema and Validation Rules (juni 2026)

- **Rolle:** Retter 14 kendte fejl i skema/valideringsregler for første
  filing-cyklus (substitut-elementer, AdditionalDataPoint, dummy-værdier,
  bounded percentages, og **ikke-anvendelse af visse valideringsregler**).
  Indlæses som referencedata til pipeline-lag 5 (`reference/guidance_deviations_2026-06.json`).
- **PDF:** https://www.oecd.org/content/dam/oecd/en/topics/policy-sub-issues/global-minimum-tax/guidance-on-the-use-of-globe-information-return-xml-schema-june-2026.pdf
- **Godkendt:** 3. juni 2026 (Inclusive Framework).

## 4) Tax Transparency Resource Centre (samleside)

- https://www.oecd.org/en/topics/sub-issues/international-standards-on-tax-transparency/tax-transparency-resource-centre.html
- Brug denne som indgang hvis ovenstående dybe links flyttes.

## Danske kilder (felt-regler, lag 7 — se ARCHITECTURE.md §Åbne danske krav)

- Skattestyrelsen GloBE: https://skat.dk/erhverv/selskaber-fonde-og-foreninger/selskaber-og-fonde/global-minimumsskat-for-store-koncerner-globe
- Den juridiske vejledning C.K.: https://info.skat.dk/data.aspx?oid=69326
- Minimumsbeskatningsloven (lov nr. 1535 af 12/12 2023); Rådets direktiv (EU) 2022/2523; DAC9.

---

**Bemærk om versionering:** OECD opdaterer løbende både skema og valideringsregler
(jf. juni-2026-guidance). Som i SAF-T-projektet skal en forældet lokal kopi kunne
afvise gyldige filer — derfor selvtjek via sync-script + månedlig GitHub Action.
