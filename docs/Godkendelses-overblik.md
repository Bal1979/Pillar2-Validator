# Godkendelses-overblik — Pillar II GIR-Validator

**Formål:** Forsidedokument til intern EY tool-governance. Viser parathed pr.
område og de åbne punkter med næste skridt og ejer. Komplementeres af
`Solution_Architecture.md`, `Regel-sporbarhedsmatrix.md`, `OECD_regelgrundlag.md`
og `Sikkerhed_og_databehandling.md`.

**Status:** Under udvikling (research preview-niveau). Skal til EY-platform før
produktionsbrug med klientdata. Klassifikation: Fortroligt — internt.

<!-- STATS:START -->
**Nøgletal (katalog 0.15.0):** 82/163 OECD-regler eksekverbare (heraf 19 beregningsregler) · 14 check-typer · 75 tests grønne.
<!-- STATS:END -->

## Parathed pr. område

| Område | Status | Note |
|--------|--------|------|
| Skema-validering (lag 1) | **Dækket** | Direkte mod OECD's officielle GIR-XSD; XXE fra; testet. |
| Strukturel integritet (lag 2) | **Dækket** | Rod/MessageSpec/GLOBEBody/sektioner + CompanyContext-udtræk. |
| OECD-regelgrundlag (dokumentation) | **Dækket** | Alle 163 officielle regler udtrukket og klassificeret; 14 guidance-issues; provenance. |
| OECD-regelmotor (lag 3-4) | **Udkast** | Motorvokabular dækker ALLE kategorier (inkl. beregningsmotor); regler eksekverbare med bekræftet OECD-nummer (antal: se nøgletal), udvides batch-vis. |
| Guidance-afvigelser (lag 5) | **Udkast** | Switched-off-regler respekteres; AdditionalDataPoint-anerkendelse mangler. |
| GIR/QDMTT-kryds (lag 6) | **Åbent** | Kilde-agnostisk design klar; ikke implementeret. |
| Danske felt-regler (lag 7) | **Åbent** | Afventer afklaring mod Skattestyrelsen/DAC9. |
| Beregningsregler | **Udkast** | Beregningsmotor (`calculation`-check-type) aktiv; en voksende delmængde kodet og verificeret — udvides batch-vis. |
| Rapport/UI | **Udkast** | Dansk HTML-rapport + JSON; PDF/eksport mangler. |
| Sikkerhed/GDPR | **Udkast** | Inputhærdning på plads; fuld databehandlingsbeskrivelse skal review'es af jura/sikkerhed. |
| Hosting/drift | **Åbent** | Følger EY-platform (som SAF-T). |
| Testsuite | **Dækket (voksende)** | 58 tests + lint-port; udvides med regeldækning. |

## Åbne punkter — næste skridt + ejer

1. **Udvid eksekverbar regeldækning** (data-opgave): kod de udtrykkelige
   conditional/compare/value_range-regler batch-vis. *Ejer: udvikling.*
2. **Flere beregningsregler** — beregningsmotoren er bygget og verificeret; en
   delmængde er kodet, resten kodes batch-vis. *Ejer: udvikling.*
3. **Lag 5 — AdditionalDataPoint-workarounds** anerkendes som gyldige. *Ejer: udvikling.*
4. **Lag 6 — GIR/QDMTT-kryds** mod normaliseret QDMTT-model. *Ejer: udvikling.*
5. **Danske felt-regler (lag 7)** — verificér mod skat.dk + Den juridiske
   vejledning C.K. + DAC9 (MessageTypeIndic, korrektion, indsendelseskanal,
   central vs. lokal filing). *Ejer: fag/jura + udvikling.*
6. **Databehandling/DPA + dataplacering (EU)** — review. *Ejer: jura/DPO.*
7. **Hosting, penetrationstest, SOC 2/ISO 27001** — fra driftsplatformen.
   *Ejer: EY-platform/org.*
8. **Uafhængigt valideringsdatasæt** — rigtige GIR-filer afstemt mod OECD's egen
   validator som facit. *Ejer: fag.*

## Bevidste designvalg (til governance-noten)

- Eget repo med kerne kopieret fra SAF-T (severity/finding/katalog), så en senere
  konsolidering til delt bibliotek bliver mekanisk.
- Regler som data → fuld sporbarhed og kontrolleret ændringsstyring.
- Skemaer + regler udtrukket fra OECD's egne dokumenter med provenance (ingen
  gættede regelnumre; kun verificeret semantik gøres eksekverbar).
