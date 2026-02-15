from data import NAME_TO_ID, ID_TO_NAME, ID_TO_LEVEL, EVO_DB

SPECIAL = {"Devimon", "Numemon", "Sukamon", "Nanimon", "Vademon", "Kunemon"}
STATS = ("HP", "MP", "Offense", "Defense", "Speed", "Brains")

def main():
    partner = {
        "id": NAME_TO_ID["Kunemon"],
        "Stats": {"HP": 3206, "MP": 6396, "Offense": 958, "Defense": 14, "Speed": 642, "Brains": 14},
        "Care": 18,
        "Weight": 28,
        "Bonus conditions": {"Happy": 30, "Disc": 54, "Battles": 33, "Techs": 50},
    }
    target = get_evolution_target(partner)

    if target is None:
        print("No evolution target met")  
    else:
        print(f"Evolution target: {ID_TO_NAME[target]}")

# ===========================================================================================================

def score(req, partner):
    """ Max score is 4 points, at least 3 required for evolution """
    pts = 0

    is_max_cm = (req["Flags"] & 0x10) != 0
    care   = (0 if req["Care"] == -1 else req["Care"])
    pts += 1 if (care >= partner["Care"] if is_max_cm else care <= partner["Care"]) else 0

    weight = (0 if req["Weight"] == -1 else req["Weight"])
    pts += 1 if (weight - 5 <= partner["Weight"] <= weight + 5) else 0

    ok = True
    for col_name in ("HP", "MP", "Offense", "Defense", "Speed", "Brains"):
        req_value = req[col_name]
        if col_name in ("HP", "MP") and req_value != -1: req_value *= 10
        if req_value != -1 and partner["Stats"][col_name] < req_value:
            ok = False
            break
    pts += 1 if ok else 0

    pts += 1 if check_bonus_conditions(req, partner) else 0

    return pts

def check_bonus_conditions(req, partner):
    bonus = False
    if req["Bonus"] != -1 and partner["id"] == req["Bonus"]: bonus = True
    if req["Disc"]  > 0 and partner["Bonus conditions"]["Disc"]  >= req["Disc"]:  bonus = True
    if req["Happy"] > 0 and partner["Bonus conditions"]["Happy"] >= req["Happy"]: bonus = True
    if req["Battles"] != -1:
        if (req["Flags"] & 1) != 0: 
            bonus = (bonus or (req["Battles"] >= partner["Bonus conditions"]["Battles"]))
        else: 
            bonus = (bonus or (req["Battles"] <= partner["Bonus conditions"]["Battles"]))
    if req["Techs"] > 0 and partner["Bonus conditions"]["Techs"] >= req["Techs"]: bonus = True
    return bonus

def get_in_training_evolution_target(partner):
    candidate_targets = []
    for id in EVO_DB["paths_to"].get(partner["id"]):
        if ID_TO_NAME[id] not in SPECIAL and score(EVO_DB["reqs"][id], partner) >= 3:
            candidate_targets.append(id)

    best, highest = None, -1
    for stat_name in STATS:
        stat_value = partner["Stats"][stat_name] / 10 if stat_name in ("MP", "HP") else partner["Stats"][stat_name]
        if stat_value <= highest:
            continue
        highest = stat_value
        for target_id in candidate_targets:
            if EVO_DB["reqs"][target_id][stat_name] != -1:
                best = target_id
                break
    return best

def get_regular_evolution_target(partner, verbose=False):
    target_scores = {}
    running_score, running_terms, highest_score = 0, 0, 0

    for target_id in EVO_DB["paths_to"][partner["id"]]:
        requirement = EVO_DB["reqs"][target_id]

        if score(EVO_DB["reqs"][target_id], partner) < 3:
            continue        

        score_sum, score_terms = running_score, running_terms
        for stat_name in STATS:
            if requirement[stat_name] == -1:
                continue
            score_sum += int(partner["Stats"][stat_name] / 10) if stat_name in ("HP", "MP") else partner["Stats"][stat_name]
            score_terms += 1
        final_score = score_sum // score_terms if score_terms else 0

        target_scores[target_id] = final_score
        if verbose:
            print(ID_TO_NAME[target_id], final_score)

        running_score = final_score
        running_terms += sum(1 for stat_name in STATS if requirement[stat_name] != -1)
        if final_score > highest_score:
            highest_score = final_score
            running_score, running_terms = 0, 0

    return max(target_scores, key=target_scores.get) if target_scores else None

def get_evolution_target(partner):
    target = None
    if ID_TO_LEVEL[partner["id"]] == "IN-TRAINING":
        target = get_in_training_evolution_target(partner)
    else:
        target = get_regular_evolution_target(partner)
    return target

if __name__ == "__main__": 
    main()
