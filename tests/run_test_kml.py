import os
import pandas as pd
import numpy as np
import geopandas as gpd
import trackintel as ti

from activity_llm.io import parse_kml, load_trackintel_from_kml_dir
from activity_llm.home_work import find_basic_locations

if __name__ == "__main__":
    kml_path = "data/kml_data"

    staypoints, triplegs = load_trackintel_from_kml_dir(kml_path)

    sp_w_purpose, home_work_result = find_basic_locations(staypoints)

    # filter for the ones that have unknown purpose
    unknown_sp = sp_w_purpose[sp_w_purpose["purpose"].isna()]

    print("Identified home and work locations:")
    print(home_work_result)