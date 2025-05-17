import rtmaps.core as rt
import rtmaps.types
from rtmaps.base_component import BaseComponent  # base class
import json  # For JSON serialization of intervals
from datetime import datetime, timezone


class rtmaps_python(BaseComponent):
    """
    RTMaps component that:
    1) Receives 3 inputs:
        - t0: the current time instant
        - current_state: 0 -> 9, refer to line 89
        - countdown: 500 ticks for each phases
    2) Estimates the available green window(s) for the vehicle as:
         If Green at t0:  Γ = [t0, g_e_curr) ∪ [g_s_next, g_e_next)
         If Yellow or Red at t0:  Γ = [g_s_next, g_e_next)
    3) Returns the estimated intervals as JSON.
    """

    def __init__(self):
        BaseComponent.__init__(self)
        # Cache to hold the schedule computed for the current SPAT message.
        self.last_spat_t0 = None
        self.cached_schedule = None  # tuple (g_s_next, g_e_next, g_e_curr)
        self.g_e_curr = None
        self.g_s_next = None 
        self.g_e_next = None

    def Dynamic(self):
        """
        Declare inputs, outputs, and properties.
        """
        self.add_input("t0", rtmaps.types.INTEGER64)
        self.add_input("current_state", rtmaps.types.TEXT_ASCII)
        self.add_input("countdown", rtmaps.types.FLOAT64)
        self.add_input("Intersection_ID_matched", rtmaps.types.FLOAT64)
        self.add_input("IntersectionID_SPaT", rtmaps.types.FLOAT64)

        # Output: Using 'Any' to allow Python objects
        #self.add_output("gamma", rtmaps.types.ANY)          # Available green windows
        #self.add_output("t0_out", rtmaps.types.FLOAT64)     # Current absolute time (seconds)
        self.add_output("g_e_curr", rtmaps.types.FLOAT64)
        self.add_output("g_s_next", rtmaps.types.FLOAT64)
        self.add_output("g_e_next", rtmaps.types.FLOAT64)
        self.add_output("state", rtmaps.types.FLOAT64)

    def Birth(self):
        """
        Called once at the beginning.
        """
        print("Green Window Estimator subsystem initialized.")
        
    def Core(self):
        """
        Called on every cycle (when new data is available).
        """
        # Read the latest data from inputs
        if (self.inputs["Intersection_ID_matched"].ioelt is None or 
            self.inputs["IntersectionID_SPaT"].ioelt is None):
            return
        
         # Read matched intersection from MapMatcher
        intersection_matched = self.inputs["Intersection_ID_matched"].ioelt.data
        # Read SPaT messages intersection ID
        intersection_spat = self.inputs["IntersectionID_SPaT"].ioelt.data

        # If the intersection IDs don't match, skip processing
        if intersection_matched != intersection_spat:
            print(f"Skipped: SPaT ID {intersection_spat} / Matched ID {intersection_matched}")
            return


        t0_in = round(float(self.inputs["t0"].ioelt.data * 1e-6),2)
        current_state_in=self.state_name_to_number(self.inputs["current_state"].ioelt.data)
        count_down_in = int(self.inputs["countdown"].ioelt.data)
               
        if not hasattr(self, "last_cd_tick"):
            self.last_cd_tick = None
            self.last_tick_time = t0_in
            self.tick_intervals = []

        if count_down_in != self.last_cd_tick:
            if self.last_tick_time is not None:
                actual_interval = t0_in - self.last_tick_time
                self.tick_intervals.append(actual_interval)
                if len(self.tick_intervals) > 20:  # keep last 20 intervals
                    self.tick_intervals.pop(0)

            self.last_cd_tick = count_down_in
            self.last_tick_time = t0_in

            # Compute dynamic tick duration (averaged)
            avg_tick_duration = sum(self.tick_intervals) / len(self.tick_intervals) if self.tick_intervals else 0.1
            # Low-pass filter
            if avg_tick_duration < 0.08:
                avg_tick_duration = 0.1

            self.g_s_next, self.g_e_next, self.g_e_curr = self.estimate_green_window_from_countdown(
                t0_in, current_state_in, count_down_in, next_green_duration=500 * avg_tick_duration
            )
            #print(f"g_e_curr: {self.g_e_curr}, g_s_next: {self.g_s_next}, g_e_next: {self.g_e_next}, phase: {current_state_in}, countdown: {count_down_in}, avg_tick: {round(avg_tick_duration, 3)}s")

        



        # Safety check: ensure we have valid data
        if (t0_in is None or
            current_state_in is None or
            self.g_e_curr is None or
            self.g_s_next is None or
            self.g_e_next is None):
            print("DEBUG: Missing input data, skipping this cycle.")
            return

        # Compute the set/list of green intervals
        gamma_result = self.gamma_function(
            t0_in,
            current_state_in,
            self.g_e_curr,
            self.g_s_next,
            self.g_e_next
        )

        # Convert the intervals to JSON to avoid tuple handling errors in RTMaps
        #gamma_str = json.dumps(gamma_result)

        # Write the intervals (as JSON) to the output
        #self.outputs["gamma"].write(gamma_str)
        self.outputs["g_e_curr"].write(self.g_e_curr)
        self.outputs["g_s_next"].write(self.g_s_next)
        self.outputs["g_e_next"].write(self.g_e_next)
        self.outputs["state"].write(current_state_in)


    def Death(self):
        """
        Called once at the end (cleanup).
        """
        print("Green Window Estimator subsystem terminated.")

    # Define Gamma function
    def gamma_function(self, t0, current_state, g_e_curr, g_s_next, g_e_next):
        """
        Compute the available green window, Γ, based on the current signal phase:
          - If the signal is Green (states 4, 5, 6) at t0:
              Γ = [t0, g_e_curr) ∪ [g_s_next, g_e_next)
          - If the signal is Yellow or Red at t0:
              Γ = [g_s_next, g_e_next)
        Returns a list of tuple intervals.
        """
        # No green window available if signal is unavailable or dark
        if current_state in {0, 1}:
            return []

        gamma = []

        if current_state in {4, 5, 6}:  # Green states
            if t0 < g_e_curr:
                gamma.append((t0, g_e_curr))  # Add current green interval
            gamma.append((g_s_next, g_e_next))  # Always add next green interval

        else:  # For yellow or red phases, only the next green window is available.
            gamma.append((g_s_next, g_e_next))  # Add next green interval

        return gamma
    
    def estimate_green_window_from_countdown(self, t0, current_state, countdown_value:float, next_green_duration ):
        """
        Estimate g_s_next, g_e_next and g_e_curr (if applicable) from SPaT countdown values.

        Parameters:
        t0 (float): current RTMaps/system time in seconds
        current_state (int): current signal state 
        countdown_value (int): current countdown from 500 to 0
        next_green_duration (int): duration of green phase in ticks (default: 50)

        Returns:
        Tuple (g_e_curr, g_s_next, g_e_next)
        - g_e_curr: float or None (end of current green)
        - g_s_next: float or None (start of next green)
        - g_e_next: float or None (end of next green)
        """
        # Convert countdown ticks (0.1s per tick) to seconds
        time_until_phase_change = countdown_value * 0.1 
        g_e_curr = -1.0
        #print(f"{t0} + {time_until_phase_change} = ")
        #print(f"Next green duration: {next_green_duration}")

        if current_state in {2.0, 3.0}:  # RED phase now
            g_s_next = time_until_phase_change
            g_e_next = g_s_next + next_green_duration 

        elif current_state in {7.0, 8.0, 9.0}:  # YELLOW phase now
            red_duration = 50  # 50s of red after yellow
            g_s_next = time_until_phase_change + red_duration
            g_e_next = g_s_next + next_green_duration

        elif current_state in {4.0, 5.0, 6.0}:  # GREEN phase now
            yellow_red_duration = 50 * 2   # 100s of red and yellow after the next green
            g_e_curr = time_until_phase_change
            g_s_next = g_e_curr + yellow_red_duration
            g_e_next = g_s_next + next_green_duration 

        else:
            print("Unknown or unsupported signal state:", current_state)
            return None, None, None

        return g_s_next, g_e_next, g_e_curr  
    
    def state_name_to_number(self,state_name: str) -> float:
        """
        Converts a MovementPhaseState name (string) to its corresponding numeric value.
        Based on SAE J2735 standard enum values.

        Parameters:
            state_name (str): The textual state name (e.g., "stop-And-Remain")

        Returns:
            int: Corresponding state number, or -1 if not recognized
        """
        state_map = {
            "unavailable": 0.0,
            "dark": 1.0,
            "stop-Then-Proceed": 2.0,
            "stop-And-Remain": 3.0,
            "pre-Movement": 4.0,
            "permissive-Movement-Allowed": 5.0,
            "protected-Movement-Allowed": 6.0,
            "permissive-clearance": 7.0,
            "protected-clearance": 8.0,
            "caution-Conflicting-Traffic": 9.0
    }
        #print(f"Signal: {state_name}")
        return state_map.get(state_name.strip(), -1.0)
