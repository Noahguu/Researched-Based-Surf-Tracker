import pandas as pd

"""
First chunk: Converts NOAA Bouy data from website into useable data w/ standard timestamp
Second chunk: 
Third chunk:
"""
noaa_bouy = pd.read_csv("https://www.ndbc.noaa.gov/view_text_file.php?filename=46237h2025.txt.gz&dir=data/historical/stdmet/",
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

print(noaa_bouy.head())
# print(data.dtypes) # - Checks if data types correct



