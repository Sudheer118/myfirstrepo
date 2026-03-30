import pandas as pd
from rapidfuzz import process, fuzz
from pathlib import Path


# FILE PATHS


forest_path = Path(__file__).resolve().parents[2] / "data/processed/forest cover1/forest_cover_all_years.csv"
output_file = Path(__file__).resolve().parents[2] / "data/processed/forest cover1/forest_with_lgd_codes.csv"

lgd_path = Path(__file__).resolve().parents[2]/"data/external/LGD_Latest 1.csv"


# READ DATA


forest = pd.read_csv(forest_path)
lgd = pd.read_csv(lgd_path, low_memory=False)


# SELECT LGD COLUMNS

lgd = lgd[[
    "State Code",
    "State Name (In English)",
    "District Code",
    "District Name  (In English)"
]]


# CLEAN TEXT


forest["state"] = forest["state"].astype(str).str.strip().str.title()
forest["district"] = forest["district"].astype(str).str.strip().str.title()

lgd["State Name (In English)"] = lgd["State Name (In English)"].astype(str).str.strip().str.title()
lgd["District Name  (In English)"] = lgd["District Name  (In English)"].astype(str).str.strip().str.title()


# STATE RENAME FIX


state_rename = {
    "Jammu & Kashmir": "Jammu And Kashmir",
    "Daman & Diu": "The Dadra And Nagar Haveli And Daman And Diu",
}

forest["state"] = forest["state"].replace(state_rename)


# DISTRICT RENAME MAP


district_rename_map = {
"Cuddapah":"Y.S.R. Kadapa",
"Ysr Kadapa":"Y.S.R. Kadapa",
"Koriya":"Korea",
"Mehsana":"Mahesana",
"Gurgaon":"Gurugram",
"Lahaul & Spiti":"Lahaul And Spiti",
"Lahul & Spiti":"Lahaul And Spiti",
"Pakaur":"Pakur",
"Chamrajnagar":"Chamarajanagar",
"Mysore":"Mysuru",
"Neernach":"Neemuch",
"Sahia":"Siaha",
"Saiha":"Siaha",
"Firozpur":"Ferozepur",
"Dhaulpur":"Dholpur",
"Mahboobnagar":"Mahabubnagar",
"Allahabad":"Prayagraj",
"Bagpat":"Baghpat",
"Barabanki":"Bara Banki",
"Ysr":"Y.S.R. Kadapa",
"Mewat":"Nuh",
"Bangalore":"Bengaluru Urban",
"Bangalore Rural":"Bengaluru Rural",
"Chikmagalur":"Chikkamagaluru",
"Anugul":"Angul",
"Baudh":"Boudh",
"Debagarh":"Deogarh",
"Jajapur":"Jajpur",
"Subarnapur":"Sonepur",
"Sahibzada Ajit Singh Nagar":"Sas Nagar",
"Chittaurgarh":"Chittorgarh",
"Faizabad":"Ayodhya",
"Kanshiram Nagar":"Kasganj",
"Mahamaya Nagar":"Hathras",
"Hugli":"Hooghly",
"Dohod":"Dahod",
"Sabarkantha":"Sabar Kantha",
"Pashchimi Singhbhum":"West Singhbhum",
"Purbi Singhbhum":"East Singhbhum",
"Southtwentyfour":"South 24 Parganas",
"Narsinghpur":"Narsimhapur",
"Balila":"Ballia",
"Donga":"Gonda",
"Orangkhpur":"Gorakhpur",
"Raebareli":"Rae Bareli",
"Rudprayag":"Rudraprayag",
"Darjehing":"Darjeeling",
"North & Middle":"North And Middle Andaman",
"Lepa Rada":"Leparada",
"Metropolitan":"Kamrup Metro",
"Dadra & Nagar":"Dadra And Nagar Haveli",
"Banaskantha":"Banas Kantha",
"Hoogly":"Hooghly",
"Ahmadnagar":"Ahmednagar",
"Aizwal":"Aizawl",
"Badgam":"Budgam",
"Balia":"Ballia",
"Belgaum":"Belagavi",
"Bellary":"Ballari",
"Bid":"Beed",
"Bulansdahr":"Bulandshahr",
"Chikmaglu":"Chikkamagaluru",
"Coochbehar":"Cooch Behar",
"Darjiling":"Darjeeling",
"Dhubari":"Dhubri",
"Dohad":"Dahod",
"Gulbarga":"Kalaburagi",
"Haora":"Howrah",
"Hoogli":"Hooghly",
"Hordoi":"Hardoi",
"Jyotiba Phule Nagar":"Amroha",
"Kawardha":"Kabeerdham",
"Keonjhar":"Kendujhar",
"Koch Bihar":"Cooch Behar",
"Krishna-Giri":"Krishnagiri",
"Laknow":"Lucknow",
"Naogaon":"Nagaon",
"Nasik":"Nashik",
"Nawanshahar":"Shahid Bhagat Singh Nagar",
"Nawapara":"Nuapada",
"North &Middle Andaman":"North And Middle Andaman",
"North Sikkim":"Mangan",
"North Twenty Four Parganas":"North 24 Parganas",
"Panchmahals":"Panch Mahals",
"Paschimi Singbhum":"West Singhbhum",
"Podukottai":"Pudukkottai",
"Popumpare":"Papum Pare",
"Punch":"Poonch",
"Purbi Singbhum":"East Singhbhum",
"Ribhoi":"Ri Bhoi",
"Sahibdazai Singh Nagar":"S.A.S Nagar",
"Sahibgani":"Sahebganj",
"Sant Ravidas Nagar":"Sant Kabir Nagar",
"Saralkeela-Kharsawan":"Saraikela Kharsawan",
"Shimoga":"Shivamogga",
"Shupiyan":"Shopian",
"Sibsagar":"Sivasagar",
"South Sikkim":"Namchi",
"South Twenty Four Parganas":"South 24 Parganas",
"Subansiri Lower":"Lower Subansiri",
"Subansiri Upper":"Upper Subansiri",
"Tumkur":"Tumakuru",
"Tuticorin":"Thoothukkudi",
"Udipi":"Udupi",
"Waynad":"Wayanad",
"West Sikkim":"Gyalshing",
"East Sikkim":"Gangtok"
}

forest["district"] = forest["district"].replace(district_rename_map)


# DIRECT DISTRICT CODE MAP


direct_district_codes = {
"Central Delhi":77,
"East Delhi":78,
"New Delhi":79,
"North Delhi":80,
"North-East Delhi":81,
"North-West Delhi":82,
"South Delhi":83,
"South-West Delhi":84,
"West Delhi":85,
"Ahmednagar":466,
"Bijapur":636,
"Hoshangabad":409,
"Aurangabad":469,
"Mumbai":482,
"Mumbai City":482,
"Mumbai Suburban":483,
"Osmanabad":488,
"Chennai":603,
"Kolkata":315,
"Vijayapura":530,
"Shahdara":671,
"Chandigarh":44
}


# FORCE STATE CODES


force_state_codes = {
"Chandigarh":4,
"Delhi":7
}


# REMOVE DUPLICATES


lgd = lgd.drop_duplicates(
    subset=["State Name (In English)", "District Name  (In English)"]
)

state_list = lgd["State Name (In English)"].drop_duplicates().tolist()


# OUTPUT STORAGE


state_codes = []
district_codes = []


# MATCH LOOP

for _, row in forest.iterrows():

    forest_state = row["state"]
    forest_district = row["district"]

    # STATE MATCH 

    state_match = process.extractOne(
        forest_state,
        state_list,
        scorer=fuzz.partial_ratio
    )

    if state_match and state_match[1] >= 85:

        lgd_state = state_match[0]

        # SPECIAL STATE SEARCH
        if forest_state == "Jammu And Kashmir":

            lgd_state_rows = lgd[
                lgd["State Name (In English)"].isin(
                    ["Jammu And Kashmir", "Ladakh"]
                )
            ]

        elif forest_state == "Jharkhand":

            lgd_state_rows = lgd[
                lgd["State Name (In English)"].isin(
                    ["Jharkhand", "Rajasthan"]
                )
            ]

        else:

            lgd_state_rows = lgd[
                lgd["State Name (In English)"] == lgd_state
            ]

        state_code = lgd_state_rows.iloc[0]["State Code"]

    else:

        lgd_state_rows = pd.DataFrame()
        state_code = None

    #  DIRECT DISTRICT MATCH 

    if forest_district in direct_district_codes:

        district_code = direct_district_codes[forest_district]

    #  FUZZY DISTRICT MATCH 

    else:

        if not lgd_state_rows.empty:

            district_list = lgd_state_rows[
                "District Name  (In English)"
            ].tolist()

            district_match = process.extractOne(
                forest_district,
                district_list,
                scorer=fuzz.partial_ratio
            )

            if district_match and district_match[1] >= 85:

                lgd_district = district_match[0]

                row_match = lgd_state_rows[
                    lgd_state_rows["District Name  (In English)"] == lgd_district
                ].iloc[0]

                district_code = row_match["District Code"]

            else:

                district_code = None

        else:

            district_code = None

    #  FORCE STATE CODE 

    if forest_state in force_state_codes:
        state_code = force_state_codes[forest_state]

    state_codes.append(state_code)
    district_codes.append(district_code)

# 
# ADD RESULTS
forest["state_code"] = state_codes
forest["district_code"] = district_codes


# MOVE STATE CODE AFTER STATE
cols = list(forest.columns)

cols.insert(cols.index("state") + 1, cols.pop(cols.index("state_code")))
cols.insert(cols.index("district") + 1, cols.pop(cols.index("district_code")))

forest = forest[cols]

# SAVE FILE


forest.to_csv(output_file, index=False)

print("File saved:", output_file)