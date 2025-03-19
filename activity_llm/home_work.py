import pandas as pd
import trackintel as ti
import geopandas as gpd
from geopy.geocoders import Nominatim
from trackintel.analysis.location_identification import location_identifier


def get_address_from_coords(latitude, longitude):
    geolocator = Nominatim(user_agent="geoapi")
    location = geolocator.reverse((latitude, longitude), exactly_one=True)
    return location.address if location else "Address not found"


def location_identifier_with_grouping(
    all_sp: gpd.GeoDataFrame,
    loc_identify_kwargs: dict,
    min_visits_whole_time: int = 5,
    min_visit_rate_for_month: float = 0.2,
    min_samples_for_month: int = 5,
):
    """
    Identifies home and work locations grouped by month.

    Parameters:
    - sp (GeoDataFrame): Input GeoDataFrame with 'started_at', 'finished_at', and point geometry.
    - loc_identify_kwargs (dict): Arguments for the `location_identifier` function.
    - min_visits (int): Minimum number of occurrences in a month to identify a location as home/work.

    Returns:
    - GeoDataFrame with a 'purpose' column containing 'home', 'work', or NaN.
    """

    # prefilter for the ones that have min_visits visits overall
    visit_per_location = all_sp.groupby("location_id")["location_id"].count()
    sufficiently_visited_locs = list(visit_per_location[visit_per_location > min_visits_whole_time].index)
    sp = all_sp[all_sp["location_id"].isin(sufficiently_visited_locs)]

    # group by month
    sp["month"] = sp["started_at"].dt.to_period("M")

    # Placeholder for combined results
    results = []

    for month, group in sp.groupby("month"):
        if len(group) < min_samples_for_month:
            # print(f"Skip month {month} bc not enough data")
            group["purpose"] = None
        else:
            group = location_identifier(group, **loc_identify_kwargs)

            # Ensure only frequently visited locations are marked
            counts = group["purpose"].value_counts()
            for purpose in ["home", "work"]:
                if counts.get(purpose, 0) < min_visit_rate_for_month * len(group):
                    # print(f"Removed {purpose} because not important enough in this month")
                    group.loc[group["purpose"] == purpose, "purpose"] = None

        results.append(group)

    results = pd.concat(results).drop("month", axis=1)
    work_home_dict = results.set_index("location_id")["purpose"].dropna().to_dict()
    all_sp["purpose"] = all_sp["location_id"].map(work_home_dict)

    # Combine all results
    return all_sp


def find_basic_locations(
    sp: gpd.GeoDataFrame,
    grouped_by_month: bool = True,
    loc_generate_kwargs: dict = {"epsilon": 100},
    loc_identify_kwargs: dict = {"method": "OSNA", "pre_filter": False},
):
    assert sp.index.name == "id", "Staypoints must have an index named 'id'"
    sp, locs = ti.preprocessing.staypoints.generate_locations(sp, **loc_generate_kwargs)

    # identify work and home
    if grouped_by_month:
        sp_w_purpose = location_identifier_with_grouping(sp, loc_identify_kwargs)
    else:
        sp_w_purpose = location_identifier(sp, **loc_identify_kwargs)

    # get dictionary of form {location_id: purpose} with work and home locations
    work_home_dict = sp_w_purpose.set_index("location_id")["purpose"].dropna().to_dict()

    # reverse geocoding:
    home_work_result = []
    for location_id, purpose in work_home_dict.items():
        loc = locs.loc[location_id]
        address = get_address_from_coords(loc.center.y, loc.center.x)
        home_work_result.append({"location_id": location_id, "purpose": purpose, "address": address})

    return sp_w_purpose, locs, pd.DataFrame(home_work_result)
