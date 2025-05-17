import rtmaps.core as rt
import rtmaps.types
from rtmaps.base_component import BaseComponent  # base class
from scapy.all import rdpcap
import rtmaps.types

class rtmaps_python(BaseComponent):
    
    def __init__(self):
        BaseComponent.__init__(self)  # call base class constructor

    def Dynamic(self):
        # Inputs: ...
        self.add_input("Intersection_1_Lane_1_Node_1_delta_x", rtmaps.types.ANY)
        self.add_input("Intersection_1_Lane_1_Node_1_delta_y", rtmaps.types.ANY)
        self.add_input("Intersection_1_Lane_1_Node_2_delta_x", rtmaps.types.ANY)
        self.add_input("Intersection_1_Lane_1_Node_2_delta_y", rtmaps.types.ANY)
        self.add_input("Intersection_1_Lane_2_Node_1_delta_x", rtmaps.types.ANY)
        self.add_input("Intersection_1_Lane_2_Node_1_delta_y", rtmaps.types.ANY)
        self.add_input("Intersection_1_Lane_2_Node_2_delta_x", rtmaps.types.ANY)
        self.add_input("Intersection_1_Lane_2_Node_2_delta_y", rtmaps.types.ANY)
        self.add_input("Intersection_1_Lane_3_Node_1_delta_x", rtmaps.types.ANY)
        self.add_input("Intersection_1_Lane_3_Node_1_delta_y", rtmaps.types.ANY)
        self.add_input("Intersection_1_Lane_3_Node_2_delta_x", rtmaps.types.ANY)
        self.add_input("Intersection_1_Lane_3_Node_2_delta_y", rtmaps.types.ANY)

        # Output: An array of constructed Shapely Linestrings
        self.add_output("road_links", rtmaps.types.ANY)
        
    def Birth(self):
        print("Passing through Birth()")

    def Core(self):
        print("Passing through Core()")

    def Death(self):
        print("Passing through Death()")
