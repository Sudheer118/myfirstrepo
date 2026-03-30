# This script maps the data with Lgd codes 
import pandas as pd
import numpy as np
from pathlib import Path
from rapidfuzz import process, fuzz


# PATHS

BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_CSV  = BASE_DIR / "data/processed/processed_all_years.csv"
LGD_CSV    = BASE_DIR / "data/external/LGD_Latest 1.csv"
AGRI_CSV   = BASE_DIR / "data/external/agri_wages_08_06_2022.csv"
OUTPUT_CSV = BASE_DIR / "data/processed/Mapped_final_data.csv"


# NORMALIZATION

def norm(x):
    if pd.isna(x):
        return ""
    return (
        str(x).lower()
        .replace("&", "and")
        .replace("-", " ")
        .replace(".", "")
        .strip()
    )


# DISTRICT RENAME MAP

district_rename_map = {
    "karimganj": "sribhumi",
    "dohad": "dahod",
    "mewat": "nuh",
    "gulbarga": "kalaburagi",
    "ramanagara": "bengaluru south",
    "hoshangabad": "narmadapuram",
    "nawanshahr": "shahid bhagat singh nagar",
    "allahabad": "prayagraj",
    "faizabad": "ayodhya",
    "sant ravidas nagar": "bhadohi",
    "24 paraganas south": "south 24 parganas",
    "dinajpur dakshin": "dakshin dinajpur",
    "dinajpur uttar": "uttar dinajpur",
    "medinipur east": "purba medinipur",
    "medinipur west": "paschim medinipur",
    "osmanabad": "dharashiv"
}


# READ FILES

final_df = pd.read_csv(INPUT_CSV, dtype=str)
lgd_df   = pd.read_csv(LGD_CSV, header=1, dtype=str)
agri_df  = pd.read_csv(AGRI_CSV, dtype=str)


# NORMALIZE FINAL DATA

final_df["state_norm"]    = final_df["state"].apply(norm)
final_df["district_norm"] = final_df["district"].apply(norm)
final_df["center_norm"]   = final_df["center"].apply(norm)

final_df["district_norm"] = final_df["district_norm"].replace(district_rename_map)

# NORMALIZE LGD

lgd_df["state_norm"]    = lgd_df["State Name (In English)"].apply(norm)
lgd_df["district_norm"] = lgd_df["District Name  (In English)"].apply(norm)

lgd_states = lgd_df[["state_norm", "State Code"]].drop_duplicates("state_norm")
lgd_districts = lgd_df[
    ["state_norm", "district_norm", "District Code"]
].drop_duplicates(["state_norm", "district_norm"])

state_lookup = dict(zip(lgd_states["state_norm"], lgd_states["State Code"]))

district_lookup = {}
for _, r in lgd_districts.iterrows():
    district_lookup.setdefault(r["state_norm"], {})[r["district_norm"]] = r["District Code"]


# FUZZY LGD FUNCTIONS

def fuzzy_state(x):
    if x in state_lookup:
        return state_lookup[x]
    m = process.extractOne(x, state_lookup.keys(), scorer=fuzz.partial_ratio)
    return state_lookup[m[0]] if m else np.nan

def fuzzy_district(s, d):
    if s not in district_lookup:
        return np.nan
    districts = district_lookup[s]
    if d in districts:
        return districts[d]
    m = process.extractOne(d, districts.keys(), scorer=fuzz.partial_ratio)
    return districts[m[0]] if m else np.nan


# APPLY LGD MATCH

keys = final_df[["state_norm", "district_norm"]].drop_duplicates()

keys["state_code"] = keys["state_norm"].apply(fuzzy_state)
keys["district_code"] = keys.apply(
    lambda r: fuzzy_district(r["state_norm"], r["district_norm"]),
    axis=1
)

final_df = final_df.merge(
    keys,
    on=["state_norm", "district_norm"],
    how="left"
)


# AGRI CENTER LOOKUPS 

agri_df["state_norm"]    = agri_df["state_name"].apply(norm)
agri_df["district_norm"] = agri_df["district_name"].apply(norm)
agri_df["center_norm"]   = agri_df["center_name"].apply(norm)

center_lookup_sd = {}
center_lookup_s  = {}

for _, r in agri_df.iterrows():
    center_lookup_sd.setdefault(
        (r["state_norm"], r["district_norm"]), {}
    )[r["center_norm"]] = (
        r["center_code"],
        r["center_lat"],
        r["center_long"]
    )

    center_lookup_s.setdefault(
        r["state_norm"], {}
    )[r["center_norm"]] = (
        r["center_code"],
        r["center_lat"],
        r["center_long"]
    )


# FUZZY CENTER MATCH

def fuzzy_center(s, d, c):
    centers = center_lookup_sd.get((s, d))
    if centers:
        if c in centers:
            return centers[c]
        m = process.extractOne(c, centers.keys(), scorer=fuzz.partial_ratio)
        if m:
            return centers[m[0]]

    centers = center_lookup_s.get(s)
    if centers:
        if c in centers:
            return centers[c]
        m = process.extractOne(c, centers.keys(), scorer=fuzz.partial_ratio)
        if m:
            return centers[m[0]]

    return np.nan, np.nan, np.nan


# APPLY CENTER MATCH

center_keys = final_df[
    ["state_norm", "district_norm", "center_norm"]
].drop_duplicates()

center_keys[["center_code", "center_lat", "center_long"]] = center_keys.apply(
    lambda r: pd.Series(
        fuzzy_center(
            r["state_norm"],
            r["district_norm"],
            r["center_norm"]
        )
    ),
    axis=1
)

final_df = final_df.merge(
    center_keys,
    on=["state_norm", "district_norm", "center_norm"],
    how="left"
)


# CLEANUP & REORDER

final_df.drop(
    columns=["state_norm", "district_norm", "center_norm"],
    inplace=True
)
final_df = final_df.rename(columns={
    "state": "state_name",
    "district": "district_name",
    "center": "center_name",
    "gen": "gender",
    "annual_average":"annual_average_wage"
})

final_df = final_df[
    [
        "month",
        "state_name", "state_code",
        "district_name", "district_code",
        "center_name", "center_code",
        "center_lat","center_long",
        "labour_category",
        "labour_type",
        "gender",
        "monthly_average_wage",
        "annual_average_wage",
    ]
]

wage_cols = ["monthly_average_wage", "annual_average_wage"]

# replace "-" only in wage columns
final_df[wage_cols] = final_df[wage_cols].replace("-", np.nan)

# replace empty strings in all columns
final_df = final_df.replace("", np.nan)
# SAVE

#final_df.to_csv(OUTPUT_CSV, index=False)
agri_df.drop(
    columns=["state_norm", "district_norm", "center_norm"],
    inplace=True
)
agri_df= pd.concat([agri_df, final_df], ignore_index= True)
agri_df.to_csv(OUTPUT_CSV, index =False)

print("LGD + AGRI center matching completed")
print("Output:", OUTPUT_CSV)
