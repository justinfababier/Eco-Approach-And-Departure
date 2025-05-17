import rtmaps.core as rt
import rtmaps.types
from rtmaps.base_component import BaseComponent  # base class
import json  # For handling Gamma input as JSON
import numpy as np

class rtmaps_python(BaseComponent):
    """
    RTMaps component that:
    1)  Receives x inputs:
        -
        -
        -
        -
    2)  Does something
    3)  - Returns the identified scenario
        - Passes the inputs through the output lines
    """

    def __init__(self):
        BaseComponent.__init__(self)

    def Dynamic(self):
        """
        Declare inputs, outputs, and properties
        """
        self.add_input("d_0", rtmaps.types.FLOAT64)  # Route distance to stop-bar
        self.add_input("v_c_in", rtmaps.types.FLOAT64)  # Instantaneous speed at time instant t_0 (in km/h)
        self.add_input("t_0", rtmaps.types.INTEGER64)  # Current absolute time (seconds)
        self.add_input("g_e_curr", rtmaps.types.FLOAT64)  # Estimated current green window end time
        self.add_input("g_s_next", rtmaps.types.FLOAT64)   # Estimated next green window start time
        self.add_input("g_e_next", rtmaps.types.FLOAT64)   # Estimated next green window end time
        self.add_output("scenario", rtmaps.types.TEXT_ASCII)  # Scenario result (String)
        self.add_output("scenario_n", rtmaps.types.INTEGER64)  # Scenario result (String)
        self.add_output("d_0_out", rtmaps.types.FLOAT64)    # Route distance to stop-bar
        #self.add_output("v_c_out", rtmaps.types.FLOAT64)    # Instantaneous speed at time instant t_0
        #self.add_output("t_0_out", rtmaps.types.FLOAT64)    # Current absolute time (seconds)
        #self.add_output("gamma_out", rtmaps.types.ANY)      # Green intervals (JSON)

    def Birth(self):
        """
        Called once at the beginning.
        """
        print("Decision Maker: Scenario Identifier initialized.")

    def Core(self):
        """
        Called on every cycle (when new data is available).
        """
        # Read inputs
        d_0_in = self.inputs["d_0"].ioelt.data 
        g_e_curr = self.inputs["g_e_curr"].ioelt.data 
        g_s_next = self.inputs["g_s_next"].ioelt.data
        g_e_next = self.inputs["g_e_next"].ioelt.data
        v_c_in = self.inputs["v_c_in"].ioelt.data
        t_0_in = round(float(self.inputs["t_0"].ioelt.data * 1e-6),2)
        #gamma_in = self.inputs["gamma"].ioelt.data if self.inputs["gamma"].ioelt else None


        # Validate critical inputs
        if d_0_in is None or v_c_in is None or t_0_in is None or g_e_curr is None or g_s_next is None or g_e_next is None:
            print("ERROR: Missing inputs!")
            self.outputs["scenario"].write("Missing Inputs")
            return

        # Robust handling of gamma input:
        # If gamma_in is a string, try to parse it as JSON. If it's already a list (or tuple), use it directly.
        
        if g_e_curr == -1:
            # Case 1: No current green phase
            gamma_intervals = ((g_s_next, g_e_next),)
        else:
            # Case 2: Current green phase exists
            gamma_intervals = ((t_0_in, g_e_curr), (g_s_next, g_e_next))
        


        # Additional parameters in case identified scenario is S3 or S4
        # Assure that these parameters are in line with the same parameters found in DMTG
        #t_e = t_0_in + d_0_in / v_c_in  # Earliest time to arrival
        a_max = 1.0          # maximum acceleration in m/s²
        d_max = 1.0         # maximum deceleration in m/s²
        jerk_max = 1.0       # maximum jerk in m/s³
        v_limit = 56.33   # speed limit in km/h (35mph) 
        v_coast = 12.87 # km/h as defined, equivalent to 8 MPH

        # Convert velocity from km/h to m/s for calculations:
        v_c_ms = v_c_in  * (5.0 / 18.0) # km/h to m/s          
        v_limit_ms = v_limit * (5.0 / 18.0)   # velocity limit in m/s
        v_coast_ms = v_coast * (5.0 / 18.0)
        
        term1p = (2 * a_max) / (v_limit_ms - v_c_ms)
        term2p = np.sqrt((2 * jerk_max) / (v_limit_ms - v_c_ms))
        term1q = (2 * a_max) / (v_c_ms - v_coast_ms)
        term2q = np.sqrt((2 * jerk_max) / (v_c_ms - v_coast_ms))

        p = min(term1p, term2p)
        q = min(term1q, term2q)

        t_cr = d_0_in / v_c_ms
        t_e = ((d_0_in - v_c_ms * np.pi / (2 * p)) / v_limit_ms) + (np.pi / (2 * p))
        t_l = ((d_0_in - v_c_ms * np.pi / (2 * q)) / v_coast_ms) + (np.pi / (2 * q))

        # Calculate time thresholds (ensure v_c_in > 0 to avoid division by zero)
        if v_c_ms < 0:
            print("ERROR: Speed must be greater than zero.")
            self.outputs["scenario"].write("Invalid Speed")
            self.outputs["d_0_out"].write(d_0_in)
            return
        elif v_c_ms > v_limit_ms:
            print("ERRPR: Speed is over speed limit!!!")
            self.outputs["scenario"].write("Invalid Speed")
            self.outputs["d_0_out"].write(d_0_in)
            return
        """
        if v_c_in == 0:
            t_cr = np.sqrt(2 * d_0_in / a_max)  
        else:
            t_cr = d_0_in / v_c_in  # Cruise time to arrival
        """
        # Identify the scenario based on gamma intervals and time thresholds
        #print(f"DEBUG: Calculated t_e={t_e}, t_l={t_l}, t_0={t_0_in}, t_cr={t_cr}")
        scenario_result, scenario_n= self.identify_scenario( gamma_intervals, t_cr, t_e, t_l)

        # Write the scenario result to the output
        self.outputs["scenario"].write(scenario_result)

        self.outputs["scenario_n"].write(scenario_n)
        # Write the inputs lines as outputs
        self.outputs["d_0_out"].write(d_0_in)
        #self.outputs["v_c_out"].write(v_c_in)
        #self.outputs["t_0_out"].write(t_0_in)
        #self.outputs["gamma_out"].write(gamma_intervals)
        
    def Death(self):
        """
        Called once at the end (cleanup).
        """
        print("Decision Maker: Scenario Identifier terminated.")

    def identify_scenario(self, gamma_intervals, t_cr, t_e, t_l):
        """
        Identify the scenario based on the current time, Gamma intervals, and thresholds.

        Args:
            t_0_in (float): Current time.
            gamma_intervals (list): List of green intervals [[start1, end1], [start2, end2], ...].
            t_e (float): Earliest relevant time.
            t_l (float): Latest relevant time.
            t_cr (float): Critical time (e.g., estimated time to reach the stop-bar).

        Returns:
            str: Identified scenario ("Scenario 1", "Scenario 2", etc.).
        """
    
        # Scenario 1: Check if the cruise arrival time t_cr falls within any green windows. If you maintain cruise speed, you will arrive while the light is green.
        for interval in gamma_intervals:
            if len(interval) == 2:
                start, end = interval
                #print(f"DEBUG: Calculated start={start}, t_l={t_l}, end={end}, t_cr={t_cr}")
                if start <= t_cr < end:
                    print("DEBUG: Scenario 1 matched.")
                    return "Scenario 1",1

        # Scenario 2: Check if the interval [t_e, t_cr] overlaps with any green windows. You could arrive during a green light if you accelerate slightly.

        for interval in gamma_intervals:
            if len(interval) == 2:
                start, end = interval
                # Determine the intersection between [t_e, t_cr] and [start, end]
                if max(t_e, start) < min(t_cr, end):
                    print("DEBUG: Scenario 2 matched.")
                    return "Scenario 2",2

        # Scenario 3: Check if there is no gamma overlap in the interval [t_cr, t_l]. Stopping is inevitable.

        overlap_found = False
        for interval in gamma_intervals:
            if len(interval) == 2:
                start, end = interval
                if max(t_cr, start) < min(t_l, end):
                    overlap_found = True
                    break
        if not overlap_found:
            print("DEBUG: Scenario 3 matched.")
            return "Scenario 3",3

        # Default: Scenario 4 if none of the above conditions are met. Possibly useful for Eco-Approach strategies (e.g., creeping forward or brief idling).

        print("DEBUG: Scenario 4 matched.")
        return "Scenario 4",4
