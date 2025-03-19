import pandas as pd
import trackintel as ti
from geopy.geocoders import Nominatim
from trackintel.analysis.location_identification import location_identifier


def get_address_from_coords(latitude, longitude):
    geolocator = Nominatim(user_agent="geoapi")
    location = geolocator.reverse((latitude, longitude), exactly_one=True)
    return location.address if location else "Address not found"


def find_basic_locations(
    sp, loc_generate_kwargs={"epsilon": 100}, loc_identify_kwargs={"method": "OSNA", "pre_filter": False}
):
    assert sp.index.name == "id", "Staypoints must have an index named 'id'"
    sp, locs = ti.preprocessing.staypoints.generate_locations(sp, **loc_generate_kwargs)

    # identify work and home -> TODO: account for potential moving by doing this grouped by month
    sp_w_purpose = location_identifier(sp, **loc_identify_kwargs)

    # get dictionary of form {location_id: purpose} with work and home locations
    work_home_dict = sp_w_purpose.set_index("location_id")["purpose"].dropna().to_dict()

    # reverse geocoding:
    home_work_result = []
    for location_id, purpose in work_home_dict.items():
        loc = locs.loc[location_id]
        address = get_address_from_coords(loc.center.y, loc.center.x)
        home_work_result.append({"location_id": location_id, "purpose": purpose, "address": address})

    return sp_w_purpose, pd.DataFrame(home_work_result)
