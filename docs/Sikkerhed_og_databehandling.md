# Sikkerhed og databehandling — Pillar II GIR-Validator

**Status:** Udkast — skal review'es af jura/databeskyttelse og sikkerhed før
formel godkendelse. Klassifikation: Fortroligt — internt.

## 1. Datakategorier

En GIR indeholder følsomme koncern-/skatteoplysninger: enheds- og koncernnavne,
TIN'er, jurisdiktioner, regnskabstal, effektiv skattesats og top-up tax. Behandles
som fortroligt forretningsdata. Værktøjet behandler **ikke** persondata om
privatpersoner som kerneformål, men TIN/navne kan forekomme.

## 2. Dataflow og dataminimering

1. Bruger uploader en GIR-XML.
2. Filen gemmes midlertidigt under kørsel og **slettes straks efter** (ingen
   varig lagring af kildefilen i nuværende fase).
3. Resultatet vises som rapport i brugerens session. Der persisteres ikke
   klientdata i nuværende fase (historik/revisionslog kan tilføjes som i SAF-T,
   med retention-styring).
4. Ingen klientdata sendes til tredjeparter. Referencedata (skema/regler) er
   statiske, lokale filer — ingen eksterne opslag under validering.

## 3. Inputhærdning

- **XXE slået fra:** XML-parseren kører med `resolve_entities=False` og
  `no_network=True` — ingen ekstern entitetsopløsning, ingen netværksadgang fra
  parseren. Gælder både well-formedness-, XSD- og regel-parsing.
- **Streaming/størrelse:** upload-grænse via `MAX_UPLOAD_MB`. lxml `huge_tree`
  bruges kontrolleret.
- **Skema fra disk:** XSD'er valideres fra lokale, versionerede filer (provenance
  m. sha256) — ikke fra netværket.

## 4. Applikationssikkerhed

- Sikkerhedsheaders i `app.py`: Content-Security-Policy, X-Content-Type-Options,
  X-Frame-Options (DENY), Referrer-Policy, Permissions-Policy, HSTS.
- `SECRET_KEY` påkrævet i produktion (fejler hurtigt hvis ikke sat).
- Ingen råt brugerinput i filstier (midlertidige filer via `tempfile`).

## 5. Trusselsmodel (resumé)

| Trussel | Modforanstaltning |
|---------|-------------------|
| XXE / XML-bomber | resolve_entities=False, no_network, upload-grænse |
| Skadelig upload | Validering før behandling; kildefil slettes straks |
| Datalækage til tredjepart | Ingen eksterne kald under validering; statiske referencedata |
| Forældet skema afviser gyldige filer | Sync + provenance + selvtjek |
| Clickjacking/MIME-sniffing | Sikkerhedsheaders |

## 6. Åbne punkter (til review)

- Behandlingsgrundlag/DPA og dataplacering (EU) — jura/DPO.
- Persistens/retention hvis historik tilføjes (env-styret, som SAF-T).
- Adgangskontrol/auth ved produktion (følger EY-platform).
- Penetrationstest, SOC 2 / ISO 27001 — fra driftsplatformen.
- Logning/hændelseshåndtering — defineres med driftsplatformen.
