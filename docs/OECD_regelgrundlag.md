# OECD GIR — regelgrundlag (komplet)

Auto-genereret af `tools/update_docs.py`. Fuldt officielt regelgrundlag udtrukket fra OECD's egne dokumenter, committet i `reference/`.

## Overblik

| | Antal |
|---|---|
| Regler i alt | 163 |
| File-level | 39 |
| Record-level | 124 |
| Slået fra (2026) | 4 |
| **Eksekverbare i dag** | **82** (heraf 19 beregningsregler) |

## Regler pr. check-type (klassificeret)

| Kategori | Antal | Status |
|---|---|---|
| conditional | 64 | ✅ understøttet |
| other | 42 | 🔎 gennemgang |
| calculation | 25 | ✅ delvist (19 kodet) |
| compare | 15 | ✅ understøttet |
| required | 4 | ✅ understøttet |
| format | 3 | ✅ understøttet |
| unique | 3 | ✅ understøttet |
| value_range | 3 | ✅ understøttet |
| ref_integrity | 2 | ✅ understøttet |
| mutually_exclusive | 1 | ✅ understøttet |
| not_equal | 1 | ✅ understøttet |

## Motorens check-type-vokabular (13)

- `conditional` — if/then (element+attribut; in/equals/contains/absent/not_in…)
- `conditional_ref` — betinget reference-integritet (dokument-bredt)
- `compare` — dato/tal-ordning mellem to felter
- `format` — regex-format
- `value_range` — numerisk min/max/exclude
- `cardinality` — antalsbegrænsning
- `unique` — værdier skal være entydige
- `not_equal` — to felter må ikke være ens
- `mutually_exclusive` — værdimængder må ikke optræde sammen
- `ref_integrity` — værdi skal referere et kendt felt
- `required_if` — felt kræves under betingelse
- `forbidden_if` — felt forbudt under betingelse
- `calculation` — beregningsmotor: aritmetisk formel (beregnet vs. rapporteret)

## Eksekverbare regler i dag

| OECD# | Level | Type | Navn |
|---|---|---|---|
| 60007 | file | unique | DocRefId skal være unik |
| 60015 | file | required_if | CorrDocRefId kræves ved rettelse/sletning |
| 60012 | file | forbidden_if | CorrDocRefId må ikke angives ved ny data |
| 60004 | file | mutually_exclusive | Ny data og rettelser må ikke blandes |
| 60006 | file | unique | Samme dokument må ikke rettes/slettes to gange |
| 70001 | record | conditional | NOTIN-TIN skal udfyldes korrekt |
| 70002 | record | conditional | TIN='NOTIN' kræver TypeOfTIN=GIR3004 |
| 60020 | file | compare | Periodens startdato må ikke ligge efter slutdato |
| 60021 | file | compare | Periodens slutdato må ikke ligge efter rapporteringsperioden |
| 60023 | file | compare | FilingCE's land skal matche afsenderlandet |
| 70003 | record | conditional | Unknown-TIN skal udfyldes korrekt |
| 70005 | record | conditional | issuedBy kræves for almindelige TIN |
| 70013 | record | conditional | GIR313 og GIR314 udelukker hinanden (samme CE) |
| 70014 | record | conditional | GIR307 og GIR308 udelukker hinanden (samme CE) |
| 70018 | record | conditional | GIR305 og GIR306 udelukker hinanden (samme CE) |
| 70022 | record | compare | ChangeDate må ikke ligge før periodens start |
| 70023 | record | compare | ChangeDate må ikke ligge efter periodens slutning |
| 70044 | record | conditional | ETRStatus skal indeholde ETRException eller ETRComputation |
| 70073 | record | value_range | EndAmount må ikke være negativ |
| 70104 | record | value_range | UTPRTopUpTaxCarriedForward må ikke være negativ |
| 70123 | record | value_range | Additions må ikke være negativ |
| 70009 | record | conditional | Ugyldig GlobeStatus for UPE |
| 70010 | record | cardinality | UPE må kun have ét ResCountryCode |
| 70011 | record | cardinality | CE må kun have ét ResCountryCode |
| 70024 | record | conditional | PreOwnership må ikke udfyldes ved PreGlobeStatus GIR719 |
| 70032 | record | conditional | QIIR kræver CE-Rules GIR201 eller GIR202 |
| 70025 | record | conditional | Nominee-PreOwnership kræver NOTIN-TIN |
| 70029 | record | conditional_ref | Ownership-TIN (GIR801) skal matche en rapporteret enheds-TIN |
| 70030 | record | conditional_ref | Ownership-TIN (GIR802-804) skal matche en rapporteret enheds-TIN |
| 70086 | record | calculation | ExcessProfits-beregning |
| 70072 | record | calculation | EndAmount-beregning (DDT-recapture) |
| 70083 | record | calculation | ExcessNegTaxExpense/Remaining-beregning |
| 70105 | record | calculation | UTPRTopUpTaxCarriedForward-beregning |
| 60027 | file | calculation | IIR ParentEntity TopUpTax-beregning |
| 70076 | record | calculation | TransBlendCFC/Total-beregning |
| 70078 | record | calculation | BefRecastAdjust-beregning |
| 70079 | record | calculation | PreRecast-beregning |
| 70064 | record | calculation | DeferTaxAsset/Total-beregning |
| 70065 | record | calculation | CoveredTaxRefund/Total-beregning |
| 70108 | record | conditional | Basis kræver TaxRate |
| 70109 | record | conditional | Basis GIR1907 kræver IndOwners/ResCountryCode |
| 70110 | record | conditional | Basis GIR1903/1908 kræver IndOwners |
| 70111 | record | conditional | Basis GIR1904/1909 kræver EntityOwner/ExTypeOfEntity |
| 70112 | record | conditional | Basis GIR1904 udelukker ExTypeOfEntity GIR2805 |
| 70113 | record | conditional | Basis GIR1909 udelukker ExTypeOfEntity GIR2804 |
| 70060 | record | conditional | AdjustmentItem GIR2025 kræver IntShippingIncome |
| 70107 | record | conditional | Exception=TRUE udelukker CrossBorderAdjustments |
| 70082 | record | conditional | DeferredTaxAssets kræver Start eller Recast = 0 |
| 70045 | record | conditional | SafeHarbour GIR1203-1205 kræver TransitionalCbCRSafeHarbour |
| 70047 | record | conditional | SafeHarbour GIR1203 kræver Revenue |
| 70048 | record | conditional | SafeHarbour GIR1204 kræver IncomeTax |
| 70049 | record | conditional | SafeHarbour GIR1206 kræver UTPRSafeHarbour |
| 70051 | record | conditional | SafeHarbour GIR1208 kræver AggregateSimplified |
| 70041 | file | conditional | CFSofUPE GIR502/504 udelukker SafeHarbour GIR1207-1209 |
| 70016 | record | conditional | GlobeStatus GIR307 kræver GIR309 |
| 70017 | record | conditional | GlobeStatus GIR308 kræver GIR309 |
| 70026 | record | conditional | GlobeStatus GIR305 kræver 100% ejerskab |
| 70062 | record | conditional | AdjustmentItem GIR2720 udelukker negativ AdjustedCoveredTax |
| 70088 | record | conditional | Negativ NetGlobeIncome kræver Art4.1.5 |
| 70101 | record | conditional | Employees kræves når UTPRTopUpTaxCarryForward ≠ 0 |
| 70102 | record | conditional | TangibleAssetValue kræves når UTPRTopUpTaxCarryForward ≠ 0 |
| 70103 | record | conditional | UTPRPercentage skal være 0 når carryforward > 0 |
| 70115 | record | conditional | AdjustmentItem GIR2022/2023 kræver UPEAdjustments |
| 60028 | record | calculation | AdjustedFANIL/Total-beregning |
| 70074 | record | calculation | TotalDDT-beregning |
| 70077 | record | calculation | DeferTaxAdjustAmt/Total-beregning (Recast) |
| 70055 | record | calculation | OutstandingBalance-beregning |
| 70059 | record | unique_in | AdjustmentItem-kode kun én gang pr. ETR |
| 70067 | record | unique_in | AmountAttributed-år skal være unikke |
| 70090 | record | calculation | GlobeLoss skal svare til NetGlobeIncome/Total |
| 70124 | record | value_range | CrossAllocation/Reductions må ikke være positiv |
| 70021 | record | conditional | GlobeStatus GIR316/318 kræver OwnershipChange |
| 70066 | record | compare | DeferTaxAsset-år må ikke ligge efter periodens start |
| 70068 | record | compare | CoveredTaxRefund-år må ikke ligge efter periodens start |
| 70070 | record | compare | Recapture-år må ikke ligge efter periodens slut |
| 70093 | record | compare | NONArt4.1.5-år må ikke overstige periodens slut |
| 70015 | file | conditional | GIR308 kræver en tilsvarende GIR307-enhed |
| 70019 | file | conditional | GIR305 kræver en tilsvarende GIR306-enhed |
| 70087 | record | calculation | SubstanceExclusion/Total-beregning |
| 70091 | record | calculation | ExpectedAdjustedCoveredTax = GlobeLoss × 15% |
| 70097 | record | calculation | InclusionRatio-beregning |
| 70098 | record | calculation | TopUpTaxShare = TopUpTax × InclusionRatio |

## Slået fra for første filing-cyklus (juni-2026-guidance)

- **60025** (ETRRate): The ETRRate must be equal to the integer value reported at the AdjustedCoveredTax/Total element DIVI…
- **60026** (TopUpTax): TopUpTax must equal the following calculation: (TopUpTaxPercentage * ExcessProfits) + (NONArt.4.1.5/…
- **70028** (OwnershipPercentage): Unless the GloBEStatus contains the value of GIR318, then the OwnershipPercentage must not be 0%…
- **70092** (AdditionalTopUpTax): The AdditionalTopUpTax integer is equal to the following calculation: ExpectedAdjustedCoveredTax – A…
