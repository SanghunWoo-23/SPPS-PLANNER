"""Static desktop UI catalogs used by the accepted SPPS Planner layout."""
from __future__ import annotations

PLAN_COLUMNS = [
    "No", "Unit name", "Unit eq", "Unit amount(g)", "Unit volume(mL)",
    "Coupling reagent 1", "Coupling reagent 1 eq", "Coupling reagent 1 count",
    "Coupling reagent 2 / catalyst", "Coupling reagent 2 / catalyst eq",
    "Coupling reagent 2 / catalyst count", "Coupling base", "Coupling base eq",
    "Coupling base count", "Coupling cocktail solvent",
    "Coupling cocktail volume(mL)", "Deprotection base", "Deprotection ratio",
    "Deprotection count", "Solvent 1", "Solvent 1 count", "Solvent 2",
    "Solvent 2 count", "Repeat",
]

MATERIAL_COLUMNS = [
    "step", "material", "class", "MW", "planned_mmol", "planned_g",
    "planned_mL", "use_count", "repeat", "phase", "note", "source",
]

RESIN_VALUES = [
    "Amide", "Rink Amide", "Rink Amide AM", "Rink Amide MBHA",
    "Rink Amide ChemMatrix", "Rink Amide Tentagel", "Wang", "HMPB",
    "Sieber Amide", "PAL resin", "CTC/Trityl", "2-CTC", "2-CTC",
    "Trityl chloride resin", "Tentagel", "Manual",
]

REAGENT_VALUES = [
    "", "DIC", "DCC", "EDC", "EDC-HCl", "HBTU", "HATU", "HCTU", "TBTU",
    "TSTU", "TNTU", "PyBOP", "PyAOP", "BOP", "DEPBT", "COMU", "T3P",
    "DMTMM", "TFFH", "BTC", "CDI", "MSNT", "Ghosez reagent", "PyClocK",
    "PyBrOP", "Manual",
]

CATALYST_VALUES = [
    "", "HOBt", "HOBt hydrate", "Cl-HOBt", "6-Cl-HOBt", "HOAt", "Oxyma",
    "Oxyma Pure", "K-Oxyma", "Ethyl cyano(hydroxyimino)acetate", "DMAP",
    "NHS", "Sulfo-NHS", "HOSu", "HODhbt", "DHO", "HOOBt", "HOSBt",
    "CuCl", "CuBr", "Pd(PPh3)4", "Phenylsilane", "Manual",
]

BASE_VALUES = [
    "", "DIEA", "DIPEA", "NMM", "TEA", "Triethylamine", "Pyridine",
    "2,4,6-collidine", "2,6-lutidine", "DBU", "Piperidine", "TMP", "TBAF",
    "NaHCO3", "Na2CO3", "K2CO3", "NaOH", "KOH", "Manual",
]

DEPRO_VALUES = [
    "Piperidine", "20% Piperidine/DMF", "DBU", "Piperazine", "Morpholine",
    "4-methylpiperidine", "TFA", "Hydrazine", "Pd(PPh3)4", "Manual",
]

RATIO_VALUES = [
    "20% in DMF", "2% DBU + 2% piperidine in DMF",
    "20% piperidine + 0.1 M HOBt", "Manual",
]

SOLVENT_VALUES = [
    "", "DMF", "NMP", "DCM", "90% DCM / 10% DMF", "10% DMF/DCM",
    "DCM/DMF", "DMF/NMP", "MeOH", "EtOH", "i-PrOH", "IPA", "ACN", "MeCN",
    "THF", "DMSO", "TFA", "TIS", "EDT", "Water", "H2O", "Ether",
    "Diethyl ether", "MTBE", "Dioxane", "Toluene", "Hexane", "EtOAc",
    "Acetone", "CHCl3", "HFIP", "Manual",
]

UNIT_VALUES = [
    "", "A", "R", "N", "D", "C", "Q", "E", "G", "H", "I", "L", "K", "M",
    "F", "P", "S", "T", "W", "Y", "V", "D-Ala", "D-Arg", "D-Asn",
    "D-Asp", "D-Cys", "D-Gln", "D-Glu", "D-His", "D-Ile", "D-Leu",
    "D-Lys", "D-Phe", "D-Pro", "D-Ser", "D-Tyr", "D-Val", "Hyp", "Nle",
    "Nva", "Orn", "Dap", "Dab", "Aib", "Sar", "Bpa", "Cha", "Cit", "hArg",
    "hLys", "Pen", "Ac", "FITC", "Biotin", "Biotin-NHS", "Biotin acid",
    "FAM", "TAMRA", "CY3", "CY5", "CY7", "Dabcyl", "DOTA", "NOTA", "Pal",
    "Myr", "Gal", "Nic", "Caf", "Ahx", "AEEA", "PEG4", "PEG8", "bAla",
    "gAla", "His6", "FLAG", "HA", "Manual",
]

MW_FALLBACK = {
    "A": 311.29, "R": 648.77, "N": 596.67, "D": 411.45, "C": 585.72,
    "Q": 610.70, "E": 425.48, "G": 297.26, "H": 619.72, "I": 353.42,
    "L": 353.42, "K": 468.55, "M": 371.45, "F": 387.43, "P": 337.37,
    "S": 383.39, "T": 397.42, "W": 526.58, "Y": 459.50, "V": 339.39,
    "DIC": 126.20, "DCC": 206.33, "EDC": 191.70, "HBTU": 379.25,
    "HATU": 380.23, "HCTU": 413.69, "TBTU": 321.08, "PyBOP": 520.39,
    "PyAOP": 521.36, "BOP": 442.28, "COMU": 427.35, "T3P": 318.18,
    "DMTMM": 276.72, "TFFH": 226.19, "BTC": 296.75, "CDI": 162.15,
    "MSNT": 284.29, "HOBt": 135.13, "Cl-HOBt": 169.57,
    "6-Cl-HOBt": 169.57, "HOAt": 136.11, "Oxyma": 142.11,
    "Oxyma Pure": 142.11, "K-Oxyma": 180.20, "DMAP": 122.17,
    "NHS": 115.09, "Sulfo-NHS": 217.13, "HOSu": 115.09,
    "HODhbt": 151.12, "DHO": 151.12, "DIEA": 129.25, "DIPEA": 129.25,
    "NMM": 101.15, "TEA": 101.19, "Pyridine": 79.10,
    "2,4,6-collidine": 121.18, "2,6-lutidine": 107.16, "DBU": 152.24,
    "Piperidine": 85.15, "Piperazine": 86.14, "Morpholine": 87.12,
    "4-methylpiperidine": 99.18, "TMP": 141.25, "Ac2O": 102.09,
    "Acetic anhydride": 102.09, "AcOH": 60.05, "Acetic acid": 60.05,
    "DMF": 73.09, "NMP": 99.13, "DCM": 84.93, "MeOH": 32.04,
    "EtOH": 46.07, "i-PrOH": 60.10, "ACN": 41.05, "THF": 72.11,
    "DMSO": 78.13, "TFA": 114.02, "TIS": 158.36, "Water": 18.02,
    "Ether": 74.12, "Diethyl ether": 74.12, "MTBE": 88.15,
    "FITC": 389.38, "Biotin": 244.31, "Biotin-NHS": 341.38,
    "FAM": 376.32, "TAMRA": 430.45, "ROX": 534.56, "CY3": 766.90,
    "CY5": 792.99, "CY7": 818.03, "Dabcyl": 252.28, "BHQ1": 552.50,
    "BHQ2": 579.50, "DOTA": 404.42, "NOTA": 393.35, "Ahx": 131.17,
    "AEEA": 175.20, "PEG1": 149.15, "PEG3": 237.25, "PEG4": 281.30,
    "PEG6": 369.41, "PEG8": 457.52, "bAla": 89.09, "gAla": 103.12,
    "His6": 840.8, "His8": 1098.9, "His10": 1357.1, "FLAG": 1012.0,
    "HA": 1102.2, "Myc": 1203.3, "StrepII": 1010.1,
    "TwinStrep": 2300.6, "V5": 1421.5, "T7": 1315.4, "ALFA": 1583.8,
    "AviTag": 1622.8, "SpyTag": 1515.6, "Pal": 256.43,
    "Palmitic acid": 256.43, "Myr": 228.38, "Myristic acid": 228.38,
    "Nic": 123.11, "Nicotinic acid": 123.11, "Caf": 180.16,
    "Caffeic acid": 180.16, "Gal": 170.12, "Gallic acid": 170.12,
    "Stear": 284.48, "Stearic acid": 284.48,
}

LIQUID_DENSITY = {
    "DIC": 0.815, "AC2O": 1.08, "ACETIC ANHYDRIDE": 1.08, "ACOH": 1.05,
    "ACETIC ACID": 1.05, "DIEA": 0.742, "DIPEA": 0.742, "NMM": 0.92,
    "TEA": 0.726, "PYRIDINE": 0.982, "2,4,6-COLLIDINE": 0.917,
    "2,6-LUTIDINE": 0.925, "PIPERIDINE": 0.862, "DBU": 1.02,
    "DMF": 0.944, "NMP": 1.03, "DCM": 1.33, "MEOH": 0.792,
    "ETOH": 0.789, "I-PROH": 0.786, "ACN": 0.786, "THF": 0.889,
    "DMSO": 1.10, "TFA": 1.49, "TIS": 0.773, "WATER": 1.00,
    "ETHER": 0.713, "DIETHYL ETHER": 0.713, "MTBE": 0.740,
}

AA_LIKE_LINKER_TOKENS = {
    "AHX", "AEEA", "CHA", "AIB", "NLE", "ORN", "CIT", "HYP", "DAB", "NAL",
    "BALA", "B-ALA", "GABA", "PEG1", "PEG2", "PEG3", "PEG4", "PEG6",
    "PEG8", "PEG12", "PEG24", "G4S", "G4SX2", "SAR", "BA", "BETA-ALA",
}

CHEMICAL_LABEL_TOKENS = {
    "AC", "AC-", "ACETYL", "ACETYL CAP", "AC / ACETYL CAP", "FITC",
    "BIOTIN", "BIOTIN-NHS", "BIOTIN ACID", "BIOTINCAP", "FAM", "5-FAM",
    "6-FAM", "FAM-NHS", "TAMRA", "ROX", "CY3", "CY5", "CY5_5", "CY7",
    "DABCYL", "BHQ", "BHQ1", "BHQ2", "DOTA", "NOTA", "DFO", "NBD",
    "DANSYL", "BODIPY", "EDANS", "PAL", "PALMITIC ACID", "PALMITICACID",
    "PALMITOYL", "MYR", "MYRISTIC ACID", "MYRISTICACID", "MYRISTOYL",
    "STEAR", "STEARIC ACID", "STEARICACID", "OLE", "OLEIC ACID",
    "OLEICACID", "GAL", "GALLIC ACID", "GALLICACID", "GALLOYL", "NIC",
    "NICOTINIC ACID", "NICOTINICACID", "CAF", "CAFFEIC ACID",
    "CAFFEICACID", "CAFFEOYL", "MALEIMIDE", "NHS",
}

CHEMICAL_DISPLAY_NAMES = {
    "PAL": "Palmitic acid", "PALMITICACID": "Palmitic acid",
    "PALMITOYL": "Palmitic acid", "MYR": "Myristic acid",
    "MYRISTICACID": "Myristic acid", "MYRISTOYL": "Myristic acid",
    "GAL": "Gallic acid", "GALLICACID": "Gallic acid",
    "GALLOYL": "Gallic acid", "CAF": "Caffeic acid",
    "CAFFEICACID": "Caffeic acid", "CAFFEOYL": "Caffeic acid",
    "NIC": "Nicotinic acid", "NICOTINICACID": "Nicotinic acid",
    "NICOTINOYL": "Nicotinic acid", "STEAR": "Stearic acid",
    "STEARICACID": "Stearic acid", "STE": "Stearic acid",
    "OLE": "Oleic acid", "OLEICACID": "Oleic acid",
}
