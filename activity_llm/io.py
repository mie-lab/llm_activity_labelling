import os
import numpy as np
import geopandas as gpd
import pandas as pd
from xml.etree import ElementTree as ET
from shapely.geometry import Point
import trackintel as ti
import shapely
from datetime import datetime

modes = [
    "Driving",
    "Walking",
    "On a tram",
    "On the subway",
    "On a train",
    "Cycling",
    "Running",
]


def format_date(date_str: str):
    # Convert to datetime object
    date_obj = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%fZ")
    # Format it to a nicer format
    formatted_date = date_obj.strftime("%Y/%m/%d at %I:%M %p")
    return formatted_date


def parse_kml(kml_path: str):
    """
    Parse a KML file and extract placemarks with timestamps, coordinates, and labels.

    Parameters:
        kml_path (str): Path to the KML file.

    Returns:
        gpd.GeoDataFrame: A geodataframe with columns [time_start, time_end, geometry, label].
    """
    # Parse the KML file
    tree = ET.parse(kml_path)
    root = tree.getroot()

    # Define the KML namespace
    namespace = {"kml": "http://www.opengis.net/kml/2.2"}

    # Extract placemarks
    data = []
    for placemark in root.findall(".//kml:Placemark", namespace):
        name = placemark.find("kml:name", namespace)
        address = placemark.find("kml:address", namespace).text
        time_start, time_end = None, None

        # Extract time if available
        timespan = placemark.find("kml:TimeSpan", namespace)
        if timespan is not None:
            time_start_elem = timespan.find("kml:begin", namespace)
            time_end_elem = timespan.find("kml:end", namespace)
            time_start = time_start_elem.text if time_start_elem is not None else None
            time_end = time_end_elem.text if time_end_elem is not None else None

        # label
        label = name.text if name is not None else "Unknown"

        # distance if available
        # Extract Distance if available
        distance = pd.NA
        extended_data = placemark.find("kml:ExtendedData", namespace)
        if extended_data is not None:
            distance_elem = extended_data.find(".//kml:Data[@name='Distance']/kml:value", namespace)
            distance = int(distance_elem.text) if distance_elem is not None else pd.NA

        # Extract coordinates
        point = placemark.find(".//kml:Point/kml:coordinates", namespace)
        linestring = placemark.find(".//kml:LineString/kml:coordinates", namespace)
        if point is not None:
            coords = point.text.strip().split(",")
            longitude, latitude = float(coords[0]), float(coords[1])
            geometry = Point(longitude, latitude)

            data.append(
                [
                    format_date(time_start),
                    format_date(time_end),
                    geometry,
                    label,
                    address,
                    distance,
                    "staypoint",
                ]
            )

        elif linestring is not None:
            coords_list = linestring.text.strip().replace("\n", "").split(" ")
            coords = shapely.LineString(
                [
                    (float(coord.split(",")[0]), float(coord.strip().split(",")[1]))
                    for coord in coords_list
                    if len(coord) > 1
                ]
            )
            data.append(
                [
                    format_date(time_start),
                    format_date(time_end),
                    coords,
                    label,
                    address,
                    distance,
                    "tripleg",
                ]
            )
        else:
            print(name.text, "point is none")

    # Create and return GeoDataFrame
    gdf = gpd.GeoDataFrame(
        data,
        columns=[
            "time_start",
            "time_end",
            "geometry",
            "label",
            "address",
            "distance",
            "type",
        ],
        crs="EPSG:4326",
    )
    return gdf


def load_trackintel_from_kml_dir(kml_path: str):
    all_tracks = []
    for file in sorted(os.listdir(kml_path)):
        kml_file_path = os.path.join(kml_path, file)
        gdf = parse_kml(kml_file_path)
        all_tracks.append(gdf)

    # combine all tracks
    all_tracks = pd.concat(all_tracks)
    all_tracks["id"] = np.arange(len(all_tracks))

    # convert to geodataframe
    all_tracks = gpd.GeoDataFrame(all_tracks, geometry="geometry")

    # change attributes to fit trackintel format
    trackintel_tracks = all_tracks.rename({"time_start": "started_at", "time_end": "finished_at"}, axis=1)
    trackintel_tracks["user_id"] = 1

    # import staypoints into trackintel
    staypoints = trackintel_tracks[trackintel_tracks["type"] == "staypoint"]
    sp = ti.io.from_geopandas.read_staypoints_gpd(
        staypoints.drop(["distance", "type"], axis=1), geom_col="geometry", tz="utc"
    )

    # import triplegs into trackintel
    triplegs = trackintel_tracks[trackintel_tracks["type"] != "staypoint"]
    valid_triplegs = triplegs[triplegs.geometry.is_valid]
    tpls = ti.io.from_geopandas.read_triplegs_gpd(
        valid_triplegs.drop(["distance", "type"], axis=1), geom_col="geometry", tz="utc"
    )

    return sp.set_index("id"), tpls.set_index("id")
