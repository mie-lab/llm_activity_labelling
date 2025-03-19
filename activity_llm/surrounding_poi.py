import pandas as pd
import math
import overpy


class SurroundingPOI:
    def __init__(self, radius: int):
        """
        Args:
            radius (int): Size of the bounding box around point
        """
        self.radius = radius
        self.api = overpy.Overpass()

    def create_bounding_box(self, lat, lon):
        # Calculate half the size in degrees
        delta_lat = self.radius / 111_320  # 1 degree latitude ≈ 111.32 km
        delta_lon = self.radius / (111_320 * abs(math.cos(math.radians(lat))))  # Adjust for longitude

        # Construct bounding box
        min_lat = lat - delta_lat
        max_lat = lat + delta_lat
        min_lon = lon - delta_lon
        max_lon = lon + delta_lon

        return (min_lat, min_lon, max_lat, max_lon)

    def __call__(self, longitude: float, latitude: float):
        bbox = self.create_bounding_box(latitude, longitude)

        # define query for overpass API
        query = f"""
        (
          node["amenity"]["amenity"!~"^(parking|parking_space|bench|bicycle_parking|motorcycle_parking|post_box|toilets|drinking_water|vending_machine)$"]
          {bbox};
          node["healthcare"] {bbox};
          node["shop"]{bbox};
          node["leisure"] {bbox};
          node["tourism"] {bbox};
          node["building"]["building"~"^(religious|transportation)$"] {bbox};
          node["public_transport"]["public_transport"="station"] {bbox};        
          node["theatre"] {bbox};
          node["cinema"] {bbox};
        );
        out;
        """
        result = self.api.query(query)

        result_return = []
        for node in result.nodes:
            details = (
                node.tags.get("shop", " ")
                + node.tags.get("leisure", "")
                + node.tags.get("tourism", "")
                + node.tags.get("cuisine", "")
                + node.tags.get("sport", "")
            ).strip()

            result_return.append(
                {
                    "name": node.tags.get("name", "Unnamed"),
                    "amenity_type": node.tags.get("amenity", "Unknown"),
                    "details": details,
                    "opening_hours": node.tags.get("opening_hours", "unknown"),
                }
            )

        return pd.DataFrame(result_return)
