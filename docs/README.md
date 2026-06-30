# Dokumentation — Pillar II GIR-Validator

Denne mappe indeholder produkt-/værktøjsdokumentationen for Pillar II
GIR-Validator. Dokumenterne versioneres bevidst **sammen med koden**, så de
altid matcher den version af produktet, de beskriver (samme commit, samme
git-historik). Rammen er identisk med SAF-T-validatorens pakke.

## Indhold (officiel pakke)

| Fil | Indhold |
|-----|---------|
| `Pillar2-Validator_Godkendelses-overblik.docx` | **Start her.** Forside- og statusdokument: samler hele pakken, viser godkendelsesparathed pr. område (Dækket/Udkast/Åbent) og lister de åbne punkter med næste skridt. Tag dette med til EY's tool-governance. |
| `Pillar2-Validator_Solution_Architecture.docx` | Løsnings- og arkitekturbeskrivelse: formål, afgrænsning, arkitektur, dataflow, den 8-lags valideringsmodel, regelmotorens vokabular, referencedata, central brugerstyring, kvalitetssikring, ændringsstyring, begrænsninger og åbne punkter. |
| `Pillar2-Validator_Regel-sporbarhedsmatrix.xlsx` | Sporbarhedsmatrix: hver eksekverbar OECD-kontrol mappet til autoritativ kilde, implementering (modul) og valideringsscenarie. Plus faner for det fulde katalog (163 regler), referencedata-provenance og severity/materialitetsprofiler. |
| `Pillar2-Validator_Sikkerhed_og_databehandling.docx` | Sikkerheds- og databehandlingsbeskrivelse: datakategorier, dataflow, inputhærdning, applikationssikkerhed, trusselsmodel, GDPR og åbne punkter. (Udkast — skal review'es af jura/databeskyttelse og sikkerhed.) |
| `Pillar2-Validator_Hosting_og_drift.docx` | Hosting, drift, roller og support: nuværende vs. mål (EY-platform), migrationsplan, miljø-/konfig-inventar, backup/BCDR, CI og support-/vedligeholdelsesmodel. (Udkast.) |
| `Pillar2-Validator_Valideringsrapport.md` | Auto-genereret valideringsrapport fra den uafhængige valideringssuite (`validation/`): for hver eksekverbar kontrol bekræftes, at netop den rigtige kontrol fyrer på sit defekt-scenarie. Regenereres med `python -m validation.run_validation`. |
| `CHANGELOG.md` | Ændringslog pr. katalogversion — understøtter ændringsstyring og reproducerbarhed. |

## Arbejdskilder (Markdown)

Følgende `.md`-filer er arbejdskilder/auto-genererede artefakter bag docx/xlsx-pakken:
`Godkendelses-overblik.md`, `Solution_Architecture.md`,
`Sikkerhed_og_databehandling.md`, `OECD_regelgrundlag.md` (auto),
`Regel-sporbarhedsmatrix.md` (auto). De officielle leverancer er docx/xlsx-filerne;
`.md`-filerne er den levende kilde i repoet. `oecd_sources/` rummer de officielle
OECD-kilde-PDF'er (lokale, git-ignoreret).

## Sådan regenereres pakken

```bash
python -m validation.run_validation        # → Pillar2-Validator_Valideringsrapport.md
python tools/build_traceability.py         # → Pillar2-Validator_Regel-sporbarhedsmatrix.xlsx
npm install docx && node tools/build_approval_docs.js   # → de 4 docx
python tools/update_docs.py                # → sporbarhedsmatrix.md + STATS-blokke
```

## Status og brug

- **Kilde (source of truth):** Denne mappe. Her redigeres og versioneres dokumenterne.
- **Officiel kopi (record of record):** Ved formel godkendelse lægges en kopi i
  EY's dokument-/governance-system. Repoet forbliver den levende kilde.
- **Klassifikation:** Fortroligt — internt. Dokumenterne må kun ligge i et
  **privat** repo og i EY-godkendte systemer.
- **Modenhed:** Research preview. Skal til EY-platform før produktionsbrug med
  klientdata; statusfelterne i Godkendelses-overblik afspejler dette ærligt.

## Vedligehold

Opdatér dokumenterne, når noget væsentligt ændres — især:

- Nye eller ændrede kontroller → opdatér regel-JSON, bump `catalog_version`,
  regenerér matrix + valideringsrapport og opdatér CHANGELOG.
- Ændret hosting/sikkerhed/retention → opdatér de relevante afsnit (docx).
- Ændret referencedata-kilde/-mekanisme → opdatér afsnit 7 + referencedata-fanen.

Dokumenterne er genereret med versionsnummer og dato på forsiden; hæv versionen
ved hver væsentlig revision.
