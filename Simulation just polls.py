import random
from collections import defaultdict
import math

# settings
NUM_SIMULATIONS = 10000
BASE_SEATS = 120
THRESHOLD = 5.0
RANDOM_SEED = None

# Electorate probabilities - chances electorates of each probability are won
ELECTORATE_PROBS = {
    "safe": 0.95,
    "likely": 0.75,
    "lean": 0.60,
    "toss": 0.50,
    "lean_against": 0.40,
    "unlikely": 0.25,
}

# party stats
parties = {
    "National": {
        "mean": 29.19,
        "std": 3.2,
        "electorates": {"safe": 20, "likely": 9, "lean": 4, "toss": 1, "lean_against": 8, "unlikely": 4},
    },
    "Labour": {
        "mean": 34.82,
        "std": 3.4,
        "electorates": {"safe": 14, "likely": 6, "lean": 10, "toss": 4, "lean_against": 4, "unlikely": 10},
    },
    "Greens": {
        "mean": 9.9,
        "std": 3.37,
        "electorates": {"safe": 1, "likely": 0, "lean": 0, "toss": 1, "lean_against": 2, "unlikely": 1},
    },
    "ACT": {
        "mean": 7.81,
        "std": 2.04,
        "electorates": {"safe": 1, "likely": 0, "lean": 0, "toss": 0, "lean_against": 0, "unlikely": 1},
    },
    "TPM": {
        "mean": 2.56,
        "std": 1.32,
        "electorates": {"safe": 0, "likely": 1, "lean": 1, "toss": 2, "lean_against": 0, "unlikely": 1},
    },
    "NZ First": {
        "mean": 11.98,
        "std": 3.75,
        "electorates": {"safe": 0, "likely": 0, "lean": 0, "toss": 0, "lean_against": 0, "unlikely": 1},
    },
    "Opportunity": {
        "mean": 2.99,
        "std": 1.54,
        "electorates": {"safe": 0, "likely": 0, "lean": 0, "toss": 0, "lean_against": 0, "unlikely": 0},
    },
}


party_names = ["Labour", "National", "Greens", "ACT", "NZ First", "TPM", "Opportunity"]

# Others
OTHERS_MEAN = 2.0
OTHERS_STD = 1.5

# Randomness
if RANDOM_SEED is not None:
    random.seed(RANDOM_SEED)

# track all stats
raw_total_party_votes = {p: 0.0 for p in party_names}
raw_total_party_votes["Others"] = 0.0

total_party_votes = {p: 0.0 for p in party_names}
total_party_votes["Others"] = 0.0

seat_results = {party: defaultdict(int) for party in party_names}
overhang_results = {p: defaultdict(int) for p in party_names}

# bloc seat distributions 
left_bloc_seat_results = defaultdict(int)   # key = total left seats, value = count of sims
right_bloc_seat_results = defaultdict(int)  # key = total right seats, value = count of sims

left_wins = right_wins = 0
nat_act_wins = lab_grn_wins = lab_grn_nzf_wins = 0
nat_act_nzf_opp_wins = lab_grn_tpm_opp_wins = lab_grn_opp_wins = 0
lab_nzf_wins = nat_nzf_wins = nat_grn_wins = grn_nzf_opp_act_tpm_wins = 0
nat_nzf_grn_wins = lab_act_wins = lab_act_nzf_wins = nat_lab_wins = lab_nzf_tpm_wins = 0

total_final_seats = {p: 0 for p in party_names}




# Sainte-lague seat distribution
def sainte_lague(votes, total_seats):
    quotients = []
    for party, vote in votes.items():
        divisors = [1.4] + [2 * i + 1 for i in range(1, total_seats * 2)]
        for d in divisors:
            quotients.append((vote / d, party))
    quotients.sort(reverse=True, key=lambda x: x[0])

    seats = {p: 0 for p in votes}
    for i in range(total_seats):
        _, p = quotients[i]
        seats[p] += 1
    return seats


# main simulation loop
for _ in range(NUM_SIMULATIONS):

    # raw gaussian expansion
    raw_votes = {}
    for party, pdata in parties.items():
        raw_votes[party] = random.gauss(pdata["mean"], pdata["std"])
    raw_votes["Others"] = random.gauss(OTHERS_MEAN, OTHERS_STD)

    # accumulate raw
    for p, v in raw_votes.items():
        if p in raw_total_party_votes:
            raw_total_party_votes[p] += v

    # clamp negatives for simulation
    votes = {p: max(v, 0.0) for p, v in raw_votes.items()}

    # normalize to 100%
    total_raw = sum(votes.values())
    for p in votes:
        votes[p] = votes[p] * (100.0 / total_raw)

    # accumulate post scaling
    for p, v in votes.items():
        if p in total_party_votes:
            total_party_votes[p] += v

    # add electorates
    electorates_won = {p: 0 for p in party_names}
    for party, pdata in parties.items():
        if party not in party_names:
            continue
        for category, count in pdata["electorates"].items():
            prob = ELECTORATE_PROBS[category]
            for _ in range(count):
                if random.random() < prob:
                    electorates_won[party] += 1

    # check 5% threshold
    eligible_votes = {}
    electorates = {}
    for party in party_names:
        if votes[party] >= THRESHOLD or electorates_won[party] > 0:
            eligible_votes[party] = votes[party]
            electorates[party] = electorates_won[party]

    if not eligible_votes:
        eligible_votes = {p: votes[p] for p in party_names}
        electorates = {p: electorates_won[p] for p in party_names}

    # renormalize eligible
    total_eligible = sum(eligible_votes.values())
    for p in eligible_votes:
        eligible_votes[p] /= total_eligible

    # calculate num of seats
    seats = sainte_lague(eligible_votes, BASE_SEATS)

    # calculate overhang
    final_seats = {}
    total_seats = BASE_SEATS
    for p in eligible_votes:
        if electorates[p] > seats[p]:
            final_seats[p] = electorates[p]
            total_seats += (electorates[p] - seats[p])
        else:
            final_seats[p] = seats[p]
    
    

    for p in party_names:
        total_final_seats[p] += final_seats.get(p, 0)

    # record seat distribution
    for p in party_names:
        seat_results[p][final_seats.get(p, 0)] += 1

    # record overhang
    for p in party_names:
        overhang = max(0, electorates_won[p] - seats.get(p, 0))
        overhang_results[p][overhang] += 1


    # bloc seats
    left_seats = (
        final_seats.get("Labour", 0)
        + final_seats.get("Greens", 0)
        + final_seats.get("TPM", 0)
    )
    right_seats = (
        final_seats.get("National", 0)
        + final_seats.get("ACT", 0)
        + final_seats.get("NZ First", 0)
    )

    # record bloc seat distributions for graph
    left_bloc_seat_results[left_seats] += 1
    right_bloc_seat_results[right_seats] += 1

    majority = total_seats // 2 + 1

    left = left_seats
    right = right_seats

    if left >= majority: left_wins += 1
    if right >= majority: right_wins += 1

    nat_act = final_seats.get("National", 0) + final_seats.get("ACT", 0)
    lab_grn = final_seats.get("Labour", 0) + final_seats.get("Greens", 0)
    lab_grn_nzf = lab_grn + final_seats.get("NZ First", 0)

    nat_act_nzf_opp = nat_act + final_seats.get("NZ First", 0) + final_seats.get("Opportunity", 0)
    lab_grn_tpm_opp = lab_grn + final_seats.get("TPM", 0) + final_seats.get("Opportunity", 0)
    lab_grn_opp = lab_grn + final_seats.get("Opportunity", 0)
    lab_nzf = final_seats.get("Labour", 0) + final_seats.get("NZ First", 0)
    nat_nzf = final_seats.get("National", 0) + final_seats.get("NZ First", 0)
    nat_grn = final_seats.get("National", 0) + final_seats.get("Greens", 0)
    grn_nzf_opp_act_tpm = (
        final_seats.get("Greens", 0)
        + final_seats.get("NZ First", 0)
        + final_seats.get("Opportunity", 0)
        + final_seats.get("ACT", 0)
        + final_seats.get("TPM", 0)
    )



    nat_nzf_grn = final_seats.get("National", 0) + final_seats.get("NZ First", 0) + final_seats.get("Greens", 0)
    lab_act = final_seats.get("Labour", 0) + final_seats.get("ACT", 0)
    lab_act_nzf = lab_act + final_seats.get("NZ First", 0)
    nat_lab = final_seats.get("National", 0) + final_seats.get("Labour", 0)
    lab_nzf_tpm = final_seats.get("Labour", 0) + final_seats.get("NZ First", 0) + final_seats.get("TPM", 0)

    if nat_act >= majority: nat_act_wins += 1
    if lab_grn >= majority: lab_grn_wins += 1
    if lab_grn_nzf >= majority: lab_grn_nzf_wins += 1

    if nat_act_nzf_opp >= majority: nat_act_nzf_opp_wins += 1
    if lab_grn_tpm_opp >= majority: lab_grn_tpm_opp_wins += 1
    if lab_grn_opp >= majority: lab_grn_opp_wins += 1
    if lab_nzf >= majority: lab_nzf_wins += 1
    if nat_nzf >= majority: nat_nzf_wins += 1
    if nat_grn >= majority: nat_grn_wins += 1
    if grn_nzf_opp_act_tpm >= majority: grn_nzf_opp_act_tpm_wins += 1

    if nat_nzf_grn >= majority: nat_nzf_grn_wins += 1
    if lab_act >= majority: lab_act_wins += 1
    if lab_act_nzf >= majority: lab_act_nzf_wins += 1
    if nat_lab >= majority: nat_lab_wins += 1
    if lab_nzf_tpm >= majority: lab_nzf_tpm_wins += 1




# outputs

def pct(x): return x / NUM_SIMULATIONS * 100.0

print("\n=== RAW AVERAGE PARTY VOTE (PURE GAUSSIAN INPUTS) ===")
for p, total in raw_total_party_votes.items():
    print(f"{p}: {total / NUM_SIMULATIONS:.3f}")

print("\n=== POST-SCALING AVERAGE PARTY VOTE (AFTER NORMALIZATION) ===")
for p, total in total_party_votes.items():
    print(f"{p}: {total / NUM_SIMULATIONS:.3f}")

print("\n=== AVERAGE FINAL SEATS ===")
for p in party_names:
    print(f"{p}: {total_final_seats[p] / NUM_SIMULATIONS:.3f}")

print("\n=== GOVERNING PROBABILITIES ===")
print(f"Left bloc: {pct(left_wins):.1f}%")
print(f"Right bloc: {pct(right_wins):.1f}%")
print(f"Left bloc + Opportunity: {pct(lab_grn_tpm_opp_wins):.1f}%")
print(f"Right bloc + Opportunity: {pct(nat_act_nzf_opp_wins):.1f}%")
print(f"National + ACT: {pct(nat_act_wins):.1f}%")
print(f"Labour + Greens: {pct(lab_grn_wins):.1f}%")
print(f"Labour + Greens + Opportunity: {pct(lab_grn_opp_wins):.1f}%")
print(f"Labour + Greens + NZ First: {pct(lab_grn_nzf_wins):.1f}%")

print("\n=== ADDITIONAL COALITIONS ===")
print(f"National + NZ First + Greens: {pct(nat_nzf_grn_wins):.1f}%")
print(f"Labour + ACT: {pct(lab_act_wins):.1f}%")
print(f"Labour + ACT + NZ First: {pct(lab_act_nzf_wins):.1f}%")
print(f"National + Labour: {pct(nat_lab_wins):.1f}%")
print(f"Labour + NZ First + TPM: {pct(lab_nzf_tpm_wins):.1f}%")

# Seat distribution table

print("\n=== SEAT DISTRIBUTION TABLE (SPACE-SEPARATED, SHEETS READY) ===")
print("Seat Labour National Greens ACT NZFirst TPM Opportunity LeftBloc RightBloc")

# Determine full seat range across parties and blocs
all_seat_values = set()
for p in party_names:
    all_seat_values.update(seat_results[p].keys())
all_seat_values.update(left_bloc_seat_results.keys())
all_seat_values.update(right_bloc_seat_results.keys())

min_seat = min(all_seat_values)
max_seat = max(all_seat_values)

for seat in range(min_seat, max_seat + 1):
    row = [seat]

    # Party seat distributions 
    for p in party_names:
        row.append(seat_results[p].get(seat, 0))

    # Bloc seat distributions 
    row.append(left_bloc_seat_results.get(seat, 0))
    row.append(right_bloc_seat_results.get(seat, 0))

    print(*row, sep=" ")

# overhang table ( mostly for debugging purposes )

print("\n=== OVERHANG SEAT DISTRIBUTION TABLE (SPACE-SEPARATED) ===")
print("Overhang Labour National Greens ACT NZFirst TPM Opportunity")


# Determine full overhang range
all_overhang_values = set()
for p in party_names:
    all_overhang_values.update(overhang_results[p].keys())

min_ov = min(all_overhang_values)
max_ov = max(all_overhang_values)

# print table
for ov in range(min_ov, max_ov + 1):
    row = [ov]
    for p in party_names:
        row.append(overhang_results[p].get(ov, 0))
    print(*row, sep=" ")

