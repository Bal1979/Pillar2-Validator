# Valideringsrapport — Pillar II GIR-Validator

Uafhængig valideringssuite: hver eksekverbar OECD-kontrol verificeres ved at plante ÉN målrettet defekt og bekræfte, at netop den tilsigtede kontrol udløses i regelmotoren — og at den rene golden-GIR ikke giver fund. Suiten er reproducerbar og køres som CI-port (`python -m validation.run_validation`).

- **Genereret:** 2026-06-30 11:37 UTC
- **Regelkatalog:** v0.14.0
- **Eksekverbare kontroller:** 78
- **Ren golden-GIR uden fund:** JA
- **Auto-scenarier bestået:** 78 / 78

## Resultater

| OECD-regel | Niveau | Check-type | Kontrol | Resultat | Udløste regler |
|---|---|---|---|---|---|
| **60004** | file | mutually_exclusive | Ny data og rettelser må ikke blandes | ✅ Bestået | 60004 |
| **60006** | file | unique | Samme dokument må ikke rettes/slettes to gange | ✅ Bestået | 60006 |
| **60007** | file | unique | DocRefId skal være unik | ✅ Bestået | 60007 |
| **60012** | file | forbidden_if | CorrDocRefId må ikke angives ved ny data | ✅ Bestået | 60012 |
| **60015** | file | required_if | CorrDocRefId kræves ved rettelse/sletning | ✅ Bestået | 60015 |
| **60020** | file | compare | Periodens startdato må ikke ligge efter slutdato | ✅ Bestået | 60020 |
| **60021** | file | compare | Periodens slutdato må ikke ligge efter rapporteringsperioden | ✅ Bestået | 60021 |
| **60023** | file | compare | FilingCE's land skal matche afsenderlandet | ✅ Bestået | 60023 |
| **60027** | file | calculation | IIR ParentEntity TopUpTax-beregning | ✅ Bestået | 60027 |
| **70015** | file | conditional | GIR308 kræver en tilsvarende GIR307-enhed | ✅ Bestået | 70015 |
| **70019** | file | conditional | GIR305 kræver en tilsvarende GIR306-enhed | ✅ Bestået | 70019 |
| **70041** | file | conditional | CFSofUPE GIR502/504 udelukker SafeHarbour GIR1207-1209 | ✅ Bestået | 70041 |
| **60028** | record | calculation | AdjustedFANIL/Total-beregning | ✅ Bestået | 60028 |
| **70001** | record | conditional | NOTIN-TIN skal udfyldes korrekt | ✅ Bestået | 70001 |
| **70002** | record | conditional | TIN='NOTIN' kræver TypeOfTIN=GIR3004 | ✅ Bestået | 70002, 70005 |
| **70003** | record | conditional | Unknown-TIN skal udfyldes korrekt | ✅ Bestået | 70003, 70005 |
| **70005** | record | conditional | issuedBy kræves for almindelige TIN | ✅ Bestået | 70005 |
| **70009** | record | conditional | Ugyldig GlobeStatus for UPE | ✅ Bestået | 70009, 70019 |
| **70010** | record | cardinality | UPE må kun have ét ResCountryCode | ✅ Bestået | 70010 |
| **70011** | record | cardinality | CE må kun have ét ResCountryCode | ✅ Bestået | 70011 |
| **70013** | record | conditional | GIR313 og GIR314 udelukker hinanden (samme CE) | ✅ Bestået | 70013 |
| **70014** | record | conditional | GIR307 og GIR308 udelukker hinanden (samme CE) | ✅ Bestået | 70014, 70016, 70017 |
| **70016** | record | conditional | GlobeStatus GIR307 kræver GIR309 | ✅ Bestået | 70016 |
| **70017** | record | conditional | GlobeStatus GIR308 kræver GIR309 | ✅ Bestået | 70015, 70017 |
| **70018** | record | conditional | GIR305 og GIR306 udelukker hinanden (samme CE) | ✅ Bestået | 70018, 70026 |
| **70021** | record | conditional | GlobeStatus GIR316/318 kræver OwnershipChange | ✅ Bestået | 70021 |
| **70022** | record | compare | ChangeDate må ikke ligge før periodens start | ✅ Bestået | 60020, 70022 |
| **70023** | record | compare | ChangeDate må ikke ligge efter periodens slutning | ✅ Bestået | 60020, 70023 |
| **70024** | record | conditional | PreOwnership må ikke udfyldes ved PreGlobeStatus GIR719 | ✅ Bestået | 70024 |
| **70025** | record | conditional | Nominee-PreOwnership kræver NOTIN-TIN | ✅ Bestået | 70025 |
| **70026** | record | conditional | GlobeStatus GIR305 kræver 100% ejerskab | ✅ Bestået | 70019, 70026 |
| **70029** | record | conditional_ref | Ownership-TIN (GIR801) skal matche en rapporteret enheds-TIN | ✅ Bestået | 70005, 70029 |
| **70030** | record | conditional_ref | Ownership-TIN (GIR802-804) skal matche en rapporteret enheds-TIN | ✅ Bestået | 70005, 70030 |
| **70032** | record | conditional | QIIR kræver CE-Rules GIR201 eller GIR202 | ✅ Bestået | 70032 |
| **70044** | record | conditional | ETRStatus skal indeholde ETRException eller ETRComputation | ✅ Bestået | 70044 |
| **70045** | record | conditional | SafeHarbour GIR1203-1205 kræver TransitionalCbCRSafeHarbour | ✅ Bestået | 70045, 70047 |
| **70047** | record | conditional | SafeHarbour GIR1203 kræver Revenue | ✅ Bestået | 70045, 70047 |
| **70048** | record | conditional | SafeHarbour GIR1204 kræver IncomeTax | ✅ Bestået | 70045, 70048 |
| **70049** | record | conditional | SafeHarbour GIR1206 kræver UTPRSafeHarbour | ✅ Bestået | 70049 |
| **70051** | record | conditional | SafeHarbour GIR1208 kræver AggregateSimplified | ✅ Bestået | 70051 |
| **70055** | record | calculation | OutstandingBalance-beregning | ✅ Bestået | 70055 |
| **70059** | record | unique_in | AdjustmentItem-kode kun én gang pr. ETR | ✅ Bestået | 70059 |
| **70060** | record | conditional | AdjustmentItem GIR2025 kræver IntShippingIncome | ✅ Bestået | 70060 |
| **70062** | record | conditional | AdjustmentItem GIR2720 udelukker negativ AdjustedCoveredTax | ✅ Bestået | 70062 |
| **70064** | record | calculation | DeferTaxAsset/Total-beregning | ✅ Bestået | 70064 |
| **70065** | record | calculation | CoveredTaxRefund/Total-beregning | ✅ Bestået | 70065 |
| **70066** | record | compare | DeferTaxAsset-år må ikke ligge efter periodens start | ✅ Bestået | 70066 |
| **70067** | record | unique_in | AmountAttributed-år skal være unikke | ✅ Bestået | 70067 |
| **70068** | record | compare | CoveredTaxRefund-år må ikke ligge efter periodens start | ✅ Bestået | 70068 |
| **70070** | record | compare | Recapture-år må ikke ligge efter periodens slut | ✅ Bestået | 70070 |
| **70072** | record | calculation | EndAmount-beregning (DDT-recapture) | ✅ Bestået | 70072 |
| **70073** | record | value_range | EndAmount må ikke være negativ | ✅ Bestået | 70073 |
| **70074** | record | calculation | TotalDDT-beregning | ✅ Bestået | 70074 |
| **70076** | record | calculation | TransBlendCFC/Total-beregning | ✅ Bestået | 70076 |
| **70077** | record | calculation | DeferTaxAdjustAmt/Total-beregning (Recast) | ✅ Bestået | 70077 |
| **70078** | record | calculation | BefRecastAdjust-beregning | ✅ Bestået | 70078 |
| **70079** | record | calculation | PreRecast-beregning | ✅ Bestået | 70079 |
| **70082** | record | conditional | DeferredTaxAssets kræver Start eller Recast = 0 | ✅ Bestået | 70082 |
| **70083** | record | calculation | ExcessNegTaxExpense/Remaining-beregning | ✅ Bestået | 70083 |
| **70086** | record | calculation | ExcessProfits-beregning | ✅ Bestået | 70086 |
| **70088** | record | conditional | Negativ NetGlobeIncome kræver Art4.1.5 | ✅ Bestået | 70088 |
| **70090** | record | calculation | GlobeLoss skal svare til NetGlobeIncome/Total | ✅ Bestået | 70090 |
| **70093** | record | compare | NONArt4.1.5-år må ikke overstige periodens slut | ✅ Bestået | 70093 |
| **70101** | record | conditional | Employees kræves når UTPRTopUpTaxCarryForward ≠ 0 | ✅ Bestået | 70101, 70102 |
| **70102** | record | conditional | TangibleAssetValue kræves når UTPRTopUpTaxCarryForward ≠ 0 | ✅ Bestået | 70101, 70102 |
| **70103** | record | conditional | UTPRPercentage skal være 0 når carryforward > 0 | ✅ Bestået | 70101, 70102, 70103 |
| **70104** | record | value_range | UTPRTopUpTaxCarriedForward må ikke være negativ | ✅ Bestået | 70104 |
| **70105** | record | calculation | UTPRTopUpTaxCarriedForward-beregning | ✅ Bestået | 70105 |
| **70107** | record | conditional | Exception=TRUE udelukker CrossBorderAdjustments | ✅ Bestået | 70107 |
| **70108** | record | conditional | Basis kræver TaxRate | ✅ Bestået | 70108 |
| **70109** | record | conditional | Basis GIR1907 kræver IndOwners/ResCountryCode | ✅ Bestået | 70109 |
| **70110** | record | conditional | Basis GIR1903/1908 kræver IndOwners | ✅ Bestået | 70110 |
| **70111** | record | conditional | Basis GIR1904/1909 kræver EntityOwner/ExTypeOfEntity | ✅ Bestået | 70111 |
| **70112** | record | conditional | Basis GIR1904 udelukker ExTypeOfEntity GIR2805 | ✅ Bestået | 70112 |
| **70113** | record | conditional | Basis GIR1909 udelukker ExTypeOfEntity GIR2804 | ✅ Bestået | 70113 |
| **70115** | record | conditional | AdjustmentItem GIR2022/2023 kræver UPEAdjustments | ✅ Bestået | 70115 |
| **70123** | record | value_range | Additions må ikke være negativ | ✅ Bestået | 70123 |
| **70124** | record | value_range | CrossAllocation/Reductions må ikke være positiv | ✅ Bestået | 70124 |

## Fortolkning

«Bestået» betyder, at den tilsigtede kontrol (**fed**) optræder blandt de udløste regler for det defekte input. Et defekt-input kan realistisk udløse flere korrelerede kontroller; alle udløste regler vises for fuld transparens.

Kontroller markeret «Enhedstestet» har ikke et auto-genereret defekt-scenarie (deres check-type kræver en kontekst, synthesizeren ikke bygger automatisk), men er dækket af enhedstest-suiten i `tests/`. Rapporten supplerer — den erstatter ikke — enhedstestene, og er tænkt som et uafhængigt, læsbart korrektheds-bevis.
