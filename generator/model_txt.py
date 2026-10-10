"""Writes c3_model.txt: building costs/desirability/labour and house evolution requirements.

Parsed by src/building/model.c: after "ALL BUILDINGS" exactly 130 + 20 '{' lines, each value
is read by skipping to the next digit/minus sign and then past the next comma, so every line
ends with a trailing comma and names contain no digits.
"""

# type: (name, cost, des_value, des_step, des_step_size, des_range, laborers)
B = {
    5: ("Road", 4, 0, 0, 0, 0, 0),
    6: ("Wall", 12, 0, 0, 0, 0, 0),
    8: ("Aqueduct", 8, 0, 0, 0, 0, 0),
    9: ("Clear land", 2, 0, 0, 0, 0, 0),
    10: ("Small tent", 10, -2, 1, 1, 3, 0),
    11: ("Large tent", 10, -2, 1, 1, 3, 0),
    12: ("Small shack", 10, -2, 1, 1, 3, 0),
    13: ("Large shack", 10, -2, 1, 1, 3, 0),
    14: ("Small hovel", 10, -2, 1, 1, 2, 0),
    15: ("Large hovel", 10, -2, 1, 1, 2, 0),
    16: ("Small casa", 10, -1, 1, 1, 1, 0),
    17: ("Large casa", 10, -1, 1, 1, 1, 0),
    18: ("Small insula", 10, 0, 1, 0, 0, 0),
    19: ("Medium insula", 10, 0, 1, 0, 0, 0),
    20: ("Large insula", 10, 0, 1, 0, 0, 0),
    21: ("Grand insula", 10, 0, 1, 0, 0, 0),
    22: ("Small villa", 10, 1, 1, -1, 1, 0),
    23: ("Medium villa", 10, 1, 1, -1, 1, 0),
    24: ("Large villa", 10, 2, 1, -1, 2, 0),
    25: ("Grand villa", 10, 2, 1, -1, 2, 0),
    26: ("Small palace", 10, 3, 1, -1, 3, 0),
    27: ("Medium palace", 10, 3, 1, -1, 3, 0),
    28: ("Large palace", 10, 4, 1, -1, 4, 0),
    29: ("Luxury palace", 10, 4, 1, -1, 4, 0),
    30: ("Amphitheater", 100, 4, 1, -1, 4, 12),
    31: ("Theater", 50, 2, 1, -1, 2, 8),
    32: ("Hippodrome", 2500, -3, 1, 1, 3, 150),
    33: ("Colosseum", 500, -3, 1, 1, 3, 25),
    34: ("Gladiator school", 75, -3, 1, 1, 3, 8),
    35: ("Lion house", 75, -3, 1, 1, 3, 8),
    36: ("Actor colony", 50, 2, 1, -1, 2, 5),
    37: ("Chariot maker", 75, -3, 1, 1, 3, 10),
    38: ("Plaza", 15, 4, 1, -2, 2, 0),
    39: ("Gardens", 12, 3, 1, -1, 3, 0),
    40: ("Fort legionaries", 1000, -20, 2, 2, 8, 0),
    41: ("Small statue", 12, 3, 1, -1, 3, 0),
    42: ("Medium statue", 60, 10, 1, -2, 4, 0),
    43: ("Large statue", 150, 14, 2, -2, 5, 0),
    44: ("Fort javelin", 1000, -20, 2, 2, 8, 0),
    45: ("Fort mounted", 1000, -20, 2, 2, 8, 0),
    46: ("Doctor", 30, 0, 0, 0, 0, 5),
    47: ("Hospital", 300, -1, 2, 1, 2, 30),
    48: ("Bathhouse", 50, 4, 1, -1, 4, 10),
    49: ("Barber", 25, 2, 1, -1, 2, 2),
    51: ("School", 50, -2, 1, 1, 2, 10),
    52: ("Academy", 100, 4, 1, -1, 4, 30),
    53: ("Library", 75, 4, 1, -1, 4, 20),
    55: ("Prefecture", 30, -2, 1, 1, 2, 6),
    56: ("Triumphal arch", 0, 18, 3, -3, 5, 0),
    57: ("Fort", 1000, -20, 2, 2, 8, 0),
    58: ("Gatehouse", 100, -4, 1, 1, 3, 0),
    59: ("Tower", 150, -8, 1, 2, 3, 6),
    60: ("Small temple Ceres", 50, 4, 2, -1, 6, 2),
    61: ("Small temple Neptune", 50, 4, 2, -1, 6, 2),
    62: ("Small temple Mercury", 50, 4, 2, -1, 6, 2),
    63: ("Small temple Mars", 50, 4, 2, -1, 6, 2),
    64: ("Small temple Venus", 50, 4, 2, -1, 6, 2),
    65: ("Large temple Ceres", 150, 8, 2, -1, 8, 5),
    66: ("Large temple Neptune", 150, 8, 2, -1, 8, 5),
    67: ("Large temple Mercury", 150, 8, 2, -1, 8, 5),
    68: ("Large temple Mars", 150, 8, 2, -1, 8, 5),
    69: ("Large temple Venus", 150, 8, 2, -1, 8, 5),
    70: ("Market", 40, -2, 1, 1, 6, 5),
    71: ("Granary", 100, -4, 1, 2, 2, 12),
    72: ("Warehouse", 70, -5, 2, 2, 3, 6),
    74: ("Shipyard", 100, -8, 1, 2, 3, 10),
    75: ("Dock", 100, -8, 2, 2, 3, 12),
    76: ("Wharf", 60, -8, 2, 2, 3, 6),
    77: ("Governors house", 150, 12, 2, -2, 3, 0),
    78: ("Governors villa", 400, 20, 2, -3, 4, 0),
    79: ("Governors palace", 700, 28, 2, -4, 5, 0),
    80: ("Mission post", 100, -3, 1, 1, 4, 20),
    81: ("Engineers post", 30, 0, 0, 0, 0, 5),
    82: ("Low bridge", 40, 0, 0, 0, 0, 0),
    83: ("Ship bridge", 100, 0, 0, 0, 0, 0),
    85: ("Senate", 400, 8, 2, -2, 4, 30),
    86: ("Forum", 75, 3, 2, -1, 2, 6),
    88: ("Native hut", 50, 0, 0, 0, 0, 0),
    89: ("Native meeting", 50, 0, 0, 0, 0, 0),
    90: ("Reservoir", 80, -6, 1, 2, 3, 0),
    91: ("Fountain", 15, 0, 0, 0, 0, 4),
    92: ("Well", 5, -1, 1, 2, 1, 0),
    94: ("Military academy", 1000, -3, 1, 1, 3, 20),
    95: ("Barracks", 150, -6, 1, 1, 3, 10),
    98: ("Oracle", 200, 8, 2, -1, 6, 0),
    100: ("Wheat farm", 40, -2, 1, 1, 2, 10),
    101: ("Vegetable farm", 40, -2, 1, 1, 2, 10),
    102: ("Fruit farm", 40, -2, 1, 1, 2, 10),
    103: ("Olive farm", 40, -2, 1, 1, 2, 10),
    104: ("Vines farm", 40, -2, 1, 1, 2, 10),
    105: ("Pig farm", 40, -2, 1, 1, 2, 10),
    106: ("Marble quarry", 50, -6, 1, 1, 4, 10),
    107: ("Iron mine", 50, -6, 1, 1, 4, 10),
    108: ("Timber yard", 40, -4, 1, 1, 3, 10),
    109: ("Clay pit", 40, -3, 1, 1, 2, 10),
    110: ("Wine workshop", 45, -4, 1, 1, 2, 10),
    111: ("Oil workshop", 50, -4, 1, 1, 2, 10),
    112: ("Weapons workshop", 50, -4, 1, 1, 2, 10),
    113: ("Furniture workshop", 40, -4, 1, 1, 2, 10),
    114: ("Pottery workshop", 40, -4, 1, 1, 2, 10),
}

# devolve, evolve, entertainment, water, religion, education, -, barber, bathhouse, health,
# food types, pottery, oil, furniture, wine, -, -, prosperity, max people, tax multiplier
H = [
    ("Small tent", -99, -10, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 5, 1),
    ("Large tent", -12, -5, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 10, 7, 1),
    ("Small shack", -7, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 15, 9, 1),
    ("Large shack", -2, 4, 0, 1, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 20, 11, 1),
    ("Small hovel", 2, 8, 0, 2, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 25, 13, 2),
    ("Large hovel", 6, 12, 10, 2, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 30, 15, 2),
    ("Small casa", 10, 16, 10, 2, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 35, 16, 2),
    ("Large casa", 14, 20, 10, 2, 1, 1, 0, 0, 1, 0, 1, 1, 0, 0, 0, 0, 0, 40, 17, 2),
    ("Small insula", 18, 25, 25, 2, 1, 1, 0, 0, 1, 0, 1, 1, 0, 0, 0, 0, 0, 45, 18, 3),
    ("Medium insula", 22, 32, 25, 2, 1, 1, 0, 0, 1, 1, 1, 1, 0, 1, 0, 0, 0, 50, 19, 3),
    ("Large insula", 29, 40, 25, 2, 1, 2, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 55, 80, 3),
    ("Grand insula", 37, 48, 35, 2, 2, 2, 0, 1, 1, 1, 2, 1, 1, 1, 0, 0, 0, 60, 84, 4),
    ("Small villa", 45, 53, 35, 2, 2, 2, 0, 1, 1, 1, 2, 1, 1, 1, 1, 0, 0, 70, 40, 9),
    ("Medium villa", 50, 58, 40, 2, 2, 3, 0, 1, 1, 1, 2, 1, 1, 1, 1, 0, 0, 80, 42, 10),
    ("Large villa", 55, 63, 45, 2, 3, 3, 0, 1, 1, 2, 2, 1, 1, 1, 1, 0, 0, 90, 90, 11),
    ("Grand villa", 60, 68, 50, 2, 3, 3, 0, 1, 1, 2, 3, 1, 1, 1, 1, 0, 0, 100, 94, 11),
    ("Small palace", 65, 74, 55, 2, 3, 3, 0, 1, 1, 2, 3, 1, 1, 1, 2, 0, 0, 110, 100, 12),
    ("Medium palace", 70, 80, 60, 2, 4, 3, 0, 1, 1, 2, 3, 1, 1, 1, 2, 0, 0, 120, 106, 13),
    ("Large palace", 76, 90, 70, 2, 4, 3, 0, 1, 1, 2, 3, 1, 1, 1, 2, 0, 0, 140, 112, 14),
    ("Luxury palace", 85, 100, 80, 2, 4, 3, 0, 1, 1, 2, 3, 1, 1, 1, 2, 0, 0, 160, 200, 15),
]


def write(path):
    lines = ["Building and house model data (generated)", "", "ALL BUILDINGS"]
    for t in range(130):
        name, *vals = B.get(t, ("Unused", 0, 0, 0, 0, 0, 0))
        nums = list(vals) + [0, 0]
        lines.append("{ " + ", ".join(str(v) for v in nums) + ", } " + name)
    lines += ["", "ALL HOUSES"]
    for name, *vals in H:
        assert len(vals) == 20
        lines.append("{ " + ", ".join(str(v) for v in vals) + ", } " + name)
    with open(path, "w", newline="\r\n") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    import sys
    write(sys.argv[1])
