
import pandas as pd
from rapidfuzz import process, fuzz
from pathlib import Path


def add_lgd_codes(forest_path, lgd_path, output_file=None):


    # READ DATA
    
    df = pd.read_csv(forest_path)

    # DELETE SL NO COLUMN
    df = df.drop(columns=["sl_no"], errors="ignore")

    lgd = pd.read_csv(lgd_path, low_memory=False)



    # KEEP REQUIRED LGD COLUMNS
    

    lgd = lgd[
        [
            "State Code",
            "State Name (In English)",
            "District Code",
            "District Name  (In English)"
        ]
    ]


    # CLEAN TEXT
    

    df["state"] = df["state"].astype(str).str.strip().str.title()
    df["district"] = df["district"].astype(str).str.strip().str.title()

    lgd["State Name (In English)"] = lgd["State Name (In English)"].astype(str).str.strip().str.title()
    lgd["District Name  (In English)"] = lgd["District Name  (In English)"].astype(str).str.strip().str.title()


    # STATE RENAME FIX
    

    state_rename = {
        "Jammu & Kashmir": "Jammu And Kashmir",
        "Dadra & Nagar Haveli And Daman & Diu": "The Dadra And Nagar Haveli And Daman And Diu",
        "Andaman & Nicobar Islands": "Andaman And Nicobar Islands"
    }

    df["state"] = df["state"].replace(state_rename)


    # FORCE STATE CODES
    

    force_state_codes = {
        "Chandigarh": 4,
        "Delhi": 7
    }


    # DIRECT DISTRICT CODES
    

    direct_district_codes = {
        "Central Delhi":77,"East Delhi":78,"New Delhi":79,"North Delhi":80,
        "North-East Delhi":81,"North-West Delhi":82,"South Delhi":83,
        "South-West Delhi":84,"West Delhi":85,"Ahmednagar":466,"Bijapur":636,
        "Hoshangabad":409,"Aurangabad":469,"Mumbai":482,"Mumbai City":482,
        "Mumbai Suburban":483,"Osmanabad":488,"Chennai":603,"Kolkata":315,
        "Vijayapura":530,"Shahdara":671,"Chandigarh":44,"South East Delhi":670,
        "Sas Nagar":608
    }


    # DISTRICT RENAME MAP
    

    district_rename_map = {
        "North & Middle Andaman":"North And Middle Andaman",
        "Ysr Kadapa":"Y.S.R. Kadapa",
        "Lepa Rada":"Leparada",
        "Lahaul & Spiti":"Lahaul And Spiti",
        "Badgam":"Budgam",
        "Punch":"Poonch",
        "Mewat":"Nuh",
        "Baudh":"Boudh",
        "Jajapur":"Jajpur",
        "Subarnapur":"Sonepur",
        "Firozpur":"Ferozepur",
        "Sahibzada Ajit Singh Nagar":"Sas Nagar",
        "Chittaurgarh":"Chittorgarh",
        "East Sikkim":"Gangtok",
        "North Sikkim":"Mangan",
        "South Sikkim":"Namchi",
        "West Sikkim":"Gyalshing",
        "Raebareli":"Rae Bareli",
        "Hoogly":"Hooghly",
        "Panchmahals":"Panch Mahals",
        "Sabarkantha":"Sabar Kantha",
        "Narsinghpur":"Narsimhapur",
        "Waynad":"Wayanad",
        "Ri-Bhoi":"Ri Bhoi",
        "Kabirdham":"Kabeerdham",
        "Raj Nandgaon":"Rajnandgaon",
        "Dadra & Nagar Haveli":"Dadra And Nagar Haveli",
        "South-East Delhi":"South East Delhi",
        "Bandipura":"Bandipora",
        "Rajauri":"Rajouri",
        "Sahibganj":"Sahebganj",
        "Baleswar":"Baleshwar",
        "Gariaband":"Gariyaband",
        "Morigaon":"Marigaon",
        "Tiruchchirapalli":"Tiruchirappalli",
        "West Champaran":"Pashchim Champaran",
        "East Champaran":"Purbi Champaran",
        "Kawardha (Kabirdham)":"Kabeerdham",
        "Banaskantha":"Banas Kantha",
        "Kodarma":"Koderma",
        "Sas Nagar":"S.A.S Nagar",
        "Jagtial":"Jagitial",
        "Jangaon":"Jangoan",
        "Shravasti":"Shrawasti",
        "Shupiyan":"Shopian",
        "North Parganas":"North 24 Parganas",
        "South Parganas":"South 24 Parganas"
    }

    df["district"] = df["district"].replace(district_rename_map)

    lgd = lgd.drop_duplicates(
        subset=["State Name (In English)", "District Name  (In English)"]
    )

    state_list = lgd["State Name (In English)"].drop_duplicates().tolist()

    state_codes = []
    district_codes = []

    for _, row in df.iterrows():

        state = row["state"]
        district = row["district"]

        if state in force_state_codes:
            state_code = force_state_codes[state]
            state_rows = lgd[lgd["State Code"] == state_code]

        else:
            state_match = process.extractOne(state, state_list, scorer=fuzz.partial_ratio)

            if state_match and state_match[1] >= 90:
                matched_state = state_match[0]
                state_rows = lgd[lgd["State Name (In English)"] == matched_state]
                state_code = state_rows.iloc[0]["State Code"]
            else:
                state_rows = pd.DataFrame()
                state_code = None

        if district in direct_district_codes:
            district_code = direct_district_codes[district]

        elif not state_rows.empty:

            district_list = state_rows["District Name  (In English)"].tolist()

            district_match = process.extractOne(
                district,
                district_list,
                scorer=fuzz.partial_ratio
            )

            if district_match and district_match[1] >= 90:

                matched_district = district_match[0]

                district_row = state_rows[
                    state_rows["District Name  (In English)"] == matched_district
                ].iloc[0]

                district_code = district_row["District Code"]

            else:
                district_code = None

        else:
            district_code = None

        state_codes.append(state_code)
        district_codes.append(district_code)

    df["State Code"] = state_codes
    df["District Code"] = district_codes

    cols = list(df.columns)

    cols.insert(cols.index("state") + 1, cols.pop(cols.index("State Code")))
    cols.insert(cols.index("district") + 1, cols.pop(cols.index("District Code")))

    df = df[cols]

    if output_file:
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_file, index=False)
        print("File saved:", output_file)

    return df


forest_path = Path(__file__).resolve().parents[2] / "data/processed/fire/fire_snpp_viirs_all_states.csv"
output_file = Path(__file__).resolve().parents[2] / "data/processed/fire/forest_with_state_codes.csv"

lgd_path = Path(__file__).resolve().parents[2]/"data/external/LGD_Latest 1.csv"


df = add_lgd_codes(forest_path, lgd_path, output_file)