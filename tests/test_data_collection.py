import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import data_collection as dc


def make_inputs():
    # 4 hours of 30-min buoy readings, one missing (99) wave height,
    # directions straddling north to check the circular average.
    buoy_raw = pd.DataFrame({
        "#YY": [2025] * 8, "MM": [1] * 8, "DD": [1] * 8,
        "hh": [0, 0, 1, 1, 2, 2, 3, 3], "mm": [0, 30] * 4,
        "WVHT": [1.0, 2.0, 99.0, 1.5, 1.2, 1.4, 1.1, 1.3],
        "DPD": [12.0] * 8, "APD": [8.0] * 8,
        "MWD": [350, 10, 270, 270, 280, 280, 290, 290],
    })
    index = pd.date_range("2025-01-01", periods=4, freq="1h", tz="UTC", name="timestamp")
    wind = pd.DataFrame({"wind_speed_10m": [5.0, 6.0, 7.0, 8.0],
                         "wind_direction_10m": [270.0] * 4}, index=index)
    tide = pd.DataFrame({"tide_ft": [1.0, np.nan, 3.0]}, index=index[:3])
    return dc.clean_buoy(buoy_raw), wind, tide


def test_clean_buoy_hourly_and_missing_values():
    buoy, _, _ = make_inputs()
    assert len(buoy) == 4
    assert buoy["WVHT"].iloc[0] == 1.5
    assert buoy["WVHT"].iloc[1] == 1.5  # the 99 sentinel was dropped, not averaged in
    mwd = buoy["MWD"].iloc[0]
    assert min(mwd, 360 - mwd) < 1e-6  # 350 and 10 average to north, not 180


def test_merge_save_load_round_trip(tmp_path):
    buoy, wind, tide = make_inputs()
    data = dc.merge(wind, buoy, tide)
    assert str(data.index.tz) == dc.LOCAL_TZ
    assert np.isnan(data["tide_ft"].iloc[3])  # missing tide hour stays NaN, no shift

    out = dc.save(data, tmp_path / "data" / "merged.csv")
    assert out.exists()

    loaded = dc.load(out)
    pd.testing.assert_frame_equal(loaded, data, check_freq=False, check_index_type=False)
