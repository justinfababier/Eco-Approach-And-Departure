import rtmaps.core as rt
import rtmaps.types
from rtmaps.base_component import BaseComponent  # Base class
import math
from shapely.geometry import LineString, Point

# Constants for conversion
METERS_PER_DEGREE_LAT = 111320.0

class rtmaps_python(BaseComponent):
    """
    RTMaps component that:
    1) Receives inputs:
       - latitude_gps: FLOAT64 representing the latitude of the GPS point (latitude)
       - longitude_gps: FLOAT64 representing the longitude of the GPS point (longitude)
       - longitude_refPoint: FLOAT64 representing the reference point (longitude, in microdegrees)
       - latitude_refPoint: FLOAT64 representing the reference point (latitude, in microdegrees)
       - Intersection_1_Lane_X_directionalUse: FLOAT64 for directional use (not used in this example)
       - Intersection_1_Lane_X_Node_1_delta_x: FLOAT64 representing the x offset of Lane X's start node (meters)
       - Intersection_1_Lane_X_Node_1_delta_y: FLOAT64 representing the y offset of Lane X's start node (meters)
       - Intersection_1_Lane_X_Node_2_delta_x: FLOAT64 representing the x offset of Lane X's end node (meters)
       - Intersection_1_Lane_X_Node_2_delta_y: FLOAT64 representing the y offset of Lane X's end node (meters)
    2) Converts offsets to GPS coordinates (longitude, latitude) using an approximate conversion.
    3) Performs heading-based map matching.
    4) Outputs the 'distance to arrival' (meters) from the current GPS point to the end of the matched link.
    """

    def __init__(self):
        BaseComponent.__init__(self)

    def Dynamic(self):
        """
        Declare inputs, outputs, and properties for RTMaps.
        """
        # Inputs: GPS coordinates and reference point + node offsets
        self.add_input("longitude_gps", rtmaps.types.FLOAT64)
        self.add_input("latitude_gps", rtmaps.types.FLOAT64)
        self.add_input("longitude_refPoint", rtmaps.types.FLOAT64)
        self.add_input("latitude_refPoint", rtmaps.types.FLOAT64)
        self.add_input("Intersection_1_Lane_1_ID", rtmaps.types.FLOAT64)
        self.add_input("Intersection_1_Lane_1_directionalUse", rtmaps.types.FLOAT64)
        self.add_input("Intersection_1_Lane_1_Node_1_delta_lon", rtmaps.types.FLOAT64)
        self.add_input("Intersection_1_Lane_1_Node_1_delta_lat", rtmaps.types.FLOAT64)
        self.add_input("Intersection_1_Lane_1_Node_2_delta_lon", rtmaps.types.FLOAT64)
        self.add_input("Intersection_1_Lane_1_Node_2_delta_lat", rtmaps.types.FLOAT64)
        self.add_input("Intersection_1_Lane_1_Node_3_delta_lon", rtmaps.types.FLOAT64)
        self.add_input("Intersection_1_Lane_1_Node_3_delta_lat", rtmaps.types.FLOAT64)
        self.add_input("Intersection_1_Lane_1_Node_4_delta_lon", rtmaps.types.FLOAT64)
        self.add_input("Intersection_1_Lane_1_Node_4_delta_lat", rtmaps.types.FLOAT64)
        self.add_input("Intersection_1_Lane_2_ID", rtmaps.types.FLOAT64)
        self.add_input("Intersection_1_Lane_2_directionalUse", rtmaps.types.FLOAT64)
        self.add_input("Intersection_1_Lane_2_Node_1_delta_lon", rtmaps.types.FLOAT64)
        self.add_input("Intersection_1_Lane_2_Node_1_delta_lat", rtmaps.types.FLOAT64)
        self.add_input("Intersection_1_Lane_2_Node_2_delta_lon", rtmaps.types.FLOAT64)
        self.add_input("Intersection_1_Lane_2_Node_2_delta_lat", rtmaps.types.FLOAT64)
        self.add_input("Intersection_1_Lane_2_Node_3_delta_lon", rtmaps.types.FLOAT64)
        self.add_input("Intersection_1_Lane_2_Node_3_delta_lat", rtmaps.types.FLOAT64)
        self.add_input("Intersection_1_Lane_2_Node_4_delta_lon", rtmaps.types.FLOAT64)
        self.add_input("Intersection_1_Lane_2_Node_4_delta_lat", rtmaps.types.FLOAT64)
        

        # Output: Distance-to-arrival from current GPS position to the end node (meters)
        self.add_output("distance_to_arrival", rtmaps.types.FLOAT64)
        self.add_output("Lane_ID_matched", rtmaps.types.INTEGER64)

    def Birth(self):
        """
        Called once at the beginning of the component lifecycle.
        """
        self.previousPoint: dict = None
        self.isFirst: bool = True

    def Core(self):
        """
        Main processing function called for every new input data sample.
        Processes available lanes (Lane 1 and Lane 3) and selects the first lane that passes
        the heading-based map matching, only if the lane's directional use is 10.
        """
        # Verify essential GPS and reference inputs are available.
        required_inputs = ["latitude_gps", "longitude_gps", 
                        "latitude_refPoint", "longitude_refPoint"]
        for key in required_inputs:
            if self.inputs[key].ioelt is None:
                print(f"Missing attribute: {key}")
                return
        
        # Read GPS and reference point data.
        latitude_gps = self.inputs["latitude_gps"].ioelt.data
        longitude_gps = self.inputs["longitude_gps"].ioelt.data
        latitude_refPoint = self.inputs["latitude_refPoint"].ioelt.data
        longitude_refPoint = self.inputs["longitude_refPoint"].ioelt.data
        gps_point = {"lat": latitude_gps, "lon": longitude_gps}

        valid_match = None  # To store a valid lane match
        for lane_num in [1, 2]:
            # Check the lane's directional use is exactly 10.
            # Refer to Page 153 of SAE J2735 MAR 2016.
            # This indicates ingress lane travel i.e., rear to front.
            directional_key = f"Intersection_1_Lane_{lane_num}_directionalUse"
            if (self.inputs[directional_key].ioelt is None or 
                    self.inputs[directional_key].ioelt.data != 10):
                print(f"Skipping lane {lane_num} due to not a ingress lane")
                continue

            # Define required keys for the lane.
            lane_keys = [
                f"Intersection_1_Lane_{lane_num}_Node_1_delta_lon",
                f"Intersection_1_Lane_{lane_num}_Node_1_delta_lat",
                f"Intersection_1_Lane_{lane_num}_Node_2_delta_lon",
                f"Intersection_1_Lane_{lane_num}_Node_2_delta_lat",
                f"Intersection_1_Lane_{lane_num}_Node_3_delta_lon",
                f"Intersection_1_Lane_{lane_num}_Node_3_delta_lat",
                f"Intersection_1_Lane_{lane_num}_Node_4_delta_lon",
                f"Intersection_1_Lane_{lane_num}_Node_4_delta_lat",
            ]
            #This might not be needed because 4 nodes is the upper limit and lower number of nodes should be fine
            #if any(self.inputs[k].ioelt is None for k in lane_keys):
            #    continue  # Skip this lane if any input is missing

            # Convert the lane's delta inputs to GPS coordinates.
            lane_data = self.get_lane_gps(lane_num, longitude_refPoint, latitude_refPoint)
            # Construct the road link as a Shapely LineString.
            # road_link = {"geometry": LineString([lane_data["start"], lane_data["end"]])} - Hung
            road_link = {"geometry": LineString(lane_data["nodes"])}
            # Attempt heading-based map matching.
            matched_link = self.map_matcher(gps_point, road_link)
            if matched_link is not None:
                valid_match = (lane_num, lane_data, matched_link)
                break  # Select the first valid match

        if valid_match is not None:
            lane_num, lane_data, matched_link = valid_match
            # Compute distance-to-arrival.
            dta_value = self.calculate_distance_to_arrival(matched_link, gps_point)
            closest_node_lon = lane_data["nodes"][3][0]
            delta_lon_deg = gps_point["lon"] - closest_node_lon
            lat = gps_point["lat"]
            meters = delta_lon_deg * self.get_lon_conversion_factor(lat)

            proximity_threshold = 1.0
            if meters <= proximity_threshold:
                self.outputs["distance_to_arrival"].write(float(dta_value))
                self.outputs["Lane_ID_matched"].write(lane_num)
                print(f"[MapMatcher] Matched lane {lane_num} within {meters:.2f} m → DTA: {dta_value:.2f}")
            else:
                print(f"[MapMatcher] Lane match ignored. Vehicle too far ({meters:.2f} m > {proximity_threshold} m).")
                #self.outputs["distance_to_arrival"].write(float(dta_value))
            

            # For testing purposes (comment-out/delete later)
            #print("Matched Link: " + str(lane_num))
            #print("Distance to Arrival: " + str(dta_value) + "m")


        else:
            print("No valid lane matched; writing NaN to outputs.")
           
    def Death(self):
        print("Passing through Death()")

    def get_lane_gps(self, lane_number: int, longitude_refPoint: float, latitude_refPoint: float) -> dict:
        """
        Helper to convert a lane's delta values into GPS coordinates.
        Returns a dictionary with:
            - Nodes with their GPS coordinates.
            - The number of nodes in the lane.
        """
        lane_nodes = []# Dictionary to store node GPS coordinates
        node_count = 1   # Start checking from Node_1

        while True:
            # Try to get the delta x and delta y for the current node
            try:
                dx = self.inputs[f"Intersection_1_Lane_{lane_number}_Node_{node_count}_delta_lon"].ioelt.data
                dy = self.inputs[f"Intersection_1_Lane_{lane_number}_Node_{node_count}_delta_lat"].ioelt.data

                # Ensure dx and dy are not None before processing
                if dx is None or dy is None:
                    break  # Stop if either delta is None
            
                # Convert deltas to GPS coordinates (longitude, latitude)
                #lon, lat = self.convert_deltas_to_gps(dx, dy, longitude_refPoint, latitude_refPoint)

                lon = dx*1e-7
                lat = dy*1e-7 

                # Append the coordinates to the list (no node name)
                lane_nodes.append((lon, lat))

                node_count += 1  # Move to the next node

            except KeyError:
                # If KeyError occurs (no more nodes), stop the loop
                break
            except AttributeError:
                # If data is missing for a node (e.g., ioelt.data is None), stop the loop
                break

        # Return the number of nodes along with the node coordinates
        return {
            "node_count": len(lane_nodes),
            "nodes": lane_nodes
        }

    def convert_deltas_to_gps(self, delta_lon: float, delta_lat: float,
                              longitude_refPoint: float, latitude_refPoint: float) -> tuple:
        """
        Converts offsets in meters to approximate (longitude, latitude) coordinates.
        The reference point is provided in microdegrees and is converted to degrees.
        
        Parameters:
            delta_x: Offset in meters (affecting latitude)
            delta_y: Offset in meters (affecting longitude)
            longitude_refPoint: Reference longitude in microdegrees
            latitude_refPoint: Reference latitude in microdegrees
        
        Returns:
            A tuple (longitude, latitude) in degrees.
        """
        # Convert reference point from microdegrees to degrees.
        ref_lat = latitude_refPoint * 1e-7
        ref_lon = longitude_refPoint * 1e-7

        # Convert meter offsets to degree offsets.
        lat_offset = delta_lat / METERS_PER_DEGREE_LAT
        lon_conversion_factor = self.get_lon_conversion_factor(ref_lat)
        lon_offset = delta_lon / lon_conversion_factor

        # Return GPS coordinates in (lon, lat) order.
        return ref_lon + lon_offset, ref_lat + lat_offset

    def get_lon_conversion_factor(self, lat: float) -> float:
        """
        Computes the conversion factor for longitude given a latitude.
        """
        return METERS_PER_DEGREE_LAT * math.cos(math.radians(lat))

    def map_matcher(self, gps_point: dict, road_link: dict) -> dict:
        """
        Heading-based map matching:
        - Skips the heading filter for the first GPS point.
        - For subsequent points, it checks whether the heading aligns with the road link.
        """
        if self.isFirst:
            self.isFirst = False  # Skip heading filter on the first point
        else:
            gps_heading = self.calculatePointsHeading(self.previousPoint, gps_point)
            if not self.headingFilter(road_link, gps_heading, threshold=45):
                # Debug: log heading mismatch
                print(f"Heading filter dropped point: GPS heading {gps_heading:.2f}° not within threshold of link heading.")
                return None

        self.previousPoint = gps_point
        return road_link

    def calculatePointsHeading(self, previousPoint: dict, currentPoint: dict) -> float:
        """
        Computes heading in degrees from previousPoint to currentPoint.
        Points are dictionaries with 'lat' and 'lon' keys.
        """
        lon1, lat1 = math.radians(previousPoint['lon']), math.radians(previousPoint['lat'])
        lon2, lat2 = math.radians(currentPoint['lon']), math.radians(currentPoint['lat'])
        d_lon = lon2 - lon1

        x = math.sin(d_lon) * math.cos(lat2)
        y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(d_lon)
        return (math.degrees(math.atan2(x, y)) + 360) % 360

    def headingFilter(self, road_link: dict, GPSHeading: float, threshold: float = 45) -> bool:
        """
        Checks if the difference between the road link heading and the GPS heading
        is within a given threshold (degrees). Returns True if within threshold.
        """
        line = road_link["geometry"]
        # Switched x0,y0 to line.coords[-1] and x1,y1 to line.coords[0] bc the end node of an ingress lane is the first node on the list - Hung
        x0, y0 = line.coords[-1]
        x1, y1 = line.coords[0]
        # Calculate heading for the road link.
        link_heading = self.calculatePointsHeading({"lat": y0, "lon": x0}, {"lat": y1, "lon": x1})
        # Compute minimal angular difference.
        diff = min(abs(link_heading - GPSHeading), 360 - abs(link_heading - GPSHeading))
        return diff <= threshold

    def calculate_distance_to_arrival(self, matched_link: dict, current_gps_point: dict) -> float:
        """
        Computes the distance (in meters) from the current GPS point to the end of the matched road link.
        """
        if matched_link is None:
            return None
        
        # Distance the vehicle should be away from node
        distance_to_be_away_from_stopbar = 3.0    # meters

        line = matched_link["geometry"]
        # Lane stop point is the first node therefore line.coords[0] - Hung
        link_end_pt = Point(line.coords[0])
        gps_pt = Point(current_gps_point['lon'], current_gps_point['lat'])
        # Convert distance from degrees to meters.
        return link_end_pt.distance(gps_pt) * METERS_PER_DEGREE_LAT + distance_to_be_away_from_stopbar
