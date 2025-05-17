import rtmaps.core as rt
import rtmaps.types
from rtmaps.base_component import BaseComponent  # Base class
import math
from shapely.geometry import LineString, Point
from typing import List

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
        self.add_input("intersectionID_MapData", rtmaps.types.FLOAT64)
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
        self.add_input("Intersection_1_Lane_3_ID", rtmaps.types.FLOAT64)
        self.add_input("Intersection_1_Lane_3_directionalUse", rtmaps.types.FLOAT64)
        self.add_input("Intersection_1_Lane_3_Node_1_delta_lon", rtmaps.types.FLOAT64)
        self.add_input("Intersection_1_Lane_3_Node_1_delta_lat", rtmaps.types.FLOAT64)
        self.add_input("Intersection_1_Lane_3_Node_2_delta_lon", rtmaps.types.FLOAT64)
        self.add_input("Intersection_1_Lane_3_Node_2_delta_lat", rtmaps.types.FLOAT64)
        self.add_input("Intersection_1_Lane_3_Node_3_delta_lon", rtmaps.types.FLOAT64)
        self.add_input("Intersection_1_Lane_3_Node_3_delta_lat", rtmaps.types.FLOAT64)
        self.add_input("Intersection_1_Lane_3_Node_4_delta_lon", rtmaps.types.FLOAT64)
        self.add_input("Intersection_1_Lane_3_Node_4_delta_lat", rtmaps.types.FLOAT64)
        self.add_input("Intersection_1_Lane_4_ID", rtmaps.types.FLOAT64)
        self.add_input("Intersection_1_Lane_4_directionalUse", rtmaps.types.FLOAT64)
        self.add_input("Intersection_1_Lane_4_Node_1_delta_lon", rtmaps.types.FLOAT64)
        self.add_input("Intersection_1_Lane_4_Node_1_delta_lat", rtmaps.types.FLOAT64)
        self.add_input("Intersection_1_Lane_4_Node_2_delta_lon", rtmaps.types.FLOAT64)
        self.add_input("Intersection_1_Lane_4_Node_2_delta_lat", rtmaps.types.FLOAT64)
        self.add_input("Intersection_1_Lane_4_Node_3_delta_lon", rtmaps.types.FLOAT64)
        self.add_input("Intersection_1_Lane_4_Node_3_delta_lat", rtmaps.types.FLOAT64)
        self.add_input("Intersection_1_Lane_4_Node_4_delta_lon", rtmaps.types.FLOAT64)
        self.add_input("Intersection_1_Lane_4_Node_4_delta_lat", rtmaps.types.FLOAT64)
        self.add_input("Intersection_1_Lane_5_ID", rtmaps.types.FLOAT64)
        self.add_input("Intersection_1_Lane_5_directionalUse", rtmaps.types.FLOAT64)
        self.add_input("Intersection_1_Lane_5_Node_1_delta_lon", rtmaps.types.FLOAT64)
        self.add_input("Intersection_1_Lane_5_Node_1_delta_lat", rtmaps.types.FLOAT64)
        self.add_input("Intersection_1_Lane_5_Node_2_delta_lon", rtmaps.types.FLOAT64)
        self.add_input("Intersection_1_Lane_5_Node_2_delta_lat", rtmaps.types.FLOAT64)
        self.add_input("Intersection_1_Lane_5_Node_3_delta_lon", rtmaps.types.FLOAT64)
        self.add_input("Intersection_1_Lane_5_Node_3_delta_lat", rtmaps.types.FLOAT64)
        self.add_input("Intersection_1_Lane_5_Node_4_delta_lon", rtmaps.types.FLOAT64)
        self.add_input("Intersection_1_Lane_5_Node_4_delta_lat", rtmaps.types.FLOAT64)
        self.add_input("Intersection_1_Lane_6_ID", rtmaps.types.FLOAT64)
        self.add_input("Intersection_1_Lane_6_directionalUse", rtmaps.types.FLOAT64)
        self.add_input("Intersection_1_Lane_6_Node_1_delta_lon", rtmaps.types.FLOAT64)
        self.add_input("Intersection_1_Lane_6_Node_1_delta_lat", rtmaps.types.FLOAT64)
        self.add_input("Intersection_1_Lane_6_Node_2_delta_lon", rtmaps.types.FLOAT64)
        self.add_input("Intersection_1_Lane_6_Node_2_delta_lat", rtmaps.types.FLOAT64)
        self.add_input("Intersection_1_Lane_6_Node_3_delta_lon", rtmaps.types.FLOAT64)
        self.add_input("Intersection_1_Lane_6_Node_3_delta_lat", rtmaps.types.FLOAT64)
        self.add_input("Intersection_1_Lane_6_Node_4_delta_lon", rtmaps.types.FLOAT64)
        self.add_input("Intersection_1_Lane_6_Node_4_delta_lat", rtmaps.types.FLOAT64)
        

        # Output: Distance-to-arrival from current GPS position to the end node (meters)
        self.add_output("distance_to_arrival", rtmaps.types.FLOAT64)
        self.add_output("Lane_ID_matched", rtmaps.types.FLOAT64)
        self.add_output("Intersection_ID_matched", rtmaps.types.FLOAT64)

    def Birth(self):
        """
        Called once at the beginning of the component lifecycle.
        """
        self.matchedID = None
        self.matchlane = None
        self.intersections: dict = None
        self.previousPoint: dict = None
        self.isFirst: bool = True
        self.stopbar: bool = False
        self.gps_heading = 0.0
        self.lateral_dist = float('inf')

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
            
        if self.intersections is None:
            self.intersections = {}
            self.store_intersection_data()
            print(self.intersections)
        
        intersection_ID = self.inputs["intersectionID_MapData"].ioelt.data
        if intersection_ID not in self.intersections:
            self.store_intersection_data()

        latitude_gps = self.inputs["latitude_gps"].ioelt.data
        longitude_gps = self.inputs["longitude_gps"].ioelt.data
        gps_point = {"lat": latitude_gps, "lon": longitude_gps}
        best_match = None
        matched_link = None
        min_distance = float('inf')
        DISTANCE_THRESHOLD_POS = 100.0 
        DISTANCE_THRESHOLD_NEV = -50.0
        
        for intersection_id, data in self.intersections.items():
            for lane in data["lanes"]:
                # Skip lanes that are not ingress (directionalUse != 10)
                if lane["directionalUse"] != 10.0:
                    continue

                node_list = lane["nodes"]["node_list"]  # Extract list of (lon, lat)
                if len(node_list) < 2:
                    continue  # Need at least two nodes to form a line

                # Create the road geometry
                line = LineString(node_list)
                lateral_distance = line.distance(Point(longitude_gps, latitude_gps))
                #print(f"land id: {lane["lane_id"]}, {lateral_distance}")

                matched_link = self.map_matcher(gps_point, line)
                if matched_link is None:
                    continue  # Heading mismatch
                
                dta = self.calculate_distance_to_arrival(line, gps_point)
                #print(f"lane id: {lane["lane_id"]}, {dta}")

                if dta > DISTANCE_THRESHOLD_POS:
                    continue
                if dta < DISTANCE_THRESHOLD_NEV:                   
                    continue


                # Update best_match if it's the closest and within valid distance range
                if dta < min_distance or (dta == min_distance and lateral_distance < self.best_lateral_dist):
                    min_distance = dta
                    self.best_lateral_dist = lateral_distance
                    best_match = {
                        "intersection_id": intersection_id,
                        "lane_id": lane["lane_id"],
                        "distance": dta,
                    }

        # Reset if vehicle out of range
        if best_match is None:
            self.matchedID = None
            self.matchedlane = None
            return

        # Start up check
        if self.matchedID is None:
            self.matchedID = best_match["intersection_id"]
            self.matchedlane = best_match["lane_id"]
        
        if self.matchedID != best_match["intersection_id"]:
            print("new intersection")
            self.matchedID = best_match["intersection_id"]
            self.matchedlane = best_match["lane_id"]
            self.outputs["distance_to_arrival"].write(best_match["distance"])
            self.outputs["Intersection_ID_matched"].write(best_match["intersection_id"])
            self.outputs["Lane_ID_matched"].write(best_match["lane_id"])

        elif self.matchedID == best_match["intersection_id"] and self.matchedlane == best_match["lane_id"]:
            self.outputs["distance_to_arrival"].write(best_match["distance"])
            self.outputs["Intersection_ID_matched"].write(best_match["intersection_id"])
            self.outputs["Lane_ID_matched"].write(best_match["lane_id"])

    def Death(self):
        print("Passing through Death()")

    def store_lane_data(self, lane_number: int) -> dict:
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
            "node_list": lane_nodes
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
            segments = self.split_to_segments(road_link)
            gps_heading = self.calculatePointsHeading(self.previousPoint, gps_point)
            if not any(self.headingFilter(segment, gps_heading, threshold=30) for segment in segments):
                # Debug: log heading mismatch
                #print(f"Heading filter dropped point: segment GPS heading {gps_heading:.2f}° not within threshold of link heading.")
                return None
            self.gps_heading = gps_heading

        self.previousPoint = gps_point
        return road_link

    def calculatePointsHeading(self, previousPoint: dict, currentPoint: dict) -> float:
        """
        Computes heading in degrees from previousPoint to currentPoint.
        Points are dictionaries with 'lat' and 'lon' keys.
        """
        lon1, lat1 = math.radians(previousPoint['lon']), math.radians(previousPoint['lat'])
        lon2, lat2 = math.radians(currentPoint['lon']), math.radians(currentPoint['lat'])
        
        #Case handling when the ego vehicle is stopping at the light
        if lon1 == lon2 and lat1 == lat2:
            return self.gps_heading

        d_lon = lon2 - lon1

        x = math.sin(d_lon) * math.cos(lat2)
        y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(d_lon)
        return (math.degrees(math.atan2(x, y)) + 360) % 360

    def headingFilter(self, line: LineString, GPSHeading: float, threshold: float = 45) -> bool:
        """
        Checks if the difference between the road link heading and the GPS heading
        is within a given threshold (degrees). Returns True if within threshold.
        """
        # Switched x0,y0 to line.coords[-1] and x1,y1 to line.coords[0] bc the end node of an ingress lane is the first node on the list - Hung
        x0, y0 = line.coords[-1]
        x1, y1 = line.coords[0]
        # Calculate heading for the road link.
        link_heading = self.calculatePointsHeading({"lat": y0, "lon": x0}, {"lat": y1, "lon": x1})
        # Compute minimal angular difference.
        diff = min(abs(link_heading - GPSHeading), 360 - abs(link_heading - GPSHeading))
        #print(diff)
        return diff <= threshold

    def calculate_distance_to_arrival(self, line: dict, current_gps_point: dict) -> float:
        """
        Computes the distance (in meters) from the current GPS point to the stopbar (last point of the line)
        following the actual path of the road. Returns negative distance if vehicle has passed the stopbar.
        
        Args:
            line: A LineString object representing the road geometry (from last node to stopbar)
            current_gps_point: Dictionary with 'lat' and 'lon' keys representing the current GPS position
            
        Returns:
            float: Distance in meters from current position to the stopbar following the road path.
                  Negative if vehicle has passed the stopbar.
        """
        # Distance the vehicle should be away from node (stopbar)
        STOPBAR_OFFSET = 3.0  # meters
        # Convert the distance to meters using the latitude-based conversion
        meters_per_degree = METERS_PER_DEGREE_LAT
        
        # Create Point object from current GPS position
        gps_pt = Point(current_gps_point['lon'], current_gps_point['lat'])
        
        # Get the last point of the line (stopbar)
        stopbar_pt = self.calculate_threshold_stopbar(line, STOPBAR_OFFSET)   
        
        # Calculate direct distance to stopbar
        direct_distance = gps_pt.distance(stopbar_pt) * meters_per_degree

        #print(f"start_pt: {gps_pt} end_pt: {stopbar_pt}")
        
        # Get the distance along the line to the projected point
        distance_along_line = line.project(gps_pt) * meters_per_degree - STOPBAR_OFFSET
        

        if distance_along_line == -(STOPBAR_OFFSET):
            dta = - abs(direct_distance )
        else:
            dta = distance_along_line 
            
        return dta
    
    def store_intersection_data(self):
        # --------------------------------------------------------
        # This section parses and stores MAP data for intersections.
        #
        # self.intersections is a dictionary where:
        # - The key is the intersection ID (e.g., 1002.0)
        # - The value is a dictionary with:
        #    'refPoint': the reference latitude and longitude of the intersection
        #     (typically in microdegrees, as per MAP encoding)
        #    'lanes': a list of lane objects, where each lane object contains:
        #       - 'lane_id': the lanes unique identifier within the intersection
        #       - 'directionalUse': lane directionality flag (e.g., 10 = ingress)
        #       - 'nodes': a dictionary with:
        #            'node_count': the number of nodes along the lane
        #            'node_list': a list of (lon, lat) tuples in degrees
        # --------------------------------------------------------

        intersection_ID = self.inputs["intersectionID_MapData"].ioelt.data
        latitude_refPoint = self.inputs["latitude_refPoint"].ioelt.data
        longitude_refPoint = self.inputs["longitude_refPoint"].ioelt.data

        intersection_curr = {
            "refPoint": {
                "lat": latitude_refPoint,
                "lon": longitude_refPoint
            },
            "lanes": []
        }

        lane_num = 1
        while True:
            try:
                lane_id_input = f"Intersection_1_Lane_{lane_num}_ID"
                if self.inputs[lane_id_input].ioelt.data == -1.0:
                    break

                LaneID = self.inputs[lane_id_input].ioelt.data
                lane_data = self.store_lane_data(lane_num)  # Should return a dict with 'nodes' 
                directional_key = f"Intersection_1_Lane_{lane_num}_directionalUse"


                intersection_curr["lanes"].append({
                    "lane_id": LaneID,
                    "directionalUse": self.inputs[directional_key].ioelt.data , 
                    "nodes": lane_data
                })

                lane_num += 1

            except KeyError:
                break
            except AttributeError:
                break

        # Store it in your global dictionary
        self.intersections[intersection_ID] = intersection_curr
        print(f"[MapMatcher] Stored MAP for Intersection {intersection_ID}: {self.intersections[intersection_ID]}")

    def calculate_threshold_stopbar(self, line: LineString, threshold_distance: float = 3.0) -> Point:
        """
        Computes the GPS coordinates of the threshold point (specified distance before the stopbar).
        
        Args:
            line: A LineString object representing the road geometry
            threshold_distance: Distance in meters from the stopbar to consider as threshold (default: 3.0)
            
        Returns:
            Point: The GPS coordinates of the threshold point
        """
        # Get the stopbar point (first node)
        stopbar_pt = Point(line.coords[0])
        #print(f"stop bar : {stopbar_pt}")
        
        # Create a point threshold_distance meters back along the line
        # First, project the stopbar point onto the line to get its position
        stopbar_position = line.project(stopbar_pt)

        # Calculate the new position by moving threshold_distance meters back
        meters_per_degree = METERS_PER_DEGREE_LAT
        offset_degrees = threshold_distance / meters_per_degree
        
        # Get the new position along the line
        new_position = stopbar_position + offset_degrees
        
        # Get the point at this new position
        threshold_pt = line.interpolate(new_position)
        
        return threshold_pt
    
    def split_to_segments(self,line: dict) -> List[LineString]:
        """
        Splits a LineString into multiple 2-point LineStrings.

        Args:
            line: A shapely.geometry.LineString object

        Returns:
            List[LineString]: A list of 2-point LineStrings
        """
        line=list(line.coords)
        segments = []
        for i in range(len(line) - 1):
            segment = LineString([line[i], line[i+1]])
            segments.append(segment)
        return segments