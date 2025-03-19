import pandas as pd
import datetime

BASE_PROMPT = "You are a system to find out what places a person visited. We only have the raw location data from this person,\
 meaning longitude, latitude and start and end time. We want to know what exactly the person did. To find out, we have\
 list of the ten closest Points of Interest (POIs) from OSM, with their name and some additional information. When classifying,\
 please consider the following considerations: 1. If there is no POI nearby, the label is probably visiting a friend or something similar.\
 2. If there are many shopping-POIs nearby, it might be a shopping mall\
 3. At typical lunch and dinner times  (lunch: 12pm - 2pm, dinner: 6pm - 9pm), a visit to a restaurant or cafe is more likely.\
 4. Activities during night hours are most likely to be hotels or sleeping at a friends place. Home and work locations were filtered out prior.\
 Here is the data for the stay point of the person: "

PROMPT_FORMAT = '.\nWhat place did the person visit or what activity did they do? Please answer with "Place: <output> Type: <output> Reasoning: <reasoning>" '

WEEKDAYS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


def prompt_pois(closest_pois: pd.DataFrame, skip_unnamed: bool = True, save_to_file: str = None):
    """Design prompt that lists the closest POIs to a location."""

    text_for_activity = "Nearby OSM points of interests are:"

    for i, row in closest_pois.iterrows():
        poi_type, name = row["amenity_type"], row["name"]
        if skip_unnamed and name == "Unnamed":
            continue
        distance = row.get("distance", 0)
        details = row["details"]

        opening = ""
        if row["opening_hours"] != "unknown":
            opening = f", opened {row['opening_hours']}"

        text_for_activity += f"\n{name} (type:{poi_type} {details}{opening}) {round(distance)}m away,".replace(
            "Unknown", ""
        )

    # to save the prompt to a file:
    if save_to_file is not None:
        with open(save_to_file, "w") as output:
            output.write(text_for_activity)

    return text_for_activity[:-1]  # remove comma


def prompt_for_activity(
    lon: float,
    lat: float,
    time_start: datetime.datetime,
    time_end: datetime.datetime,
    existing_label: str = None,
):
    text_for_activity = f'Detected at coordinates {round(lon, 3), round(lat, 3)} on {WEEKDAYS[time_start.weekday()]}, \
        {time_start.strftime("%Y/%m/%d from %I:%M %p")} to {time_end.strftime(" to %I:%M %p")}'
    if existing_label is not None:
        text_for_activity += f'This point was already labelled as "{existing_label}" (label not reliable!).'
    return text_for_activity
