from data import NAME_TO_ID, ID_TO_NAME, ID_TO_LEVEL, EVO_DB

SPECIAL = {"Devimon", "Numemon", "Sukamon", "Nanimon", "Vademon", "Kunemon"}
STATS = ("HP", "MP", "Offense", "Defense", "Speed", "Brains")
LEVELS = ("FRESH", "IN-TRAINING", "ROOKIE", "CHAMPION", "ULTIMATE")


def main():
    evo_path = fill_in_evolution_path(["Ninjamon", "Mamemon"])
    training_regimem = construct_training_regimen(evo_path)

    # partner = {
    #     "id": NAME_TO_ID["Kunemon"],
    #     "Stats": {"HP": 3206, "MP": 6396, "Offense": 958, "Defense": 14, "Speed": 642, "Brains": 14},
    #     "Care": 18,
    #     "Weight": 28,
    #     "Bonus conditions": {"Happy": 30, "Disc": 54, "Battles": 33, "Techs": 50},
    # }
    # target = get_evolution_target(partner)

    # if target is None:
    #     print("No evolution target met")  
    # else:
    #     print(f"Evolution target: {ID_TO_NAME[target]}")

# ===========================================================================================================

def fill_in_evolution_path(partial_evo_path):
    if isinstance(partial_evo_path, str):
        partial_evo_path = [partial_evo_path]
    assert isinstance(partial_evo_path, list), "Input must be a string or list"

    evo_path = {ID_TO_LEVEL[NAME_TO_ID[name]]: NAME_TO_ID[name] for name in partial_evo_path}
    for n in range(len(LEVELS)-1):
        from_id, to_id = evo_path.get(LEVELS[::-1][n+1]), evo_path.get(LEVELS[::-1][n])
        assert ID_TO_NAME.get(to_id) not in SPECIAL, f"Special evolutions are not supported"
        if to_id is not None and from_id is not None:
            assert to_id in EVO_DB["paths_to"][from_id], f"{ID_TO_NAME[from_id]} does not Digivolve to {ID_TO_NAME[to_id]}"
        elif to_id is not None:
            i, valid_candidate_found = 0, False
            while not valid_candidate_found:
                candidate = EVO_DB["paths_from"][to_id][i]
                if candidate not in SPECIAL: valid_candidate_found = True
                else: i+=1
            evo_path[LEVELS[::-1][n+1]] = candidate

    return {level: evo_path[level] for level in LEVELS}

def set_weight_and_care_mistake_goals(evo_path):
    pass

def construct_training_regimen(evo_path):
    champ_reqs = {id: EVO_DB["reqs"][id] for id in EVO_DB["paths_to"][evo_path["ROOKIE"]]}
    for id, reqs in champ_reqs.items():
        print(ID_TO_NAME[id], reqs)


    ult_reqs = EVO_DB["reqs"].get(evo_path.get("ULTIMATE"), {})
    partner = {"id": evo_path["ROOKIE"], "Weight": champ_reqs["Weight"], "Care": 0}

    if ult_reqs:
        goal_stats = []
        for stat in STATS:
            if ult_reqs[stat] == -1: 
                goal_stats.append(100)
            elif ult_reqs.get(stat) == -1:
                goal_stats.append(200)

# ===========================================================================================================

def score(reqs, partner, grant_bonus_condition=False):
    """ Max score is 4 points, at least 3 required for evolution """
    pts = 0

    is_max_cm = (reqs["Flags"] & 0x10) != 0
    care   = (0 if reqs["Care"] == -1 else reqs["Care"])
    pts += 1 if (care >= partner["Care"] if is_max_cm else care <= partner["Care"]) else 0

    weight = (0 if reqs["Weight"] == -1 else reqs["Weight"])
    pts += 1 if (weight - 5 <= partner["Weight"] <= weight + 5) else 0

    ok = True
    for stat in STATS:
        req_value = reqs[stat]
        if stat in ("HP", "MP") and req_value != -1: req_value *= 10
        if req_value != -1 and partner["Stats"][stat] < req_value:
            ok = False
            break
    pts += 1 if ok else 0

    if grant_bonus_condition:
        pts += 1
    else:
        pts += 1 if check_bonus_conditions(reqs, partner) else 0

    return pts

def check_bonus_conditions(reqs, partner):
    bonus = False
    if reqs["Bonus"] != -1 and partner["id"] == reqs["Bonus"]: bonus = True
    if reqs["Disc"]  > 0 and partner["Bonus conditions"]["Disc"]  >= reqs["Disc"]:  bonus = True
    if reqs["Happy"] > 0 and partner["Bonus conditions"]["Happy"] >= reqs["Happy"]: bonus = True
    if reqs["Battles"] != -1:
        if (reqs["Flags"] & 1) != 0: 
            bonus = (bonus or (reqs["Battles"] >= partner["Bonus conditions"]["Battles"]))
        else: 
            bonus = (bonus or (reqs["Battles"] <= partner["Bonus conditions"]["Battles"]))
    if reqs["Techs"] > 0 and partner["Bonus conditions"]["Techs"] >= reqs["Techs"]: bonus = True
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
