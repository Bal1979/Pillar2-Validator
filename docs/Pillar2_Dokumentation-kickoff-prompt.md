# Pillar 2 GIR-Validator — kickoff-prompt: dokumentationspakke til EY-standard

> Indsæt teksten nedenfor i en ny session for at løfte **godkendelses-/
> dokumentationspakken** for Pillar 2 op på **nøjagtig samme ramme som SAF-T, VIES,
> VAT Analytics og Data Extract**. Pillar 2 har allerede god dokumentation — men kun
> som løse `.md`-filer uden tool-præfiks. Opgaven er at **migrere/løfte** den til den
> fælles docx/xlsx-pakke med samme filnavne, sektioner og rækkefølge som de andre, så
> rammen er identisk på tværs af porteføljen. Indholdet skal fortsat ærligt afspejle,
> at værktøjet er på research-preview-niveau.

---

Løft dokumentationen for mit værktøj **"Pillar 2 GIR-Validator"** (validerer en færdig
GloBE Information Return mod OECD's skema + valideringsregler) op på den **fælles
EY-dokumentationsramme**. Jeg har netop fået lavet en TTAR-parathedsvurdering, hvor
Pillar 2 er fagligt langt, men ligger på research-preview-niveau, og hvor docs kun
findes som `.md` — ikke som den færdige docx-pakke de fire modne værktøjer har. Jeg vil
**ikke** lave et fuldt kodereview nu — jeg vil have **rammen gjort identisk** med de
andre og udfyldt så langt værktøjet tillader (Dækket / Udkast / Åbent).

**ADGANG — bed om adgang til disse mapper med det samme:**
- `~/Projects/pillar2-validator` (værktøjet vi dokumenterer — har allerede .md-docs)
- `~/Projects/saf-t-validator` (REFERENCESKABELONEN — docs-pakken vi matcher 1:1)
- `~/Projects/vies-validation` (indeholder review-playbook'en + en moden docs-pakke)
- `~/Projects/vat-extract` (Data Extract — indeholder de genbrugbare docs-generatorer)
- `~/Projects/balai-platform` (tværgående platform-/build-standard)

**LÆS FØRST, i denne rækkefølge:**
1. Review-playbook'en: `~/Projects/vies-validation/docs/Review-playbook_EY-standard.md`
   — især §4 (dokumentationspakken) og §3 (kvalitets-bar).
2. Referenceskabelonen: `~/Projects/saf-t-validator/docs/README.md` + de seks dokumenter
   den indekserer. Det er DENNE struktur, rammen skal matche 1:1.
3. Pillar 2's eksisterende docs (råstoffet der skal løftes, IKKE kasseres):
   `~/Projects/pillar2-validator/docs/` — `Godkendelses-overblik.md`,
   `Solution_Architecture.md`, `Sikkerhed_og_databehandling.md`, `OECD_regelgrundlag.md`,
   `Regel-sporbarhedsmatrix.md`, `CHANGELOG.md` + `~/Projects/pillar2-validator/ARCHITECTURE.md`.
   (Kort status: lag 1-4 kører, data-drevet regelmotor, beregningsmotor aktiv, golden-fixtur;
   78/163 OECD-regler eksekverbare; ingen login/auth endnu; sikkerhed = udkast.)
4. Tværgående standard: `~/Projects/balai-platform/PLATFORM-BUILD-STANDARD.md`.

**MÅL — PRODUCÉR DENNE PAKKE i `pillar2-validator/docs/` (samme navne/struktur som SAF-T):**
- `Pillar2-Validator_Godkendelses-overblik.docx` — løft af eksisterende
  `Godkendelses-overblik.md`. Parathed pr. område (Dækket / Udkast / Åbent) + åbne
  punkter med næste skridt + ejer. Behold ærligheden om research-preview-status.
- `Pillar2-Validator_Solution_Architecture.docx` — løft af `Solution_Architecture.md`
  + `ARCHITECTURE.md`: formål/afgrænsning, stack, 8-lags model, regelmotor-vokabular,
  referencedata/provenance (OECD-skema+regler), QA, ændringsstyring, hosting, åbne punkter.
- `Pillar2-Validator_Sikkerhed_og_databehandling.docx` — løft af
  `Sikkerhed_og_databehandling.md`: datakategorier (GIR = følsomme koncerntal), dataflow,
  inputhærdning (XXE fra), app-sikkerhed, trusselsmodel, GDPR/DPA, åbne punkter.
- `Pillar2-Validator_Hosting_og_drift.docx` — **NY** (findes ikke endnu): nuværende vs.
  EY-platform, migrationsplan, env-/konfig-inventar, backup/BCDR, roller, support. Brug
  SAF-T's `Hosting_og_drift` som skabelon; meget kan genbruges (samme stack/platform).
- `Pillar2-Validator_Regel-sporbarhedsmatrix.xlsx` — løft af `Regel-sporbarhedsmatrix.md`
  til xlsx: hver regel → autoritativ OECD-kilde → modul → testdækning, + faner for
  referencedata-provenance og severity. Generér fra regel-JSON så den holder sig selv ajour.
- `Pillar2-Validator_Valideringsrapport.md` — auto-genereret fra en uafhængig
  valideringssuite (plantet ÉN defekt pr. kontrol). Findes den ikke endnu, så skriv en
  eksplicit placeholder, der siger hvad der mangler, og list det som "Åbent".
- `README.md` (pakke-indeks, som SAF-T's) + behold/opdatér `CHANGELOG.md`.

**MEKANIK — genbrug de eksisterende generatorer:**
- docx: `~/Projects/vat-extract/tools/build_approval_docs.js` (docx-js). Lokal
  `npm install docx`; `node_modules` gitignored.
- sporbarhedsmatrix: `~/Projects/vat-extract/tools/build_traceability.py` (tilpas til
  Pillar 2's regel-JSON). Pillar 2 har allerede `tools/sync_oecd_rules.py` og
  `tools/update_docs.py` — afklar om matrixen skal hænges på dem, så STATS-blokken og
  matrixen genereres samme sted.

**ARBEJDSRÆKKEFØLGE:**
0. **AFKLAR SCOPE FØRST** med AskUserQuestion (playbook §0/§7): bekræft at leverancen er
   docx-rammen (ikke fuld regeludvidelse eller auth-bygning nu), og hvilke kode-/
   governance-punkter der skal LISTES som "Åbent" (auth/login, fuld regeldækning,
   lag 6-7, valideringssuite, hosting på EY-platform). Byg intet før.
1. **Map eksisterende .md → docx-rammen:** afklar hvilke afsnit der flytter 1:1, hvad
   der mangler (især `Hosting_og_drift`), og hvad der skal markeres Udkast/Åbent.
2. **Generér de fire docx + matrix-xlsx + valideringsrapport** via generatorerne. Sørg
   for tool-præfiks i ALLE filnavne (`Pillar2-Validator_…`) så navngivningen matcher
   søsterværktøjerne — de gamle uprefiksede .md kan blive som arbejdskilde, men den
   officielle pakke er docx/xlsx.
3. **Skriv/opdatér README + CHANGELOG** så pakken indekserer sig selv som SAF-T's.
4. **Selvkontrol:** sammenlign filnavne, sektioner og rækkefølge 1:1 mod SAF-T-pakken —
   rammen SKAL være identisk; kun indholdet/statusniveauet afspejler research-preview.

**PRINCIP FOR ÆRLIG STATUS:** Behold den eksisterende ærlighed (research preview,
78/163 regler, ingen auth endnu, sikkerhed = udkast). Rammen skal være komplet og
identisk; statusfelterne må gerne være Udkast/Åbent med tydelig ejer + næste skridt.

**KONVENTIONER:**
- Tal dansk, klart og konkret. **Slet aldrig filer uden min tilladelse.** Brug
  AskUserQuestion ved uklarheder, og lav en task-liste for arbejdet.
- Jeg kører `pytest` lokalt og **pusher selv** (SSH ligger kun på min Mac). Giv
  commit/push som en kopiérbar terminal-boks — **UDEN inline-kommentarer** (zsh).
- Lokalt miljø: venv. Mind mig om `pip install -r requirements.txt -r requirements-dev.txt`.
  docx kræver lokal `npm install docx`; `node_modules` gitignored.
- Klassifikation på alle docs: **Fortroligt — internt.** Kun privat repo + EY-godkendte systemer.

**START:** bed om mappeadgang (inkl. de fem repoer ovenfor), læs playbook'en OG
SAF-T's docs-README, kør så scope-afklaringen — og løft derefter rammen.
