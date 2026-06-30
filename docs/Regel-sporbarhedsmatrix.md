# Regel-sporbarhedsmatrix — Pillar II GIR-Validator

Auto-genereret af `tools/update_docs.py`. Regenereres efter hver batch.

Katalogversion: **0.17.0** · OECD-regelliste: **163**, heraf **87** eksekverbare (inkl. 19 beregningsregler).

## Lag 3-4 — eksekverbare OECD-regler

| OECD# | Level | Check-type | Navn | Kilde |
|---|---|---|---|---|
| 60007 | file | unique | DocRefId skal være unik | OECD Status Message User Guide Part 4 — regel 60007 (DocRefID allerede brugt) |
| 60015 | file | required_if | CorrDocRefId kræves ved rettelse/sletning | OECD Status Message User Guide Part 4 — regel 60015 (OECD2/3 uden CorrDocRefId) |
| 60012 | file | forbidden_if | CorrDocRefId må ikke angives ved ny data | OECD Status Message User Guide Part 4 — regel 60012 (OECD1/OECD0 → CorrDocRefId udeladt) |
| 60004 | file | mutually_exclusive | Ny data og rettelser må ikke blandes | OECD Status Message User Guide Part 4 — regel 60004 |
| 60006 | file | unique | Samme dokument må ikke rettes/slettes to gange | OECD Status Message User Guide Part 4 — regel 60006 |
| 70001 | record | conditional | NOTIN-TIN skal udfyldes korrekt | OECD Status Message User Guide Part 4 — regel 70001 |
| 70002 | record | conditional | TIN='NOTIN' kræver TypeOfTIN=GIR3004 | OECD Status Message User Guide Part 4 — regel 70002 |
| 60020 | file | compare | Periodens startdato må ikke ligge efter slutdato | OECD Status Message User Guide Part 4 — regel 60020 |
| 60021 | file | compare | Periodens slutdato må ikke ligge efter rapporteringsperioden | OECD Status Message User Guide Part 4 — regel 60021 |
| 60023 | file | compare | FilingCE's land skal matche afsenderlandet | OECD Status Message User Guide Part 4 — regel 60023 |
| 70003 | record | conditional | Unknown-TIN skal udfyldes korrekt | OECD Status Message User Guide Part 4 — regel 70003 |
| 70005 | record | conditional | issuedBy kræves for almindelige TIN | OECD Status Message User Guide Part 4 — regel 70005 |
| 70013 | record | conditional | GIR313 og GIR314 udelukker hinanden (samme CE) | OECD Status Message User Guide Part 4 — regel 70013 |
| 70014 | record | conditional | GIR307 og GIR308 udelukker hinanden (samme CE) | OECD Status Message User Guide Part 4 — regel 70014 |
| 70018 | record | conditional | GIR305 og GIR306 udelukker hinanden (samme CE) | OECD Status Message User Guide Part 4 — regel 70018 |
| 70022 | record | compare | ChangeDate må ikke ligge før periodens start | OECD Status Message User Guide Part 4 — regel 70022 |
| 70023 | record | compare | ChangeDate må ikke ligge efter periodens slutning | OECD Status Message User Guide Part 4 — regel 70023 |
| 70044 | record | conditional | ETRStatus skal indeholde ETRException eller ETRComputation | OECD Status Message User Guide Part 4 — regel 70044 |
| 70073 | record | value_range | EndAmount må ikke være negativ | OECD Status Message User Guide Part 4 — regel 70073 |
| 70104 | record | value_range | UTPRTopUpTaxCarriedForward må ikke være negativ | OECD Status Message User Guide Part 4 — regel 70104 |
| 70123 | record | value_range | Additions må ikke være negativ | OECD Status Message User Guide Part 4 — regel 70123 |
| 70009 | record | conditional | Ugyldig GlobeStatus for UPE | OECD Status Message User Guide Part 4 — regel 70009 |
| 70010 | record | cardinality | UPE må kun have ét ResCountryCode | OECD Status Message User Guide Part 4 — regel 70010 |
| 70011 | record | cardinality | CE må kun have ét ResCountryCode | OECD Status Message User Guide Part 4 — regel 70011 |
| 70024 | record | conditional | PreOwnership må ikke udfyldes ved PreGlobeStatus GIR719 | OECD Status Message User Guide Part 4 — regel 70024 |
| 70032 | record | conditional | QIIR kræver CE-Rules GIR201 eller GIR202 | OECD Status Message User Guide Part 4 — regel 70032 |
| 70025 | record | conditional | Nominee-PreOwnership kræver NOTIN-TIN | OECD Status Message User Guide Part 4 — regel 70025 |
| 70029 | record | conditional_ref | Ownership-TIN (GIR801) skal matche en rapporteret enheds-TIN | OECD Status Message User Guide Part 4 — regel 70029 |
| 70030 | record | conditional_ref | Ownership-TIN (GIR802-804) skal matche en rapporteret enheds-TIN | OECD Status Message User Guide Part 4 — regel 70030 |
| 70086 | record | calculation | ExcessProfits-beregning | OECD Status Message User Guide Part 4 — regel 70086 |
| 70072 | record | calculation | EndAmount-beregning (DDT-recapture) | OECD Status Message User Guide Part 4 — regel 70072 |
| 70083 | record | calculation | ExcessNegTaxExpense/Remaining-beregning | OECD Status Message User Guide Part 4 — regel 70083 |
| 70105 | record | calculation | UTPRTopUpTaxCarriedForward-beregning | OECD Status Message User Guide Part 4 — regel 70105 |
| 60027 | file | calculation | IIR ParentEntity TopUpTax-beregning | OECD Status Message User Guide Part 4 — regel 60027 |
| 70076 | record | calculation | TransBlendCFC/Total-beregning | OECD Status Message User Guide Part 4 — regel 70076 |
| 70078 | record | calculation | BefRecastAdjust-beregning | OECD Status Message User Guide Part 4 — regel 70078 |
| 70079 | record | calculation | PreRecast-beregning | OECD Status Message User Guide Part 4 — regel 70079 |
| 70064 | record | calculation | DeferTaxAsset/Total-beregning | OECD Status Message User Guide Part 4 — regel 70064 |
| 70065 | record | calculation | CoveredTaxRefund/Total-beregning | OECD Status Message User Guide Part 4 — regel 70065 |
| 70108 | record | conditional | Basis kræver TaxRate | OECD Status Message User Guide Part 4 — regel 70108 |
| 70109 | record | conditional | Basis GIR1907 kræver IndOwners/ResCountryCode | OECD Status Message User Guide Part 4 — regel 70109 |
| 70110 | record | conditional | Basis GIR1903/1908 kræver IndOwners | OECD Status Message User Guide Part 4 — regel 70110 |
| 70111 | record | conditional | Basis GIR1904/1909 kræver EntityOwner/ExTypeOfEntity | OECD Status Message User Guide Part 4 — regel 70111 |
| 70112 | record | conditional | Basis GIR1904 udelukker ExTypeOfEntity GIR2805 | OECD Status Message User Guide Part 4 — regel 70112 |
| 70113 | record | conditional | Basis GIR1909 udelukker ExTypeOfEntity GIR2804 | OECD Status Message User Guide Part 4 — regel 70113 |
| 70060 | record | conditional | AdjustmentItem GIR2025 kræver IntShippingIncome | OECD Status Message User Guide Part 4 — regel 70060 |
| 70107 | record | conditional | Exception=TRUE udelukker CrossBorderAdjustments | OECD Status Message User Guide Part 4 — regel 70107 |
| 70082 | record | conditional | DeferredTaxAssets kræver Start eller Recast = 0 | OECD Status Message User Guide Part 4 — regel 70082 |
| 70045 | record | conditional | SafeHarbour GIR1203-1205 kræver TransitionalCbCRSafeHarbour | OECD Status Message User Guide Part 4 — regel 70045 |
| 70047 | record | conditional | SafeHarbour GIR1203 kræver Revenue | OECD Status Message User Guide Part 4 — regel 70047 |
| 70048 | record | conditional | SafeHarbour GIR1204 kræver IncomeTax | OECD Status Message User Guide Part 4 — regel 70048 |
| 70049 | record | conditional | SafeHarbour GIR1206 kræver UTPRSafeHarbour | OECD Status Message User Guide Part 4 — regel 70049 |
| 70051 | record | conditional | SafeHarbour GIR1208 kræver AggregateSimplified | OECD Status Message User Guide Part 4 — regel 70051 |
| 70041 | file | conditional | CFSofUPE GIR502/504 udelukker SafeHarbour GIR1207-1209 | OECD Status Message User Guide Part 4 — regel 70041 |
| 70016 | record | conditional | GlobeStatus GIR307 kræver GIR309 | OECD Status Message User Guide Part 4 — regel 70016 |
| 70017 | record | conditional | GlobeStatus GIR308 kræver GIR309 | OECD Status Message User Guide Part 4 — regel 70017 |
| 70026 | record | conditional | GlobeStatus GIR305 kræver 100% ejerskab | OECD Status Message User Guide Part 4 — regel 70026 |
| 70062 | record | conditional | AdjustmentItem GIR2720 udelukker negativ AdjustedCoveredTax | OECD Status Message User Guide Part 4 — regel 70062 |
| 70088 | record | conditional | Negativ NetGlobeIncome kræver Art4.1.5 | OECD Status Message User Guide Part 4 — regel 70088 |
| 70101 | record | conditional | Employees kræves når UTPRTopUpTaxCarryForward ≠ 0 | OECD Status Message User Guide Part 4 — regel 70101 |
| 70102 | record | conditional | TangibleAssetValue kræves når UTPRTopUpTaxCarryForward ≠ 0 | OECD Status Message User Guide Part 4 — regel 70102 |
| 70103 | record | conditional | UTPRPercentage skal være 0 når carryforward > 0 | OECD Status Message User Guide Part 4 — regel 70103 |
| 70115 | record | conditional | AdjustmentItem GIR2022/2023 kræver UPEAdjustments | OECD Status Message User Guide Part 4 — regel 70115 |
| 60028 | record | calculation | AdjustedFANIL/Total-beregning | OECD Status Message User Guide Part 4 — regel 60028 |
| 70074 | record | calculation | TotalDDT-beregning | OECD Status Message User Guide Part 4 — regel 70074 |
| 70077 | record | calculation | DeferTaxAdjustAmt/Total-beregning (Recast) | OECD Status Message User Guide Part 4 — regel 70077 |
| 70055 | record | calculation | OutstandingBalance-beregning | OECD Status Message User Guide Part 4 — regel 70055 |
| 70059 | record | unique_in | AdjustmentItem-kode kun én gang pr. ETR | OECD Status Message User Guide Part 4 — regel 70059 |
| 70067 | record | unique_in | AmountAttributed-år skal være unikke | OECD Status Message User Guide Part 4 — regel 70067 |
| 70090 | record | calculation | GlobeLoss skal svare til NetGlobeIncome/Total | OECD Status Message User Guide Part 4 — regel 70090 |
| 70124 | record | value_range | CrossAllocation/Reductions må ikke være positiv | OECD Status Message User Guide Part 4 — regel 70124 |
| 70021 | record | conditional | GlobeStatus GIR316/318 kræver OwnershipChange | OECD Status Message User Guide Part 4 — regel 70021 |
| 70066 | record | compare | DeferTaxAsset-år må ikke ligge efter periodens start | OECD Status Message User Guide Part 4 — regel 70066 |
| 70068 | record | compare | CoveredTaxRefund-år må ikke ligge efter periodens start | OECD Status Message User Guide Part 4 — regel 70068 |
| 70070 | record | compare | Recapture-år må ikke ligge efter periodens slut | OECD Status Message User Guide Part 4 — regel 70070 |
| 70093 | record | compare | NONArt4.1.5-år må ikke overstige periodens slut | OECD Status Message User Guide Part 4 — regel 70093 |
| 70015 | file | conditional | GIR308 kræver en tilsvarende GIR307-enhed | OECD Status Message User Guide Part 4 — regel 70015 |
| 70019 | file | conditional | GIR305 kræver en tilsvarende GIR306-enhed | OECD Status Message User Guide Part 4 — regel 70019 |
| 70087 | record | calculation | SubstanceExclusion/Total-beregning | OECD Status Message User Guide Part 4 — regel 70087 |
| 70091 | record | calculation | ExpectedAdjustedCoveredTax = GlobeLoss × 15% | OECD Status Message User Guide Part 4 — regel 70091 |
| 70097 | record | calculation | InclusionRatio-beregning | OECD Status Message User Guide Part 4 — regel 70097 |
| 70098 | record | calculation | TopUpTaxShare = TopUpTax × InclusionRatio | OECD Status Message User Guide Part 4 — regel 70098 |
| 70038 | record | conditional | Transitional CbCR SafeHarbour udløber efter 30/06/2028 | OECD Status Message User Guide Part 4 — regel 70038 |
| 70039 | record | conditional | UTPR SafeHarbour (GIR1206) udløber efter 31/12/2026 | OECD Status Message User Guide Part 4 — regel 70039 |
| 70071 | record | conditional | Recapture-år må ikke være 4+ år før periodens slut | OECD Status Message User Guide Part 4 — regel 70071 |
| 70094 | record | conditional | Articles GIR2605 kræver år mindst 4 år før periodens slut | OECD Status Message User Guide Part 4 — regel 70094 |
| 70095 | record | conditional | Articles GIR2602 kræver det femte år før periodens slut | OECD Status Message User Guide Part 4 — regel 70095 |

## Dækning pr. check-type-kategori

| Kategori | Antal | Status |
|---|---|---|
| conditional | 64 | ✅ |
| other | 42 | 🔎 gennemgang |
| calculation | 25 | ✅ delvist (19 kodet) |
| compare | 15 | ✅ |
| required | 4 | ✅ |
| format | 3 | ✅ |
| unique | 3 | ✅ |
| value_range | 3 | ✅ |
| ref_integrity | 2 | ✅ |
| mutually_exclusive | 1 | ✅ |
| not_equal | 1 | ✅ |

**Eksekverbar dækning:** 87/163. 4 regler slået fra (fyres aldrig). Hver kodet regel er verificeret med negativ test + mod golden-fixturen `tests/fixtures/gir_valid_rich.xml`.
