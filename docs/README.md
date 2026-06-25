# Dokumentation — Pillar II GIR-Validator

Produkt- og governance-dokumentation for Pillar II GIR-Validatoren. Dokumenterne
versioneres **sammen med koden**, så de altid matcher den version af produktet, de
beskriver (samme commit, samme git-historik). Samme model som SAF-T-validatoren.

## Indhold

| Fil | Indhold |
|-----|---------|
| `Godkendelses-overblik.md` | **Start her.** Status- og forsidedokument: samler pakken, viser godkendelsesparathed pr. område (Dækket/Udkast/Åbent) og lister åbne punkter med næste skridt. Tag dette med til EY's tool-governance. |
| `Solution_Architecture.md` | Løsnings- og arkitekturbeskrivelse: formål, afgrænsning, arkitektur, dataflow, den 8-lags valideringsmodel, referencedata, sikkerhed/GDPR, kvalitetssikring, ændringsstyring, begrænsninger og åbne punkter. |
| `Regel-sporbarhedsmatrix.md` | Sporbarhedsmatrix: hver kontrol mappet til autoritativ OECD-kilde, modul og testdækning. Plus dækning mod det fulde 163-regelkatalog. Auto-genereret. |
| `OECD_regelgrundlag.md` | Det komplette regelgrundlag: 163 officielle regler klassificeret pr. check-type, de 14 guidance-issues, og motorens check-type-vokabular. |
| `Sikkerhed_og_databehandling.md` | Sikkerheds- og databehandlingsbeskrivelse: datakategorier, dataflow, GDPR, XXE/inputhærdning, retention, trusselsmodel, åbne punkter. (Udkast — review af jura/sikkerhed.) |
| `CHANGELOG.md` | Ændringslog pr. version. |
| `oecd_sources/` | De officielle OECD-kilde-PDF'er (lokale, git-ignoreret) — sandhedskilde for skema og regler. |

## Status og brug

- **Kilde (source of truth):** Denne mappe. Her redigeres og versioneres dokumenterne (markdown).
- **Officiel kopi (record of record):** Ved formel EY-godkendelse kan en kopi
  renderes til .docx/.xlsx og lægges i EY's governance-system. Repoet forbliver
  den levende kilde. (Render-trin kan tilføjes når formatet er fastlagt.)
- **Klassifikation:** Fortroligt — internt. Værktøjet behandler følsomme
  koncerntal; dokumenter og kode må kun ligge i privat repo / EY-godkendte systemer.

## Vedligehold

Opdatér dokumenterne ved væsentlige ændringer — især:

- Ny/ændret kontrol → opdatér regelkatalog + sporbarhedsmatrix + CHANGELOG og bump
  `catalog_version`.
- Ændret referencedata-kilde (OECD-skema/regler) → opdatér `OECD_regelgrundlag.md`
  og `schemas/SCHEMA_SOURCES.md`.
- Ændret hosting/sikkerhed/retention → opdatér de relevante afsnit.
