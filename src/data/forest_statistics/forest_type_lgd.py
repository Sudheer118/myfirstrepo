import pandas as pd
from rapidfuzz import process, fuzz
from pathlib import Path

# FILE PATHS
forest_path = Path(__file__).resolve().parents[2] / "data/processed/statistics/forest_type_all_years1.csv"
output_file = Path(__file__).resolve().parents[2] / "data/processed/statistics/forest_type_lgd.csv"

lgd_path = Path(__file__).resolve().parents[2]/"data/external/LGD_Latest 1.csv"



# READ DATA


forest = pd.read_csv(forest_path)
lgd = pd.read_csv(lgd_path, low_memory=False)


# KEEP ONLY STATE COLUMNS


lgd = lgd[[
    "State Code",
    "State Name (In English)"
]]


# CLEAN TEXT


forest["state"] = forest["state"].astype(str).str.strip().str.title()
lgd["State Name (In English)"] = lgd["State Name (In English)"].astype(str).str.strip().str.title()


# STATE NAME FIX


state_rename = {
    "Jammu & Kashmir": "Jammu And Kashmir",
    "Daman & Diu": "The Dadra And Nagar Haveli And Daman And Diu",
    "Dadra & Nagar Haveli" :"The Dadra And Nagar Haveli And Daman And Diu",
    "Dadra & Nagar Haveli And Daman & Diu":"The Dadra And Nagar Haveli And Daman And Diu"

}

forest["state"] = forest["state"].replace(state_rename)


# FORCE STATE CODES


force_state_codes = {
    "Chandigarh": 4,
    "Delhi": 7
}


# REMOVE DUPLICATES


lgd = lgd.drop_duplicates(subset=["State Name (In English)"])

state_list = lgd["State Name (In English)"].tolist()


# MATCH STATES


state_codes = []

for state in forest["state"]:

    #  FORCE STATE CODE FIRST
    if state in force_state_codes:
        code = force_state_codes[state]

    else:

        match = process.extractOne(
            state,
            state_list,
            scorer=fuzz.partial_ratio
        )

        if match and match[1] >= 85:

            matched_state = match[0]

            code = lgd.loc[
                lgd["State Name (In English)"] == matched_state,
                "State Code"
            ].values[0]

        else:
            code = None

    state_codes.append(code)
    
# ADD COLUMN

forest = forest.drop(columns=["State Code"], errors="ignore")

forest.insert(forest.columns.get_loc("state") + 1, "State Code", state_codes)


# SAVE


forest.to_csv(output_file, index=False)

print("File saved:", output_file)