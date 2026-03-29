import pandas as pd

DATA_FILENAME = "Digimon_World/Digimon World Data Sheet.xlsx"

ITEMS = (
    pd.read_excel(DATA_FILENAME, sheet_name="Items")[["ID", "Name"]]
    .assign(ID=lambda df: pd.to_numeric(df["ID"], errors="coerce"))
    .dropna(subset=["ID"])
    .assign(ID=lambda df: df["ID"].astype(int))
    .set_index("ID")["Name"]
    .to_dict()
)

LOCATIONS = (
    pd.read_excel(DATA_FILENAME, sheet_name="Map Setup")[["ID", "Name", "Description"]]
    .assign(ID=lambda df: pd.to_numeric(df["ID"], errors="coerce"))
    .dropna(subset=["ID"])
    .assign(ID=lambda df: df["ID"].astype(int))
    .assign(
        Name=lambda df: df["Name"].fillna(""),
        Description=lambda df: df["Description"].fillna(""),
    )
    .assign(
        Location=lambda df: (
            df["Name"].astype(str)
            + df["Description"].astype(str).map(lambda d: f" / {d}" if d else "")
        ).str.strip()
    )
    .set_index("ID")["Location"]
    .to_dict()
)

stats_df = pd.read_excel(
    DATA_FILENAME, sheet_name="Digimon Stats", usecols=["ID", "Name", "Level"], nrows=66
).dropna(subset=["ID", "Name"])
stats_df["ID"] = stats_df["ID"].astype(int)

NAME_TO_ID = dict(zip(stats_df["Name"], stats_df["ID"]))
ID_TO_NAME = dict(zip(stats_df["ID"], stats_df["Name"]))
ID_TO_LEVEL = dict(zip(stats_df["ID"], stats_df["Level"].astype(str)))

def load_evolution_db():
    """
    Creates a dictionary with the following keys:
    'reqs', 'paths'
    """

    evo = pd.read_excel(DATA_FILENAME, sheet_name="Digimon Evolution", header=[0, 1])

    cols = list(evo.columns)
    id_col   = next(c for c in cols if c[0] == "ID")
    name_col = next(c for c in cols if c[0] == "Name")
    evo = evo.dropna(subset=[id_col, name_col])

    reqs, paths_from, paths_to = {}, {}, {}
    for _, row in evo.iterrows():
        id = NAME_TO_ID[row[name_col]]
        
        req = {}
        for col_name in ("HP", "MP", "Offense", "Defense", "Speed", "Brains", "Care", "Weight", "Disc", "Happy", "Battles", "Techs"):
            v = row[("Evolution Requirements", col_name)]
            req[col_name] = int(v)
        bonus = row[("Evolution Requirements", "Bonus")]
        req["Bonus"] = -1 if pd.isna(bonus) or bonus in ("", "-") else NAME_TO_ID.get(str(bonus), -1)
        flags = row[("Evolution Requirements", "Flags")]
        req["Flags"] = 0 if pd.isna(flags) else int(flags)
        reqs[id] = req

        from_names = [row[col] for col in [("Paths", f"From#{i+1}") for i in range(5)] if pd.notna(row[col])]
        paths_from[id] = [NAME_TO_ID[name] for name in from_names if name in NAME_TO_ID]
        to_names = [row[col] for col in [("Paths", f"To#{i+1}") for i in range(6)] if pd.notna(row[col])]
        paths_to[id] = [NAME_TO_ID[name] for name in to_names if name in NAME_TO_ID]

    return {"reqs": reqs, "paths_from": paths_from, "paths_to": paths_to}

EVO_DB = load_evolution_db()

ADDRESSES = {
    "Weight":                {"address": "PSXBaseAddress+001384A2", "type": "Byte"},
    "Care mistakes":         {"address": "PSXBaseAddress+001384B2", "type": "2 Bytes"},
    "Happiness":             {"address": "PSXBaseAddress+0013848A", "type": "2 Bytes"},
    "Discipline":            {'address': 'PSXBaseAddress+00138488', 'type': '2 Bytes'},
    "Battles":               {'address': 'PSXBaseAddress+001384B4', 'type': '2 Bytes'},
    "Techs":                 {'address': 'PSXBaseAddress+00089C2C', 'type': '2 Bytes'},

    "Off":                   {"address": "PSXBaseAddress+001557E0", "type": "2 Bytes"},
    "Def":                   {"address": "PSXBaseAddress+001557E2", "type": "2 Bytes"},
    "Speed":                 {"address": "PSXBaseAddress+001557E4", "type": "2 Bytes"},
    "Brains":                {"address": "PSXBaseAddress+001557E6", "type": "2 Bytes"},
    "HP":                    {"address": "PSXBaseAddress+001557F0", "type": "2 Bytes"},
    "MP":                    {"address": "PSXBaseAddress+001557F2", "type": "2 Bytes"},

    "Needs scolding":        {"address": "PSXBaseAddress+00134C59", "type": "Binary"},
    "Tiredness":             {"address": "PSXBaseAddress+00138482", "type": "2 Bytes"},
    "Energy level":          {"address": "PSXBaseAddress+0013849C", "type": "2 Bytes"},
    "Lifespan":              {"address": "PSXBaseAddress+001384A8", "type": "2 Bytes"},
    "Age since Digivolution":{"address": "PSXBaseAddress+001384B6", "type": "2 Bytes"},

    "Digimon ID":            {'address': 'PSXBaseAddress+001557A8', 'type': 'Byte'},
    "Bedtime":               {"address": "PSXBaseAddress+00138468", "type": "2 Bytes"},

    "Condition flag":        {"address": "PSXBaseAddress+00138460", "type": "Binary"},
    "Hungry":                {"address": "PSXBaseAddress+0013849E", "type": "2 Bytes"},
    "Pooping":               {"address": "PSXBaseAddress+00138480", "type": "2 Bytes"},
    "Sickness":              {"address": "PSXBaseAddress+00138496", "type": "2 Bytes"},
    "Starvation":            {"address": "PSXBaseAddress+001384A0", "type": "2 Bytes"},
    "Tiredness hunger":      {"address": "PSXBaseAddress+00138486", "type": "2 Bytes"},
    "Tiredness sleep":       {"address": "PSXBaseAddress+00138476", "type": "2 Bytes"},
    "Training Boost":        {"address": "PSXBaseAddress+001384B0", "type": "2 Bytes"},

    "Bits":                  {"address": "PSXBaseAddress+00134EB8", "type": "4 Bytes"},
    "Tournaments won":       {"address": "PSXBaseAddress+00134FCC", "type": "2 Bytes"},
    "Tournaments lost":      {'address': 'PSXBaseAddress+00134FD0', 'type': '2 Bytes'},
    "Tamer Level":           {"address": "PSXBaseAddress+001557A4", "type": "Byte"},

    "Year":                  {"address": "PSXBaseAddress+00134F02", "type": "Byte"},
    "Day":                   {"address": "PSXBaseAddress+00134F04", "type": "Byte"},
    "Hour":                  {"address": "PSXBaseAddress+00134EBC", "type": "Byte"},
    "Minute":                {"address": "PSXBaseAddress+00134EBE", "type": "Byte"},

    "Took Meat":             {"address": "PSXBaseAddress+001BE050", "type": "Binary"},
    "Drimogemon Days passed":{"address": "PSXBaseAddress+001BE04F", "type": "Byte"},
    "Drimogemon":            {"address": "PSXBaseAddress+001BE04F", "type": "Byte"},
    "Back Dimension":        {"address": "PSXBaseAddress+001BE04D", "type": "Byte"},

    "Fishing State":         {"address": "PSXBaseAddress+0007B41C", "type": "Byte"},
    "Frames Since Hooked":   {"address": "PSXBaseAddress+0007B484", "type": "4 Bytes"},
    "Nibble Time":           {"address": "PSXBaseAddress+0007B49C", "type": "4 Bytes"},
    "Tension Bar":           {"address": "PSXBaseAddress+0007B504", "type": "4 Bytes"},

    "Current Screen ID":     {"address": "PSXBaseAddress+00134DA8", "type": "Byte"},
    "RNG":                   {"address": "PSXBaseAddress+00009010", "type": "4 Bytes"},
    "Textbox Timer":         {'address': 'PSXBaseAddress+00135012', 'type': 'Byte'},
    "Location X":            {"address": "PSXBaseAddress+0015577E", "type": "2 Bytes"},
    "Location Y":            {"address": "PSXBaseAddress+00155786", "type": "2 Bytes"},
    "Location Z":            {"address": "PSXBaseAddress+00155782", "type": "2 Bytes"},
}

# Adding inventory addresses
for n in range(30):
    ADDRESSES[f"Slot{n}/Name"]   = {"address": f"PSXBaseAddress+{0x0013D474 + n:08X}", "type": "Byte"}
    ADDRESSES[f"Slot{n}/Amount"] = {"address": f"PSXBaseAddress+{0x0013D492 + n:08X}", "type": "Byte"}