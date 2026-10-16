import json
import urllib.parse
import urllib.request
from pathlib import Path


import pandas as pd
import openmeteo_requests
import numpy as np

import random
import sys


CLEAN_PATH = Path("data/raw_data.csv")

# If data set updated, run function with rebuild=True or just delete file manually I suppose
def load_data(rebuild=False):
    if CLEAN_PATH.exists and not rebuild:
        data = pd.read_csv(CLEAN_PATH)
        data["timestamp"] = pd.to_datetime(data["timestamp"], utc=True).dt.tz_convert("America/Los_Angeles")
        return data.set_index("timestamp")
    
    """
    1. NOAA buoy 46274: wave data -> hourly, UTC
    2. Open-Meteo archive: wind data -> hourly, UTC
    3. Merge on timestamp (not row position), then convert to local time
    """
    
    LOCAL_TZ = "America/Los_Angeles"
    
    # ---------------------------------------------------------------------------
    # 1. NOAA buoy 
    # ---------------------------------------------------------------------------
    BUOY_URL = ("https://www.ndbc.noaa.gov/view_text_file.php?"
                "filename=46274h2025.txt.gz&dir=data/historical/stdmet/")
    
    buoy = pd.read_csv(
        BUOY_URL,
        sep=r"\s+",
        header=0,
        skiprows=[1],
        usecols=["#YY", "MM", "DD", "hh", "mm", "WVHT", "DPD", "APD", "MWD"],
    )
    
    time_cols = ["#YY", "MM", "DD", "hh", "mm"]
    buoy["timestamp"] = pd.to_datetime(
        buoy[time_cols].set_axis(["year", "month", "day", "hour", "minute"], axis=1),
        utc=True,
    )
    buoy = buoy.drop(columns=time_cols).set_index("timestamp").sort_index()
    
    # NDBC writes missing values as 99 / 999 instead of leaving them blank
    buoy = buoy.replace({
        "WVHT": {99.0: np.nan},
        "DPD": {99.0: np.nan},
        "APD": {99.0: np.nan},
        "MWD": {999: np.nan},
    })
    
    # Collapse the 30-min readings into hourly buckets.
    # Direction is circular (350 and 10 should average to 0, not 180),
    # so average its sin/cos components instead of the raw degrees.
    rad = np.deg2rad(buoy["MWD"])
    buoy["_sin"] = np.sin(rad)
    buoy["_cos"] = np.cos(rad)
    
    buoy_hourly = buoy.resample("1h").mean()
    buoy_hourly["MWD"] = np.rad2deg(np.arctan2(buoy_hourly["_sin"], buoy_hourly["_cos"])) % 360
    buoy_hourly = buoy_hourly.drop(columns=["_sin", "_cos"])
    
    # ---------------------------------------------------------------------------
    # 2. Open-Meteo wind 
    # ---------------------------------------------------------------------------
    openmeteo = openmeteo_requests.Client()
    params = {
        "latitude": 33.063,
        "longitude": -117.304,
        "start_date": "2025-01-01",
        "end_date": "2025-12-31",
        "hourly": ["wind_speed_10m", "wind_direction_10m"],
        "timezone": "GMT",
    }
    response = openmeteo.weather_api("https://archive-api.open-meteo.com/v1/archive", params=params)[0]
    hourly = response.Hourly()
    
    wind = pd.DataFrame(
        {
            "wind_speed_10m": hourly.Variables(0).ValuesAsNumpy(),
            "wind_direction_10m": hourly.Variables(1).ValuesAsNumpy(),
        },
        index=pd.date_range(
            start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
            end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=hourly.Interval()),
            inclusive="left",
            name="timestamp",
        ),
    )

    # ---------------------------------------------------------------------------
    # 3. NOAA CO-OPS tide gauge (time_zone=GMT, so already UTC)
    #    The API allows at most 1 year per request for hourly_height.
    # ---------------------------------------------------------------------------
    tide_params = {
        "product": "hourly_height",
        "application": "NOS.COOPS.TAC.WL",
        "begin_date": "20250101",
        "end_date": "20251231",
        "datum": "MLLW",
        "station": "9410230",
        "time_zone": "GMT",
        "units": "english",
        "format": "json",
    }
    tide_url = ("https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?"
                + urllib.parse.urlencode(tide_params))
    with urllib.request.urlopen(tide_url, timeout=60) as r:
        tide_json = json.load(r)
    if "error" in tide_json:  # bad params come back as {"error": {...}}, not an HTTP error
        raise RuntimeError(tide_json["error"])
    
    tide = pd.DataFrame(tide_json["data"])
    tide["timestamp"] = pd.to_datetime(tide["t"], utc=True)
    tide["tide_ft"] = pd.to_numeric(tide["v"], errors="coerce")  # values arrive as strings; blanks -> NaN
    tide = tide.set_index("timestamp")[["tide_ft"]]


    # ---------------------------------------------------------------------------
    # 4. Merge on timestamp
    # ---------------------------------------------------------------------------
    # Wind has a complete hourly grid, so use it as the base; hours where the
    # buoy was offline show up as NaN instead of shifting everything after them.
    data = wind.join([buoy_hourly, tide], how="left")
    
    # Convert to local time at the end
    data.index = data.index.tz_convert(LOCAL_TZ)

    BEACH_FACING = 249

    rel = np.deg2rad((data["wind_direction_10m"] - BEACH_FACING) % 360)
    data["wind_offshore"] = -data["wind_speed_10m"] * np.cos(rel)  # + = offshore, - = onshore
    data["wind_cross"]    =  abs(data["wind_speed_10m"] * np.sin(rel))  # sideways component

    data = data.drop(["wind_speed_10m", "wind_direction_10m"], axis=1)


    data.to_csv(CLEAN_PATH)
    return data




# Test data randomly selected here
SEED = 57295
data = load_data()

def one_data_per_day(df: pd.DataFrame, seed=SEED):
   
    samples = df.groupby(df.index.date, group_keys=False).sample(n=1, random_state=seed).sort_index()
    return samples


# Data formatted specifically to make it easier for me, a human, to grade, but nothing changed from raw data technically
def make_stuff_easy(df: pd.DataFrame):
    df["MWD"] = df["MWD"].apply(check_direction)
    df = df.rename(columns={"WVHT": "WVHT_ft"})
    df["WVHT_ft"] = (df["WVHT_ft"] * 3.281).round(1)   # NOAA gives meters; feet are easier to judge for me at least
    return df

def check_direction(direction: int):
    if direction < 200:
        return 'Worst'
    elif direction < 225:
        return 'Second worst'
    elif direction < 255:
        return 'Average'
    elif direction < 280:
        return 'Best'
    return 'Second best'


samples = one_data_per_day(make_stuff_easy(data))
samples["rating"] = ""



