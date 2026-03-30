
import re
from difflib import get_close_matches
from pathlib import Path

import pandas as pd

STATE_NAMES = [
    "Andhra Pradesh",
    "Arunachal Pradesh",
    "Assam",
    "Bihar",
    "Chhattisgarh",
    "Delhi",
    "Goa",
    "Gujarat",
    "Haryana",
    "Himachal Pradesh",
    "Jammu & Kashmir",
    "Jharkhand",
    "Karnataka",
    "Kerala",
    "Madhya Pradesh",
    "Maharashtra",
    "Manipur",
    "Meghalaya",
    "Mizoram",
    "Nagaland",
    "Odisha",
    "Punjab",
    "Rajasthan",
    "Sikkim",
    "Tamil Nadu",
    "Telangana",
    "Tripura",
    "Uttarakhand",
    "Uttar Pradesh",
    "West Bengal",
    "A & N Islands",
    "Chandigarh",
    "Dadra & Nagar Haveli",
    "Daman & Diu",
    "Lakshadweep",
    "Puducherry",
    "all-India",
    "Ladakh",
    "Dadra & Nagar Haveli & Daman & Diu",
]


def convert_data_to_title_case(df: pd.DataFrame) -> pd.DataFrame:
    df_copy = df.copy()
    for col in df_copy.select_dtypes(include=["object"]).columns:
        df_copy[col] = (
            df_copy[col]
            .astype(str)
            .apply(
                lambda x: (
                    x.title()
                    if x.strip().lower() not in ["nan", "none", ""]
                    else x
                )
            )
        )
    return df_copy


def normalize_state_name(value, state_list=STATE_NAMES):
    if pd.isna(value):
        return value
    value_clean = str(value).strip().replace(" ", "").lower()
    candidates = {s: s.replace(" ", "").lower() for s in state_list}

    matches = get_close_matches(
        value_clean, candidates.values(), n=1, cutoff=0.6
    )
    if matches:
        for s, norm in candidates.items():
            if norm == matches[0]:
                return s
    return value


def normalize_state_column(df, col_name="state_name"):
    df[col_name] = df[col_name].apply(normalize_state_name)
    return df


def extract_sector_gender(text):
    clean = str(text).lower().replace("\n", " ")
    clean = re.sub(r"\s+", " ", clean).strip()
    clean = clean.replace("rural + urban", "rural+urban")
    tokens = clean.split()

    sector, gender = None, None
    sectors = {"rural", "urban", "rural+urban", "total"}
    genders = {
        "male": "male",
        "female": "female",
        "persons": "total",
        "person": "total",
    }

    for i, tok in enumerate(tokens):
        if tok in sectors:
            sector = "total" if tok in ["rural+urban", "total"] else tok
            if i + 1 < len(tokens):
                nxt = tokens[i + 1]
                if nxt in genders:
                    gender = genders[nxt]
            break
    return sector, gender


def add_sector_gender_columns(df, text_col=0):
    df = df.copy()
    df.insert(1, "sector", None)
    df.insert(2, "gender", None)

    current_sector = None
    current_gender = None
    for idx, val in df[text_col].astype(str).items():
        sec, gen = extract_sector_gender(val)
        if sec:
            current_sector = sec
        if gen:
            current_gender = gen
        df.at[idx, "sector"] = current_sector
        df.at[idx, "gender"] = current_gender
    return df


def has_long_run_of_100(series, threshold=10):
    count = 0
    for val in series:
        try:
            v = float(str(val).strip())
        except ValueError:
            v = None
        if v == 100:
            count += 1
            if count > threshold:
                return True
        else:
            count = 0
    return False


def drop_cols_after_all_incl(df):
    df = df.copy()
    cols_to_keep = []

    for i, col in enumerate(df.columns):
        col_values = df[col].astype(str).str.strip().str.lower()
        if col_values.str.contains(r"all\s*\(incl", regex=True).any():
            break
        if col_values.eq("all").any():
            if (
                i > 0
                and df[df.columns[i - 1]]
                .astype(str)
                .str.strip()
                .str.contains("90-100")
                .any()
            ):
                cols_to_keep.append(col)
                continue
            break
        if has_long_run_of_100(df[col], threshold=10):
            break
        cols_to_keep.append(col)
    return df[cols_to_keep]


def drop_unwanted_rows_first_col(df):
    df = df.copy()
    first_col = df.columns[0]
    col_data = df[first_col].fillna("").astype(str).str.strip().str.lower()
    pattern = r"(?i)(^\s*$|^-1$|^\(1\)$|^state/ut$|state|sample|table|estd|estimated|\* in the enterprise|note[:\s]*\*[:\s]*self[-\s]*employed\s*workers|note:\s*for\s*chandigarh)"
    mask = ~col_data.str.contains(pattern, regex=True)
    return df[mask]


def process_table_folder(table_folder, year):
    table_folder = Path(table_folder)
    file_order = ["rural.csv", "urban.csv", "total.csv"]
    processed_dfs = []

    for file_name in file_order:
        file_path = table_folder / file_name
        if not file_path.exists():
            continue

        df = pd.read_csv(file_path, header=None)
        df = add_sector_gender_columns(df)
        df = drop_cols_after_all_incl(df)
        df = drop_unwanted_rows_first_col(df)
        df.insert(0, "year", year)

        df = df.rename(columns={df.columns[1]: "state_name"})
        df = normalize_state_column(df, "state_name")

        processed_dfs.append(df)

    if processed_dfs:
        final_df = pd.concat(processed_dfs, ignore_index=True)
        return final_df
    else:
        return pd.DataFrame()


#  Other.csv
def get_table_indices(df):
    table_mask = df[0].astype(str).str.lower().str.startswith("table")
    return df.index[table_mask].tolist() + [len(df)]


def get_state_order(df, table_indices):
    first_table_start, first_table_end = table_indices[0], table_indices[1]
    state_block = df.iloc[first_table_start + 1 : first_table_end].copy()
    pattern = (
        r"(?i)"
        r"^\(1\)$|^1$|^-1$|^state/ut$|state|sample|estimated|"
        r"^note[^a-zA-Z0-9]*for[^a-zA-Z0-9]*chandigarh|"
        r"^note.*chandigarh.*survey|\bsurvey\b"
    )
    state_block = state_block[
        ~state_block[0].astype(str).str.lower().str.contains(pattern)
    ]
    state_block = state_block[state_block[0].notna()]
    state_block[0] = state_block[0].apply(normalize_state_name)
    return state_block[0].tolist()


def reshape_tables(df, table_indices, state_order, year):
    sector_list = ["rural", "urban", "total"]
    gender_list = ["male", "female", "total"]
    sector_cols = {
        "rural": range(1, 4),
        "urban": range(4, 7),
        "total": range(7, 10),
    }
    all_tables = []
    pattern = (
        r"(?i)"
        r"^\(1\)$|^1$|^-1$|^state/ut$|state|sample|estimated|"
        r"^note[^a-zA-Z0-9]*for[^a-zA-Z0-9]*chandigarh|"
        r"^note.*chandigarh.*survey|\bsurvey\b"
    )

    for i in range(len(table_indices) - 1):
        start, end = table_indices[i], table_indices[i + 1]
        table_name = f"table_{i + 1}"
        block = df.iloc[start + 1 : end].copy()
        block = block[block[0].notna()]
        block = block[~block[0].astype(str).str.lower().str.contains(pattern)]
        block[0] = block[0].apply(normalize_state_name)

        long_rows = []
        for sector in sector_list:
            for gender, col_idx in zip(gender_list, sector_cols[sector]):
                for state in state_order:
                    if state not in block[0].values:
                        val = pd.NA
                    else:
                        val = block[block[0] == state].iloc[0, col_idx]
                    long_rows.append(
                        {
                            "year": year,
                            "state_name": state,
                            "sector": sector,
                            "gender": gender,
                            table_name: val,
                        }
                    )
        table_df = pd.DataFrame(long_rows)

        all_tables.append(table_df)

    final_df = all_tables[0]
    for tdf in all_tables[1:]:
        final_df = pd.merge(
            final_df,
            tdf,
            on=["year", "state_name", "sector", "gender"],
            how="outer",
        )

    final_df["state_name"] = pd.Categorical(
        final_df["state_name"], categories=state_order, ordered=True
    )
    final_df["sector"] = pd.Categorical(
        final_df["sector"],
        categories=["rural", "urban", "total"],
        ordered=True,
    )
    final_df["gender"] = pd.Categorical(
        final_df["gender"],
        categories=["male", "female", "total"],
        ordered=True,
    )

    return final_df.sort_values(
        ["sector", "gender", "state_name"]
    ).reset_index(drop=True)


def process_code2_file(file_path, year):
    df = pd.read_csv(file_path, header=None)
    table_indices = get_table_indices(df)
    state_order = get_state_order(df, table_indices)
    return reshape_tables(df, table_indices, state_order, year)


TABLE_NAME_PATTERNS = {
    r"general[_\s]*educational[_\s]*level": [
        "gen_edu_not_lit",
        "gen_edu_primary",
        "gen_edu_middle",
        "gen_edu_secondary",
        "gen_edu_higher_secondary",
        "gen_edu_dip_cert",
        "gen_edu_grad",
        "gen_edu_post_grad_above",
        "gen_edu_secondary_above",
    ],
    r"broad[_\s]*status[_\s]*employment": [
        "usual_self_own_account",
        "usual_self_helper",
        "usual_self_all",
        "usual_wage_salary",
        "usual_casual_labour",
    ],
    r"labour[_\s]*force[_\s]*participation[_\s]*rate": [
        "lfpr_not_lit",
        "lfpr_primary",
        "lfpr_middle",
        "lfpr_secondary",
        "lfpr_higher_secondary",
        "lfpr_dip_cert",
        "lfpr_grad",
        "lfpr_post_grad",
        "lfpr_secondary_above",
    ],
    r"worker[_\s]*population[_\s]*ratio": [
        "wpr_not_lit",
        "wpr_primary",
        "wpr_middle",
        "wpr_secondary",
        "wpr_higher_secondary",
        "wpr_dip_cert",
        "wpr_grad",
        "wpr_post_grad",
        "wpr_secondary_above",
    ],
    r"unemployment[_\s]*rate": [
        "ur_not_lit",
        "ur_primary",
        "ur_middle",
        "ur_secondary",
        "ur_higher_secondary",
        "ur_dip_cert",
        "ur_grad",
        "ur_post_grad",
        "ur_secondary_above",
    ],
    r"industry[_\s]*of[_\s]*work": [
        "indus_agri_forest_fish",
        "indus_mining_quarry",
        "indus_manufac",
        "indus_elec_gas_ac_supply",
        "indus_water_sewer_waste_manage",
        "indus_cons",
        "indus_wholesale_retail_repair",
        "indus_transport_stor",
        "indus_acco_food",
        "indus_infor_comm",
        "indus_finan_insurance",
        "indus_real_estate",
        "indus_prof_scientific_tech",
        "indus_admin_support_services",
        "indus_pub_admin_defence",
        "indus_edu",
        "indus_human_social_work",
        "indus_art_entertain_rec",
        "indus_oth_service",
        "indus_hhs_as_employers",
        "indus_extraterritorial_org",
    ],
    r"lfpr[_\s]*decile": [
        "lfpr_usual_mpce_0-10",
        "lfpr_usual_mpce_10-20",
        "lfpr_usual_mpce_20-30",
        "lfpr_usual_mpce_30-40",
        "lfpr_usual_mpce_40-50",
        "lfpr_usual_mpce_50-60",
        "lfpr_usual_mpce_60-70",
        "lfpr_usual_mpce_70-80",
        "lfpr_usual_mpce_80-90",
        "lfpr_usual_mpce_90-100",
        "lfpr_usual_mpce_all",
    ],
    r"wpr[_\s]*decile": [
        "wpr_usual_mpce_0-10",
        "wpr_usual_mpce_10-20",
        "wpr_usual_mpce_20-30",
        "wpr_usual_mpce_30-40",
        "wpr_usual_mpce_40-50",
        "wpr_usual_mpce_50-60",
        "wpr_usual_mpce_60-70",
        "wpr_usual_mpce_70-80",
        "wpr_usual_mpce_80-90",
        "wpr_usual_mpce_90-100",
        "wpr_usual_mpce_all",
    ],
    r"ur[_\s]*decile": [
        "ur_usual_mpce_0-10",
        "ur_usual_mpce_10-20",
        "ur_usual_mpce_20-30",
        "ur_usual_mpce_30-40",
        "ur_usual_mpce_40-50",
        "ur_usual_mpce_50-60",
        "ur_usual_mpce_60-70",
        "ur_usual_mpce_70-80",
        "ur_usual_mpce_80-90",
        "ur_usual_mpce_90-100",
        "ur_usual_mpce_all",
    ],
    r"cws[_\s]*broad[_\s]*status": [
        "cws_self_own_account",
        "cws_self_helper",
        "cws_self_all",
        "cws_wage_salary",
        "cws_casual_labour",
    ],
    r"industry[_\s]*enterprise[_\s]*type": [
        "enterprise_proprietary_partner",
        "enterprise_govt_local_public",
        "enterprise_autonomous",
        "enterpirse_pub_pvt_ltd",
        "enterprise_cooeprative",
        "enterprise_trust_nonprofit",
        "enterprise_emp_hhs",
        "enterprise_oth",
    ],
    r"average[_\s]*regular[_\s]*wage": [
        "wage_salary_july-sep",
        "wage_salary_oct-dec",
        "wage_salary_jan-march",
        "wage_salary_apr-june",
    ],
    r"average[_\s]*casual[_\s]*wage": [
        "wage_casual_july-sep",
        "wage_casual_oct-dec",
        "wage_casual_jan-march",
        "wage_casual_apr-june",
    ],
    r"self[_\s]*employed": [
        "earning_self_july-sep",
        "earning_self_oct-dec",
        "earning_self_jan-march",
        "earning_self_apr-june",
    ],
    r"lfpr[_\s]*cws": ["lfpr_cws_15_above"],
    r"wpr[_\s]*cws": ["wpr_cws_15_above"],
    r"lfpr[_\s]*usual[_\s]*state": [
        "lfpr_usual_age_15-29",
        "lfpr_usual_age_15-59",
        "lfpr_usual_age_15_above",
        "lfpr_usual_all",
    ],
    r"wpr[_\s]*usual[_\s]*state": [
        "wpr_usual_age_15-29",
        "wpr_usual_age_15-59",
        "wpr_usual_age_15_above",
        "wpr_usual_all",
    ],
    r"ur[_\s]*usual[_\s]*state": [
        "ur_usual_age_15-29",
        "ur_usual_age_15-59",
        "ur_usual_age_15_above",
        "ur_usual_all",
    ],
}

# hours quarters
HRS_QUARTERS = {
    "july-sep": [
        f"hrs_cws_july-sep_{r}"
        for r in [
            "0-12",
            "12-24",
            "24-36",
            "36-48",
            "48-60",
            "60-72",
            "72-84",
            "84above",
        ]
    ],
    "oct-dec": [
        f"hrs_cws_oct-dec_{r}"
        for r in [
            "0-12",
            "12-24",
            "24-36",
            "36-48",
            "48-60",
            "60-72",
            "72-84",
            "84above",
        ]
    ],
    "jan-march": [
        f"hrs_cws_jan-march_{r}"
        for r in [
            "0-12",
            "12-24",
            "24-36",
            "36-48",
            "48-60",
            "60-72",
            "72-84",
            "84above",
        ]
    ],
    "apr-june": [
        f"hrs_cws_apr-june_{r}"
        for r in [
            "0-12",
            "12-24",
            "24-36",
            "36-48",
            "48-60",
            "60-72",
            "72-84",
            "84above",
        ]
    ],
}


def get_hours_cols_for_folder(name):
    n = name.lower()
    if any(k in n for k in ["jul", "july", "jul-sep", "july-sep"]):
        return HRS_QUARTERS["july-sep"]
    if any(k in n for k in ["oct", "oct-dec", "oct_dec"]):
        return HRS_QUARTERS["oct-dec"]
    if any(
        k in n
        for k in ["jan", "jan-mar", "jan-mar", "jan-mar-ch", "jan-march"]
    ):
        return HRS_QUARTERS["jan-march"]
    if any(k in n for k in ["apr", "apr-jun", "apr-june"]):
        return HRS_QUARTERS["apr-june"]
    return []


def map_folder_to_cols(folder_name):

    hrs = get_hours_cols_for_folder(folder_name)
    if hrs:
        return hrs

    for pat, cols in TABLE_NAME_PATTERNS.items():
        if re.search(pat, folder_name, re.I):
            return cols
    return None


def find_child_folder(parent: Path, target_key: str):
    target_key = target_key.strip().lower()

    def norm(s):
        return re.sub(r"[^a-z0-9]", "", s.lower())

    tnorm = norm(target_key)

    p = parent / target_key
    if p.exists() and p.is_dir():
        return p

    for child in parent.iterdir():
        if not child.is_dir():
            continue
        cn = norm(child.name)
        if cn == tnorm or tnorm in cn or cn in tnorm:
            return child

    target_pattern = re.sub(r"[_\s]+", ".*", re.escape(target_key))
    for child in parent.iterdir():
        if not child.is_dir():
            continue
        if re.search(target_pattern, child.name, re.I):
            return child

    return None


KEY_COLS = ["year", "state_name", "sector", "gender"]


def get_ordered_folders(parent_folder, fixed_folders):
    parent_folder = Path(parent_folder)
    all_folders_ordered = list(fixed_folders)

    quarter_order = ["jul-sep", "oct-dec", "jan-mar", "apr-jun"]

    hw_folders = [
        p for p in parent_folder.glob("hours_worked_*") if p.is_dir()
    ]

    def get_quarter_index(name):
        lname = name.lower()
        for i, q in enumerate(quarter_order):
            if q in lname:
                return i
        return len(quarter_order)

    hw_matches = sorted([p.name for p in hw_folders], key=get_quarter_index)

    all_folders_ordered.extend(hw_matches)

    print("Processing in this order (keys/actual names may differ on disk):")
    print(all_folders_ordered)
    return all_folders_ordered


def resolve_main_folder(parent_folder, folder_key):
    main_folder = parent_folder / folder_key
    if not (main_folder.exists() and main_folder.is_dir()):
        main_folder = find_child_folder(parent_folder, folder_key)
    return main_folder


def get_nested_table_folder(main_folder):
    nested_folders = [f for f in main_folder.iterdir() if f.is_dir()]
    if nested_folders:
        return nested_folders[0]
    return None


def load_folder_csv(table_folder, year_val):
    csv_map = {p.name.lower(): p for p in table_folder.glob("*.csv")}
    df = pd.DataFrame()

    # Case 1: regular rural/urban/total files
    if any(k in csv_map for k in ["rural.csv", "urban.csv", "total.csv"]):
        df = process_table_folder(table_folder, year_val)

    # Case 2: other.csv
    elif "other.csv" in csv_map:
        file_path = csv_map["other.csv"]

        try:
            file_text = " ".join(
                pd.read_csv(file_path, header=None)
                .astype(str)
                .fillna("")
                .values.flatten()
            ).lower()
        except Exception as e:
            print(f"Could not read {file_path}: {e}")
            file_text = ""

        if "rural" in file_text:
            print(
                "  → Found 'rural' in file: using process_code2_file() method"
            )
            df = process_code2_file(file_path, year_val)
        else:
            print("  → No 'rural' found: using sequence-based cleaning method")

            df = pd.read_csv(file_path, header=None)
            first_col = df.columns[0]

            sequence = [
                ("rural", "male"),
                ("rural", "female"),
                ("rural", "total"),
                ("urban", "male"),
                ("urban", "female"),
                ("urban", "total"),
            ]

            df["sector"] = ""
            df["gender"] = ""
            seq_index = -1
            sector, gender = None, None

            for i, val in enumerate(df[first_col].astype(str)):
                if "table" in val.lower():
                    seq_index = (seq_index + 1) % len(sequence)
                    sector, gender = sequence[seq_index]
                df.loc[i, "sector"] = sector
                df.loc[i, "gender"] = gender

            df[first_col] = df[first_col].astype(str).str.strip()
            pattern = r"^(table|state|\-?\d+(\.\d+)?$)|\(1\)"
            mask = df[first_col].str.lower().str.match(pattern) | df[
                first_col
            ].isin(["", "nan"])
            df = df[~mask].copy()

            df = df.rename(columns={first_col: "state_name"})
            df = normalize_state_column(df, "state_name")

            df.insert(0, "year", year_val)

    # Case 3: unknown CSVs
    else:
        csvs = list(table_folder.glob("*.csv"))
        if csvs:
            try:
                pd.read_csv(csvs[0], header=None)
                print(
                    f"  Found csv {csvs[0].name} but not 'rural/urban/total/other' — skipping"
                )
            except Exception as e:
                print(f"  Could not read csv {csvs[0].name}: {e}")

    return df


KEY_COLS = ["year", "state_name", "sector", "gender"]


def map_and_align_columns(df, main_folder_name):
    non_key_cols = [c for c in df.columns if c not in KEY_COLS]
    mapped_cols = map_folder_to_cols(main_folder_name) or []
    n_non = len(non_key_cols)

    out_df = df[KEY_COLS].copy().reset_index(drop=True)

    if mapped_cols:
        for i, mcol in enumerate(mapped_cols):
            out_df[mcol] = df[non_key_cols[i]].values if i < n_non else pd.NA

        if n_non > len(mapped_cols):
            for j in range(len(mapped_cols), n_non):
                extra_name = (
                    f"{main_folder_name}_extra_{j - len(mapped_cols) + 1}"
                )
                out_df[extra_name] = df[non_key_cols[j]].values
    else:
        for col in non_key_cols:
            out_df[f"{main_folder_name}_{col}"] = df[col].values

    out_df.set_index(KEY_COLS, inplace=True)
    return out_df


# STATE CODE MAPPING


def load_mapping(mapping_csv: Path):
    """Load LGD mapping CSV even if extra header rows are present."""
    if not mapping_csv.exists():
        raise FileNotFoundError(f"Mapping CSV not found: {mapping_csv}")

    # Find where header starts
    with open(mapping_csv, "r", encoding="utf-8") as f:
        lines = f.readlines()

    header_line_idx = None
    for i, line in enumerate(lines):
        if "State Code" in line and "State Name" in line:
            header_line_idx = i
            break

    if header_line_idx is None:
        raise ValueError(
            "Could not find header row with 'State Code' in mapping file."
        )

    df = pd.read_csv(mapping_csv, skiprows=header_line_idx)
    df = df[["State Code", "State Name (In English)"]].drop_duplicates()

    df["State Name (In English)"] = (
        df["State Name (In English)"].str.strip().str.title()
    )
    df.rename(
        columns={
            "State Code": "state_code",
            "State Name (In English)": "state_name",
        },
        inplace=True,
    )
    print(f" Loaded LGD mapping with {len(df)} states.")
    return df


def merge_with_state_codes(df, mapping_df):
    """Merge dataframe with LGD mapping to add state_code column."""
    df["state_name"] = df["state_name"].astype(str).str.strip().str.title()
    df["state_name"] = df["state_name"].replace(
        {
            "Jammu & Kashmir": "Jammu And Kashmir",
            "A & N Islands": "Andaman And Nicobar Islands",
        }
    )

    merged_df = df.merge(mapping_df, on="state_name", how="left")

    # Manual fix for Delhi & Chandigarh
    manual_codes = {
        "Delhi": 7,
        "Chandigarh": 4,
        "Dadra & Nagar Haveli": 38,
        "Daman & Diu": 38,
        "All-India": 0,
    }
    merged_df["state_code"] = merged_df.apply(
        lambda row: manual_codes.get(row["state_name"], row["state_code"]),
        axis=1,
    )

    merged_df["state_code"] = (
        merged_df["state_code"]
        .astype(float)
        .astype("Int64")
        .astype(str)
        .str.zfill(2)
    )

    return merged_df


#  Main combine func
def combine_all_folders_full(parent_folder, fixed_folders, output_file):
    parent_folder = Path(parent_folder)
    all_indexed_dfs = []

    all_folders_ordered = get_ordered_folders(parent_folder, fixed_folders)

    year_match = re.search(r"(\d{4})-(\d{2})", str(parent_folder))
    year_val = int(year_match.group(1)) + 1 if year_match else None

    for folder_key in all_folders_ordered:
        main_folder = resolve_main_folder(parent_folder, folder_key)
        if main_folder is None:
            print(
                f"  folder not found on disk for key: {folder_key} — skipping"
            )
            continue

        table_folder = get_nested_table_folder(main_folder)
        if table_folder is None:
            print(
                f"  no nested table folder inside '{main_folder.name}' — skipping"
            )
            continue

        print(
            f"\nProcessing '{folder_key}' → actual '{main_folder.name}' → using nested '{table_folder.name}'"
        )
        df = load_folder_csv(table_folder, year_val)
        if df.empty:
            print(f"  No data extracted from folder '{main_folder.name}'")
            continue
        if not all(k in df.columns for k in KEY_COLS):
            print(
                f" expected key column missing in output from '{main_folder.name}' — skipping"
            )
            continue

        out_df = map_and_align_columns(df, main_folder.name)
        all_indexed_dfs.append(out_df)

    if not all_indexed_dfs:
        print(" No valid data found.")
        return None

    combined = pd.concat(all_indexed_dfs, axis=1).reset_index()
    mapping_csv = Path.cwd().parents[1] / "data/external/LGD_Latest 1.csv"

    mapping_df = load_mapping(mapping_csv)
    combined = merge_with_state_codes(combined, mapping_df)
    if "indus_extraterritorial_org" in combined.columns:
        combined["indus_extraterritorial_org"] = combined["indus_extraterritorial_org"].replace("-", pd.NA)

    key_cols_with_code = [
        "year",
        "state_name",
        "state_code",
        "sector",
        "gender",
    ]
    other_cols = [c for c in combined.columns if c not in key_cols_with_code]
    combined = combined[key_cols_with_code + other_cols]

    combined = convert_data_to_title_case(combined)
    combined.to_csv(output_file, index=False)
    print(f"\n Combined all folders → {output_file} (shape={combined.shape})")
    return combined


if __name__ == "__main__":
    PARENT_INPUT_FOLDER = Path.cwd().parents[1] / "data/interim/interim1"
    OUTPUT_PARENT_FOLDER = Path.cwd().parents[1] / "data/processed"
    OUTPUT_PARENT_FOLDER.mkdir(parents=True, exist_ok=True)

    FIXED_FOLDERS = [
        "general_educational_level",
        "broad_status_employment",
        "labour_force_participation_rate",
        "worker_population_ratio",
        "unemployment_rate",
        "industry_of_work",
        "lfpr_decile",
        "wpr_decile",
        "ur_decile",
        "cws_broad_status",
        "industry_enterprise_type",
        "average_regular_wage",
        "average_casual_wage",
        "self_employed",
        "lfpr_cws",
        "wpr_cws",
        "lfpr_usual_state",
        "wpr_usual_state",
        "ur_usual_state",
    ]

    # Find all year folders
    year_folders = sorted(
        [f for f in PARENT_INPUT_FOLDER.iterdir() if f.is_dir() and re.match(r"^\d{4}-\d{2}$", f.name)]
    )
    print("Found year folders:", [f.name for f in year_folders])

    all_year_dfs = []

    # Process each year folder
    for year_folder in year_folders:
        print(f"\nProcessing year folder: {year_folder.name}")
        combined_df = combine_all_folders_full(year_folder, FIXED_FOLDERS, output_file=None)
        if combined_df is not None:
            all_year_dfs.append(combined_df)
        else:
            print(f"No data processed for {year_folder.name}")

    # Combine all years into one master CSV
    if all_year_dfs:
        final_combined = pd.concat(all_year_dfs, ignore_index=True, join="outer")
        key_cols = ["year", "state_name", "sector", "gender"]
        other_cols = [c for c in final_combined.columns if c not in key_cols]
        final_combined = final_combined[key_cols + other_cols]

        final_combined = convert_data_to_title_case(final_combined)
        final_output_file = OUTPUT_PARENT_FOLDER / "all_years_combined.csv"
        final_combined.to_csv(final_output_file, index=False)
        print(f"\nFinal combined file saved: {final_output_file} (shape={final_combined.shape})")
    else:
        print("\nNo valid data from any year folder.")
