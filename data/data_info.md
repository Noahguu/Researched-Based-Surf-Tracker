# Data source: 

## NOAA bouy NDBC station 46237 for 2025

### Link: https://www.ndbc.noaa.gov/view_text_file.php?filename=46237h2025.txt.gz&dir=data/historical/stdmet/

### Provides:
- Day, month, time for every 30 minutes (In UTC)
- Significant wave Height(WVHT)
- Dominant wave period (DPD)
- Average wave period (APD)
- Mean wave direction, clockwise from true north (MWD)

### Ex (one row of data):
| Date | Time (UTC) | WVHT (m) | DPD (sec) | APD (sec) | MWD (°T) |
|---|---|---:|---:|---:|---:|
| 2025-01-01 | 00:00 | 1.81 | 12.50 | 8.73 | 278 |



# Data source: 

## NOAA tides and current tracker station 9414290 for 2025

### Link: https://tidesandcurrents.noaa.gov/waterlevels.html?id=9414290&units=standard&bdate=20250101&edate=20251231&timezone=GMT&datum=MLLW&interval=h&action=

### Provides: 
- Day, month, time for every 1 hour
- Tide
- Whether falling/rising and rate not listed, but can be easily calculated using surrounding data

### Ex (one row of data):
| Date | Time (GMT) | Predicted (ft) | Verified (ft) |
|---|---|---:|---:|
| 2025-01-01 | 00:00 | 0.099 | 0.12 |


# Data source: 

## Open Metro historical wind data

### Link: https://open-meteo.com/en/docs/historical-weather-api?utm_source=chatgpt.com&hourly=wind_speed_10m,wind_direction_10m&start_date=2025-01-01&end_date=2025-12-31&latitude=37.7557&longitude=-122.5065&timezone=auto

### Provides:
- Wind speed
- Wind direction
- Literally all the python code needed to collect the data so I dont even need an example data set to parse it I can just use their provided code!



# Missing:
- *** Surf ratings *** (Possibly use conditions and wave size, then have user input their ideal combo and it checks how good it is      comp to that in order to form score out of 10)