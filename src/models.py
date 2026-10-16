from data_collection import *

import pandas as pd
import numpy as np
import random


DATA = make_stuff_easy(load_data())

"""
Generic model:

Rules (And my general grading guidelines):
Starts with number ourly based on wave height in feet: .7ft or lower -> 1, 1.5ft -> 3,  2.3ft -> 5, 3.4ft -> 7, 4.5+ -> 8
Wind next to quickly weed out wind swells: -10 or lower -> -4, -5 -> -2, 0 -> +0.5, 5 -> +2, 10 or more -> +1
Cross shore: 10 or higher: -2, 6 -> -1, 4 -> 0, 0 -> +0.5
Period: Less than 7 -> -3, 10 -> -1, 13 -> +1, 17 -> +2
Avg period: Less than 10 -> -0.5, 10 or more -> +0.5
Tide: Greater than 3.5 -> -2, 3 -> -1, 2.4 -> 0, 1.2 -> +1, 0.5 -> 0, -0.8 -> -1, lower than -0.8 -> -1.5
Swell angle: Worst -> -2, Second worst -> -1, Average -> 0, Second best -> +0.5, Best -> +1
"""
DIRECTION_POINTS = {"Worst": -2, "Second worst": -1, "Average": 0,
                    "Second best": 0.5, "Best": 1}

def generic_model(row):
    score = np.interp(row["WVHT_ft"], [1, 1.5, 2.3, 3.4, 4.5], [1, 3, 5, 7, 8])
    score += np.interp(row["wind_offshore"], [-10, -5, 0, 5, 10], [-4, -2, 0, 2, 1])
    score += np.interp(row["wind_cross"], [10, 6, 4, 0], [-2, -1, 0, 0.5])
    score += np.interp(row["DPD"], [7, 10, 13, 17], [-3, -1, 1, 2])
    score += 0.5 if row["APD"] >= 7 else -0.5
    score += np.interp(row["tide_ft"], [3.5, 3, 2.4, 1.2, 0.5, -0.8, -1.5], [-2, -1, 0, 1, 1, -1, -1.5])
    score += DIRECTION_POINTS.get(row["MWD"])

    if row["WVHT_ft"] < 1:
        score = min(score, 2)
    return float(np.clip(score, 0, 10))

print(generic_model(DATA.iloc[1]))

