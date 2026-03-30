import pandas as pd
from pathlib import Path
from rapidfuzz import process, fuzz

#  DIRECTORIES 
BASE_DIR = Path(__file__).resolve().parents[2]

RAW_DIR = BASE_DIR / "data/raw"
DISTRICT_DIR = RAW_DIR / "district_data"
EXTERNAL_DIR = BASE_DIR / "data/external"
PROCESSED_DIR = BASE_DIR / "data/processed"

# Create directories if they don't exist
RAW_DIR.mkdir(parents=True, exist_ok=True)
DISTRICT_DIR.mkdir(parents=True, exist_ok=True)
EXTERNAL_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# FILE PATHS 
MASTER_FILE = DISTRICT_DIR / "training_centres_all_states_clean.csv"
STATE_FOLDER = RAW_DIR  # Folder containing *_candidate_wise.csv
LGD_FILE = EXTERNAL_DIR / "LGD_Latest .csv"

MAPPED_OUTPUT = PROCESSED_DIR / "mapped.csv"
UNMAPPED_OUTPUT = PROCESSED_DIR / "unmapped.csv"



# DISTRICT OVERRIDES & MANUAL CODES
DISTRICT_NAME_OVERRIDE = {
    "y.s.r.": "y.s.r. kadapa", "anantapur": "ananthapuramu",
    "konaseema": "dr. b.r. ambedkar konaseema", "kamrup metropolitan": "kamrup metro",
    "dantewada": "dakshin bastar dantewada", "kabirdham": "kabeerdham",
    "chhota udaipur": "chhotaudepur", "punch": "poonch", "badgam": "budgam",
    "shupiyan": "shopian", "saraikela-kharsawan": "saraikela kharsawan",
    "mysore": "mysuru", "shimoga": "shivamogga", "bangalore rural": "bengaluru rural",
    "khargone": "khargone (west nimar)", "bid": "beed", "raigarh": "raigad",
    "ribhoi": "ri bhoi", "firozpur": "ferozepur", "dhaulpur": "dholpur",
    "yadadri": "yadadri bhuvanagiri", "garhwal": "pauri garhwal", "darjiling": "darjeeling",
}

MANUAL_DISTRICT_CODES = {
    "karimganj": 293, "balrampur": 649, "kanker": 381, "dohad": 676,
    "gurgaon": 62, "mewat": 604, "leh(ladakh)": 9, "kargil": 6,
    "purbi singhbhum": 327, "bangalore": 525, "gulbarga": 538, "bijapur": 530,
    "ramanagara": 631, "hoshangabad": 409, "khandwa": 405, "aurangabad": 469,
    "osmanabad": 488, "ahmadnagar": 466, "mumbai suburban": 483,
    "subarnapur": 372, "muktsar": 39, "mohali": 52,
    "sahibzada ajit singh nagar": 608, "east district": 225,
    "west district": 228, "south district": 227, "tuticorin": 100,
    "chennai": 568, "warangal urban": 686, "medchal": 700,
    "warangal rural": 522, "sant ravidas nagar (bhadohi)": 179,
    "kolkata": 315, "medinipur east": 317, "south andaman": 602,
    "morigaon": 296, "purba champaran": 213, "raigad": 386, "gariaband": 645,
    "ahmadabad": 438, "devbhoomi dwarka": 674, "dang": 444, "aravalli": 672,
    "baramula": 3, "bandipore": 623, "kodarma": 334, "chikkballapura": 630,
    "tumkur": 548, "chikmagalur": 532, "bagalkot": 524, "agar malwa": 667,
    "buldana": 472, "jajapur": 356, "anugul": 344, "nabarangapur": 366,
    "jhunjhunun": 106, "chittaurgarh": 95, "jalor": 104, "rangareddi": 518,
    "mahbubnagar": 512, "jayashankar bhupalpalle": 687,
    "komaram bheem asifabad": 699, "hardwar": 50, "24 paraganas north": 303,
    "24 paraganas south": 304, "puruliya": 321, "maldah": 316,
}

#  HELPERS
def norm(x):
    return str(x).strip().lower().replace("&", "and") if pd.notna(x) else ""

def clean_col(c):
    return c.strip().lower().replace(" ", "_").replace("(", "").replace(")", "").replace(".", "")

def reorder_columns(df, order):
    present = [c for c in order if c in df.columns]
    remaining = [c for c in df.columns if c not in present]
    return df[present + remaining]

def apply_district_override(x):
    return DISTRICT_NAME_OVERRIDE.get(norm(x), norm(x))

def lgd_partial_ratio_match(row, lgd_df, threshold=85):
    if not row["n_district"]:
        return pd.NA
    choices = lgd_df[lgd_df["n_state"] == row["n_state"]]
    if choices.empty:
        return pd.NA
    match = process.extractOne(row["n_district"], choices["n_district"], scorer=fuzz.partial_ratio)
    if match and match[1] >= threshold:
        return choices[choices["n_district"] == match[0]]["district_code"].iloc[0]
    return pd.NA

YES_NO_COLS = [
    "candidateenrolled","candidatefreezed","trained","dropout",
    "undergoing","assessed","writeoff","certified","placed","appointed",
    "monthly_continuitymin_3_months"
]

UNIQUE_COUNT_COLS = [
    "sanction_order","pia","tc_name","tc_id",
    "training_centre_district","training_centre_address","batch","batch_code"
]

def add_grand_total(df):
    total = {}
    for c in df.columns:
        if c in YES_NO_COLS:
            total[c] = df[c].astype("string").str.lower().eq("yes").sum()
        elif c in UNIQUE_COUNT_COLS or c == "name":
            total[c] = df[c].nunique(dropna=True)
        else:
            total[c] = pd.NA
    total["statename"] = "Grand Total"
    return pd.concat([df, pd.DataFrame([total])], ignore_index=True)

#  LOAD MASTER
df_master = pd.read_csv(MASTER_FILE)
df_master.columns = df_master.columns.str.strip()
df_master["TC ID"] = df_master["TC ID"].astype(str)
df_master["n_pia"] = df_master["PIA Name"].apply(norm)
df_master["n_tc"] = df_master["Training Centre Name"].apply(norm)
df_master["n_state"] = df_master["Training Centre State"].apply(norm)
df_master = df_master.drop_duplicates(subset=["TC ID","n_pia","n_tc","n_state"])
df_master_reduced = df_master[["TC ID","n_pia","n_tc","n_state","Training Centre District","Training Centre Address"]]

#  PROCESS STATE FILES 
mapped_all, unmapped_all = [], []

for f in Path(STATE_FOLDER).glob("*_candidate_wise.csv"):
    df = pd.read_csv(f)
    df.columns = df.columns.str.strip()
    df["TC ID"] = df["TC ID"].astype(str)
    df["n_pia"] = df["PIA"].apply(norm)
    df["n_tc"] = df["TC Name"].apply(norm)
    df["n_state"] = df["StateName"].apply(norm)

    # Drop unwanted columns
    for col in ["S.No.", "Monthly Continuity (min. 3 months)", "Monthly Continuity"]:
        if col in df.columns:
            df.drop(columns=[col], inplace=True)

    merged = df.merge(df_master_reduced, on=["TC ID","n_pia","n_tc","n_state"], how="left", indicator=True)
    mapped = merged[merged["_merge"]=="both"].copy()
    unmapped = merged[merged["_merge"]!="both"].copy()

    mapped.drop(columns=["_merge","n_pia","n_tc","n_state"], inplace=True)
    unmapped.drop(columns=["_merge","n_pia","n_tc","n_state"], inplace=True)

    mapped.columns = [clean_col(c) for c in mapped.columns]
    unmapped.columns = [clean_col(c) for c in unmapped.columns]

    mapped_all.append(mapped.drop_duplicates())
    unmapped_all.append(unmapped.drop_duplicates())

mapped_df = pd.concat(mapped_all, ignore_index=True)
unmapped_df = pd.concat(unmapped_all, ignore_index=True)

# LGD PREP 
lgd = pd.read_csv(LGD_FILE)
lgd["n_state"] = lgd["State Name (In English)"].apply(norm)
lgd["n_district"] = lgd["District Name  (In English)"].apply(norm)
lgd = lgd[["n_state","n_district","State Code","District Code"]].drop_duplicates().rename(
    columns={"State Code":"state_code","District Code":"district_code"}
)
# MAPPED DF 
mapped_df["n_state"] = mapped_df["statename"].apply(norm)
mapped_df["n_district"] = mapped_df["training_centre_district"].apply(apply_district_override)

# Map state and district
mapped_df = mapped_df.merge(lgd[['n_state','state_code']].drop_duplicates('n_state'), on='n_state', how='left')
mapped_df = mapped_df.merge(lgd[['n_state','n_district','district_code']], on=['n_state','n_district'], how='left')

mapped_df["district_code"] = mapped_df["district_code"].astype("Int64")
# Partial match fallback
mask = mapped_df["district_code"].isna()
mapped_df.loc[mask, "district_code"] = mapped_df[mask].apply(lgd_partial_ratio_match, axis=1, lgd_df=lgd)
mapped_df["district_code"] = mapped_df["district_code"].astype("Int64")


# Manual fallback
mapped_df.loc[mapped_df["district_code"].isna(), "district_code"] = mapped_df["n_district"].map(MANUAL_DISTRICT_CODES)

mapped_df.drop(columns=["n_state","n_district"], errors='ignore', inplace=True)

#  UNMAPPED DF 
unmapped_df["n_state"] = unmapped_df["statename"].apply(norm)
unmapped_df = unmapped_df.merge(lgd[['n_state','state_code']].drop_duplicates('n_state'), on='n_state', how='left')
unmapped_df.drop(columns=["n_state"], errors='ignore', inplace=True)

#  FORMAT, GRAND TOTAL & COLUMN ORDER 
TITLE_CASE_COLS = ["statename","pia","tc_name","training_centre_district","training_centre_address",
                   "batch","name","gender","industryname","work_placename","employername"]

for df in (mapped_df, unmapped_df):
    for c in TITLE_CASE_COLS:
        if c in df.columns:
            df[c] = df[c].astype("string").str.title()
    for c in YES_NO_COLS:
        if c in df.columns:
            df[c] = df[c].astype("string").str.lower().str.capitalize()

mapped_df = add_grand_total(mapped_df)
unmapped_df = add_grand_total(unmapped_df)

FINAL_COLUMN_ORDER = [
    "statename","state_code","sanction_order","pia","tc_name","tc_id",
    "training_centre_district","district_code","batch","batch_code","batch_start_date","batch_end_date",
    "name","gender","candidateenrolled","candidatefreezed","trained","dropout",
    "undergoing","assessed","writeoff","certified","placed","appointed","monthly_continuitymin_3_months","joining_date",
    "industryname","work_placename","employername","training_centre_address"
]

mapped_df = reorder_columns(mapped_df, FINAL_COLUMN_ORDER)
unmapped_df = reorder_columns(unmapped_df, FINAL_COLUMN_ORDER)

# SAVE 
mapped_df.to_csv(MAPPED_OUTPUT, index=False)
unmapped_df.to_csv(UNMAPPED_OUTPUT, index=False)

print("saved")
