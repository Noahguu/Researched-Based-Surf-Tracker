import pandas as pd
import openmeteo_requests

"""
First chunk: Converts NOAA Bouy data from website into useable data w/ standard timestamp
Second chunk: 
Third chunk: Wind Data
"""
noaa_bouy = pd.read_csv("https://www.ndbc.noaa.gov/view_text_file.php?filename=46274h2025.txt.gz&dir=data/historical/stdmet/",
                    header=0,
                    skiprows=[1],
                    sep=r'\s+',
                    usecols=['#YY', 'MM', 'DD', 'hh', 'mm', 'WVHT', 'DPD', 'APD', 'MWD'])

noaa_bouy["timestamp"] = pd.to_datetime({"year": noaa_bouy["#YY"],
                                     "month": noaa_bouy["MM"],
                                     "day": noaa_bouy["DD"],
                                     "hour": noaa_bouy["hh"], 
                                     "minute": noaa_bouy["mm"]})

noaa_bouy.drop(columns=['#YY', 'MM', 'DD', 'hh', 'mm'], inplace=True)
noaa_bouy.insert(0, "timestamp", noaa_bouy.pop('timestamp'))

# print(noaa_bouy.head())
# print(data.dtypes) # - Checks if data types correct





openmeteo = openmeteo_requests.Client()

url = "https://archive-api.open-meteo.com/v1/archive"
params = {
	"latitude": 33.063000,
	"longitude": -117.304000,
	"start_date": "2025-01-01",
	"end_date": "2025-12-31",
	"hourly": ["wind_speed_10m", "wind_direction_10m"],
	"timezone": "auto",
	"utm_source": "chatgpt.com",
}
responses = openmeteo.weather_api(url, params = params)

response = responses[0]
# print(f"Coordinates: {response.Latitude()}°N {response.Longitude()}°E")
# print(f"Elevation: {response.Elevation()} m asl")
# print(f"Timezone: {response.Timezone()}{response.TimezoneAbbreviation()}")
# print(f"Timezone difference to GMT+0: {response.UtcOffsetSeconds()}s")


# Process hourly data. The order of variables needs to be the same as requested.
hourly = response.Hourly()
hourly_wind_speed_10m = hourly.Variables(0).ValuesAsNumpy()
hourly_wind_direction_10m = hourly.Variables(1).ValuesAsNumpy()

print(hourly_wind_direction_10m, hourly_wind_speed_10m)