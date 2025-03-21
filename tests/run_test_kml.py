import os
import pandas as pd
import numpy as np
import geopandas as gpd
import trackintel as ti

from activity_llm.io import parse_kml, load_trackintel_from_kml_dir
from activity_llm.home_work import find_basic_locations
from activity_llm.surrounding_poi import SurroundingPOI
from activity_llm.query_llm import QueryLLM

if __name__ == "__main__":
    kml_path = "data/kml_data"
    out_path = "outputs/final_labeled_sp.csv"

    staypoints, triplegs = load_trackintel_from_kml_dir(kml_path)

    sp_w_purpose, locations, home_work_result = find_basic_locations(staypoints)

    # filter for the ones that have unknown purpose
    unknown_staypoints = sp_w_purpose[sp_w_purpose["purpose"].isna()]
    # unknown_locations = locations.loc[sp_w_purpose[sp_w_purpose["purpose"].isna()]["location_id"].unique()]

    print("Identified home and work locations:")
    print(home_work_result)

    print("Continuing with the unknown locations:")
    print(unknown_staypoints.head())
    print()

    poi_identifier = SurroundingPOI(radius=100)
    llm_to_query = QueryLLM(poi_identifier, model="gpt-4o")

    # query the LLM for the unknown locations
    results = llm_to_query(unknown_staypoints, output_dir="outputs")

    # merge with original
    all_sp_w_purpose = pd.merge(sp_w_purpose, results, left_index=True, right_on="sp_id", how="left")
    all_sp_w_purpose["purpose"] = all_sp_w_purpose["purpose"].fillna(all_sp_w_purpose["label_llm"])

    all_sp_w_purpose.set_index("sp_id").to_csv(out_path)
    print("Finished and saved to", out_path)
