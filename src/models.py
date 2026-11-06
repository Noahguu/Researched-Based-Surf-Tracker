from data_collection import *

from sklearn.model_selection import RepeatedKFold, cross_val_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import learning_curve
# Models being used:
from tabpfn import TabPFNRegressor
from sklearn.gaussian_process.kernels import RBF, WhiteKernel
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.neighbors import KNeighborsRegressor
from sklearn.gaussian_process import GaussianProcessRegressor
from xgboost import XGBRegressor

import pandas as pd
import numpy as np
import random
import json


import warnings
from sklearn.exceptions import ConvergenceWarning
warnings.filterwarnings("ignore", category=ConvergenceWarning)


DATA = make_stuff_easy(load_data())





"""
Baseline model:

Always returns the average score for all of the scores from my data set
"""
def average(df: pd.Series):
    return f"A mean of {df.mean(numeric_only=True)} and an S.D. of {df.std(numeric_only=True)}"



# ------------------------------------- #




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
    score += np.interp(row["wind_cross"], [0, 4, 6, 10], [0.5, 0, -1, -2])
    score += np.interp(row["DPD"], [7, 10, 13, 17], [-3, -1, 1, 2])
    score += 0.5 if row["APD"] >= 7 else -0.5
    score += np.interp(row["tide_ft"], [-1.5, -0.8, 0.5, 1.2, 2.4, 3, 3.5], [-1.5, -1, 1, 1, 0, -1, -2])
    score += DIRECTION_POINTS.get(row["MWD"])

    if row["WVHT_ft"] < 1:
        score = min(score, 2)
    return float(np.clip(score, 0, 10))

# print(generic_model(DATA.iloc[1]))




# ------------------------------------- #



"""
Makes the models and sets parameters; places them in dictionary
"""
def make_models():
    model_dict = {"ridge": make_pipeline(StandardScaler(), Ridge()),
                  "random_forest": make_pipeline(StandardScaler(), RandomForestRegressor(random_state=33)),
                  "neural_network": make_pipeline(StandardScaler(), MLPRegressor(max_iter=2000, random_state=33)),
                  "kNN": make_pipeline(StandardScaler(), KNeighborsRegressor()),
                  "gaussian_process": make_pipeline(StandardScaler(), GaussianProcessRegressor(kernel=RBF() + WhiteKernel(), normalize_y=True, random_state=33)),
                  "xgboost": make_pipeline(StandardScaler(), XGBRegressor(random_state=33)),
                  "tabpfn": make_pipeline(StandardScaler(), TabPFNRegressor(random_state=33))
                }
    return model_dict




# --- Format data for model testing --- #
df = pd.read_csv("data/rated_data.csv")
df = df.dropna(subset=["WVHT_ft", "rating"])
df.reset_index(drop=True, inplace=True)


df["MWD"] = df["MWD"].map({
                  "Best": 3,
                  "Second best": 2,
                  "Average": 1,
                  "Second worst": 0
                 })

x = df[["WVHT_ft", "DPD", "APD", "MWD", "tide_ft", "wind_offshore", "wind_cross"]]
y = df["rating"]



print(average(y))
# ------------------------------------- #


CLEAN_PATH = Path("data/model_results.json")
"""
Tests and evaluates a model for its full data set
"""
def evaluate(model, X: pd.DataFrame, y: pd.Series):
    cv = RepeatedKFold(n_splits=10, n_repeats=5, random_state=33)
    scores = cross_val_score(model, X, y, cv=cv, scoring="neg_mean_absolute_error")

    return float(-scores.mean()), float(scores.std())


"""
Evaluates model at different input sizes
"""
def split(model, X: pd.DataFrame, y: pd.Series, input_sizes):
    cv = RepeatedKFold(n_splits=10, n_repeats=5, random_state=33)

    sizes, _, test_scores = learning_curve(model, X, y, train_sizes=input_sizes, cv=cv, scoring="neg_mean_absolute_error")

    return sizes, -test_scores.mean(axis=1), test_scores.std(axis=1)






# --- Running evaluate function on each model and displaying results --- #
def run_stuff():
    results = {}
    for name, model in make_models().items():
        results[name] = evaluate(model, x, y)
        print(f'The {name} model produced a standard error and S.D. of {results[name]}')



    curves = {}
    for name, model in make_models().items():
        curves[name] = split(model, x, y, [10, 25, 50, 75, 100, 150])
        print(f'The {name} model produced {curves[name]}')


    out = {
    "overall": {n: list(map(float, r)) for n, r in results.items()},          # [mae, sd]
    "curves": {n: {"sizes": list(map(int, s)), "mae": list(map(float, m)), "sd": list(map(float, sd))}
           for n, (s, m, sd) in curves.items()},
}
    json.dump(out, open("data/model_results.json", "w"), indent=2)

    return results, curves

if not CLEAN_PATH.exists():
    run_stuff()







# OMP_NUM_THREADS=1 caffeinate -i python3 src/models.py