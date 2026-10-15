import json
import urllib.parse
import urllib.request

import pandas as pd
import openmeteo_requests
import numpy as np

import random
import sys

# """
# First chunk: Converts NOAA Bouy data from website into useable data w/ standard timestamp
# Second chunk: 
# Third chunk: Wind Data
# """
# noaa_bouy = pd.read_csv("https://www.ndbc.noaa.gov/view_text_file.php?filename=46274h2025.txt.gz&dir=data/historical/stdmet/",
#                     header=0,
#                     skiprows=[1],
#                     sep=r'\s+',
#                     usecols=['#YY', 'MM', 'DD', 'hh', 'mm', 'WVHT', 'DPD', 'APD', 'MWD'])

# noaa_bouy["timestamp"] = pd.to_datetime({"year": noaa_bouy["#YY"],
#                                      "month": noaa_bouy["MM"],
#                                      "day": noaa_bouy["DD"],
#                                      "hour": noaa_bouy["hh"], 
#                                      "minute": noaa_bouy["mm"]})

# noaa_bouy.drop(columns=['#YY', 'MM', 'DD', 'hh', 'mm'], inplace=True)
# noaa_bouy.insert(0, "timestamp", noaa_bouy.pop('timestamp'))

# # print(noaa_bouy.head())
# # print(data.dtypes) # - Checks if data types correct





# openmeteo = openmeteo_requests.Client()

# url = "https://archive-api.open-meteo.com/v1/archive"
# params = {
# 	"latitude": 33.063000,
# 	"longitude": -117.304000,
# 	"start_date": "2025-01-01",
# 	"end_date": "2025-12-31",
# 	"hourly": ["wind_speed_10m", "wind_direction_10m"],
# 	"timezone": "auto",
# 	"utm_source": "chatgpt.com",
# }
# responses = openmeteo.weather_api(url, params = params)

# response = responses[0]
# # print(f"Coordinates: {response.Latitude()}°N {response.Longitude()}°E")
# # print(f"Elevation: {response.Elevation()} m asl")
# # print(f"Timezone: {response.Timezone()}{response.TimezoneAbbreviation()}")
# # print(f"Timezone difference to GMT+0: {response.UtcOffsetSeconds()}s")


# # Process hourly data. The order of variables needs to be the same as requested.
# hourly = response.Hourly()
# hourly_wind_speed_10m = hourly.Variables(0).ValuesAsNumpy()
# hourly_wind_direction_10m = hourly.Variables(1).ValuesAsNumpy()

# hourly_data = {
# 	"date": pd.date_range(
# 		start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
# 		end =  pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
# 		freq = pd.Timedelta(seconds = hourly.Interval()),
# 		inclusive = "left"
# 	).tz_convert(response.Timezone().decode())
# }

# hourly_data["wind_speed_10m"] = hourly_wind_speed_10m
# hourly_data["wind_direction_10m"] = hourly_wind_direction_10m

# hourly_dataframe = pd.DataFrame(data = hourly_data)
# # print("\nHourly data\n", hourly_dataframe)

# print(len(noaa_bouy[::2]), len(hourly_dataframe))

# data = pd.DataFrame(pd.concat([noaa_bouy[::2], hourly_dataframe], axis=1))

# # print(data.head)


# for row1, row2 in zip(noaa_bouy.itertuples(), hourly_dataframe.itertuples()):
#     if row1[0] != row2[0]:
#         print(row1[0], row2[0])



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
 
# Convert to local time at the end (tz-aware, so DST is handled correctly)
data.index = data.index.tz_convert(LOCAL_TZ)

BEACH_FACING = 249

rel = np.deg2rad((data["wind_direction_10m"] - BEACH_FACING) % 360)
data["wind_offshore"] = -data["wind_speed_10m"] * np.cos(rel)  # + = offshore, - = onshore
data["wind_cross"]    =  abs(data["wind_speed_10m"] * np.sin(rel))  # sideways component

data = data.drop(["wind_speed_10m", "wind_direction_10m"], axis=1)

# print(data.sample(n=20))
# print(f"\n{len(data)} hours total")
# print("Missing values per column:\n", data.isna().sum())






"""

Dataset!!! (And my general grading guidelines):

- Swell Angle:
    Best	270°-285° (W to WNW)	Hits the reef head-on. Creates perfectly shaped, peeling A-frame peaks with clean rights and lefts. Handles size well.
    Second Best	285°-300° (WNW to NW)	Punchy and consistent winter swell angle. Can get a bit sectiony or walled up, but offers fast, fun rights.
    Average	210°-240° (SW to WSW)	Soft, slower, and cleaner lines. Fun for longboarding and mid-lengths, but lacks the hollow punch of a western groundswell.
    Second Worst	200°-210° (SSW)	Heavily shadowed and blocked by the Channel Islands. Mostly small, inconsistent, and mushy lines sneak through.
    Worst	180°-199° (S to SSW) & 305°+ (Deep NW)	Fully blocked or shadowed. South swells under 200° completely miss the reef, while deep NW swells pass too far offshore or get blocked by Point Conception.
(The rest I know well enough to keep broad)
- Swell height: above 0.9 is ideal, lower is pretty meh unless period is higher than like 15
- Dominant period needs to be above 10, above 14 is quite good and 18+ is GOOD surf unless wind sucksssss
- Wind should be as low as possible if onshore, and up to like 10 if offshore. Side winds minimal.
- Ideal tide is between 0.5-2.5 feet. High high tide much worse than low low tide unless high period then both fine

"""



"""
Code to get my data:
input - data

output - one random data piece for each day of the year of data
"""

SEED = 57295
TIME_COL = "timestamp"

def one_data_per_day(df: pd.DataFrame, time_col=TIME_COL, seed=SEED):
   
    samples = df.groupby(df.index.date, group_keys=False).sample(n=1, random_state=seed).sort_index()
    return samples

def make_swell_direction_easy(df: pd.DataFrame):
    df["MWD"] = df["MWD"].apply(check_direction)
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


samples = one_data_per_day(make_swell_direction_easy(data))
samples = samples.rename(columns={"WVHT": "WVHT_ft"})
samples["WVHT_ft"] = (samples["WVHT_ft"] * 3.281).round(1)   # NOAA gives meters; feet are easier to judge
samples["rating"] = ""
# samples.to_csv("data/to_rate.csv")

