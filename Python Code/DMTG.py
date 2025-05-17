import rtmaps.core as rt
import rtmaps.types
from rtmaps.base_component import BaseComponent  # base class
import numpy as np
import json  # For handling Gamma input as JSON
import os

class rtmaps_python(BaseComponent):
    """
    RTMaps component that:
    1)  Receives x inputs:
        - scenario: Identified scenario (e.g., "Scenario 1", "Scenario 2", etc.)
        - d_0: Route distance to stop-bar (in meters)
        - v_c: Instantaneous velocity at current time instant t_0 (in km/h)
        - t: Current time (data type can be adjusted later)
        - gamma: Set of all subsequent green windows after t_0 (sent as JSON or a Python structure)
    2)  Performs trajectory or target velocity computations.
    3)  Outputs a recommended vehicle velocity:
        - v_t_kmh (kilometers-per-hour)
        - v_t_mph (miles-per-hour)
        
        (Maximum recommended vehicle velocity must be <= 35MPH (or, 56.327 KPH) per
        EcoCAR EV Challenge competition rules)
    """

    def __init__(self):
        BaseComponent.__init__(self)

    def Dynamic(self):
        """
        Declare inputs, outputs, and properties.
        """
        # Inputs:
        self.add_input("scenario", rtmaps.types.ANY)     # Scenario result (String)
        self.add_input("d_0", rtmaps.types.FLOAT64)             # Route distance to stop-bar (meters)
        self.add_input("v_c", rtmaps.types.FLOAT64)             # Instantaneous velocity at t_0 (kilometers-per-hour)
        self.add_input("t_0", rtmaps.types.INTEGER64)                   # Current absolute time (seconds)
        self.add_input("g_e_curr", rtmaps.types.FLOAT64)  # Estimated current green window end time
        self.add_input("g_s_next", rtmaps.types.FLOAT64)   # Estimated next green window start time
        self.add_input("g_e_next", rtmaps.types.FLOAT64)   # Estimated next green window end time

        # Output:
        self.add_output("v_t_kmh", rtmaps.types.FLOAT64)    # Recommended target velocity (kilometers-per-hour)
        self.add_output("v_t_mph", rtmaps.types.FLOAT64)    # Recommended target velocity (miles-per-hour)

    def Birth(self):
        """
        Called once at the beginning of the component lifecycle.
        """
        print("Trajectory Generator Component Initialized.")
        self.precomputed_velocity_profile = None
        self.profile_start_time = None
        self.profile_end_time = None
        self.dt = 0.1  # 100 ms
        self.last_scenario = None

    def Core(self):
        """
        Main logic executed when new data is available.
        """
        # Read inputs
        scenario = self.inputs["scenario"].ioelt.data
        d_0 = self.inputs["d_0"].ioelt.data
        v_c = self.inputs["v_c"].ioelt.data
        t_0 = round(float(self.inputs["t_0"].ioelt.data * 1e-6),2)
        g_e_curr = self.inputs["g_e_curr"].ioelt.data 
        g_s_next = self.inputs["g_s_next"].ioelt.data
        g_e_next = self.inputs["g_e_next"].ioelt.data


        # Validate critical inputs
        if scenario is None or d_0 is None or t_0 is None or g_e_curr is None or g_s_next is None or g_e_next is None:
            print("ERROR: Missing inputs!")
            return
        
        # Reset if scenario changes
        #if scenario != self.last_scenario:
            self.precomputed_velocity_profile = None
            self.last_scenario = scenario
        
        if self.precomputed_velocity_profile is None:
            (self.precomputed_velocity_profile, 
             self.profile_start_time, 
             self.profile_end_time) = self.compute_velocity_profile(t_0, d_0, v_c, g_e_curr, g_s_next, g_e_next, scenario)

        # Lookup velocity
        if t_0 <= self.profile_start_time:
            v_output = self.precomputed_velocity_profile[0][1]
        elif t_0 >= self.profile_end_time:
            v_output = self.precomputed_velocity_profile[-1][1]
        else:
            idx = int((t_0 - self.profile_start_time) / self.dt)
            idx = min(idx, len(self.precomputed_velocity_profile) - 1)
            v_output = self.precomputed_velocity_profile[idx][1]

        self.outputs["v_t_kmh"].write(v_output)
        self.outputs["v_t_mph"].write(v_output / 1.609)        
           
    def Death(self):
        """
        Called once at the end of the component lifecycle.
        """
        print("Trajectory Generator Component Terminated.")

    # Scenario 2 target velocity calculations (piecewise function)
    def f(self, t, v_c, v_h, v_d, m, n, t_1, d_0, t_2, t_3) -> float:
        if 0 <= t <= np.pi / (2 * m):
            return v_h - v_d * np.cos(m * t)
        elif t <= t_1:
            return v_h - (m / n) * v_d * np.cos(n * (t + (np.pi / n) - t_1))
        elif t <= d_0 / v_h:
            return v_h + (m / n) * v_d
        elif t <= t_2:
            return v_h - (m / n) * v_d * np.cos(n * (t + (3 * np.pi / (2 * n)) - t_2))
        elif t <= t_3:
            return v_h - v_d * np.cos(m * (t - t_3))
        else:
            return v_c

    def calculate_scen2_t_arr(self, t_e, t_cr, gamma) -> float:
        """
        Calculate t_arr for Scenario 2 based on the intersection between [t_e, t_cr] and gamma intervals.
        """
        intersections = []
        for interval in gamma:
            if len(interval) == 2:
                start, end = interval
                overlap_start = max(t_e, start)
                overlap_end = min(t_cr, end)
                if overlap_start < overlap_end:
                    intersections.append(overlap_start)
        return min(intersections) if intersections else None

    def calculate_scen4_t_arr(self, t_l, t_cr, gamma) -> float:
        """
        Calculate t_arr for Scenario 4 based on the intersection between [t_l, t_cr] and gamma intervals.
        """
        intersections = []
        for interval in gamma:
            if len(interval) == 2:
                start, end = interval
                overlap_start = max(t_cr, start)
                overlap_end = min(t_l, end)
                print(f"overlap start: {overlap_start}, overlap end: {overlap_end}, start: {start}, end: {end}")
                if overlap_start < overlap_end:
                    intersections.append(overlap_start)
        #print(f"[Scenario 4] t_l={t_l}, t_cr={t_cr}, Intersections={intersections}")            
        return min(intersections) if intersections else None

    # Scenario 3 target velocity function (static-like definition)
    def g(self, t, v_c, t_arr, g_next_s, t_5, m) -> float:
        #print(f"t = {t}, v_c = {v_c}, t_arr = {t_arr}, g_next_s = {g_next_s}, t5 = {t_5}, m = {m}")
        if 0 <= t < t_arr:
            v = v_c/2 + (v_c/2) * np.cos(m*t)
            if t > np.pi/ (m):  # Beyond 0-π/2m it should stay at 0
                v = 0.0
            return v
        elif t_arr <= t < g_next_s:
            return 0.0
        elif g_next_s <= t < t_5:
            #return v_c * (1 - np.cos() m * (t - g_next_s))) / 2
            #ramp_duration = t_5 - g_next_s
            #m = np.pi / ramp_duration  # faster ramp
            return v_c/2 + (v_c/2) * np.cos(m*(t-t_5))
        else:
            return v_c

    # Scenario 4 target velocity calculations (piecewise function)
    def h(self, t, v_c, v_h, v_d, m, n, t_1, d_0, t_2, t_3) -> float:
        if 0 <= t <= np.pi / (2 * m):
            return v_h - v_d * np.cos(m * t)
        elif t <= t_1:
            return v_h - (m / n) * v_d * np.cos(n * (t + (np.pi / n) - t_1))
        elif t <= d_0 / v_h:
            return v_h + (m / n) * v_d
        elif t <= t_2:
            return v_h - (m / n) * v_d * np.cos(n * (t + (3 * np.pi / (2 * n)) - t_2))
        elif t <= t_3:
            return v_h - v_d * np.cos(m * (t - t_3))
        else:
            return v_c

    def calculate_n_scen2and4(self, a_max, d_max, jerk_max, v_d, v_h, d_0) -> float:
        pi = np.pi
        valid_n_candidates = []

        if abs(v_d) > 1e-6:
            n_acc = a_max / abs(v_d)
            n_dec = d_max / abs(v_d)
            n_jerk = (jerk_max / abs(v_d))**0.5
            valid_n_candidates.extend([n_acc, n_dec, n_jerk])

        if abs(v_h) > 1e-6 and abs(d_0) > 1e-6:
            n_lower_bound = ((np.pi / 2) - 1) * (v_h / d_0)
        else:
            n_lower_bound = 0.01

        # Final value is the maximum n that is ≥ n_lower_bound and satisfies all upper bounds
        n = max(min(valid_n_candidates), n_lower_bound)

        #print(f"[n Calculation] candidates={valid_n_candidates}, lower bound={n_lower_bound:.4f}, selected n={n:.4f}")
        return n



    def calculate_m_scen2and4(self, n, d_0, v_h) -> float:
        pi_over_2 = np.pi / 2
        safe_eps = 1e-6  # small number to prevent divide by zero

        numerator_part1 = -pi_over_2 * n
        inside_sqrt = (pi_over_2 * n)**2 - 4 * n**2 * ((pi_over_2 - 1) - (d_0 / v_h) * n)

        if inside_sqrt < 0:
            #print(f"[Warning] sqrt_term negative: {inside_sqrt:.6f}, setting sqrt_term=0")
            sqrt_term = 0.0
        else:
            sqrt_term = np.sqrt(inside_sqrt)

        numerator = numerator_part1 - sqrt_term
        denominator = 2 * ((pi_over_2 - 1) - (d_0 / v_h) * n)

        if abs(denominator) < safe_eps:
            #print(f"[Warning] denominator too small: {denominator:.6f}, setting m=1e6")
            m = 1e6
        else:
            m = numerator / denominator

        #print(f"[m Calculation] numerator={numerator:.6f}, denominator={denominator:.6f}, m={m:.6f}")
        return m


    def calculate_m_scen3(self, d_0, v_h) -> float:
        m = v_h / d_0 * np.pi
        return m

    def calculate_n_scen3(self, d_0, v_h) -> float:
        n = v_h / d_0 * np.pi
        return n
    
    def compute_velocity_profile(self, t_0, d_0, v_c, g_e_curr, g_s_next, g_e_next, scenario):
        profile = []
        # Define additional parameters
        a_max = 1.0          # maximum acceleration in m/s²
        d_max = 1.0         # maximum deceleration in m/s²
        jerk_max = 1.0       # maximum jerk in m/s³
        v_limit = 56.33   # speed limit in km/h (35mph) 
        v_coast = 12.87 # km/h as defined, equivalent to 8 MPH

        # Convert velocity from km/h to m/s for calculations:
        v_c_ms = v_c * (5.0 / 18.0)           # current velocity in m/s
        v_limit_ms = v_limit * (5.0 / 18.0)   # velocity limit in m/s
        v_coast_ms = v_coast * (5.0 / 18.0)

        # Obtain critical time
        term1p = (2 * a_max) / (v_limit_ms - v_c_ms)
        term2p = np.sqrt((2 * jerk_max) / (v_limit_ms - v_c_ms))
        term1q = (2 * a_max) / (v_c_ms - v_coast_ms)
        term2q = np.sqrt((2 * jerk_max) / (v_c_ms - v_coast_ms))

        p = min(term1p, term2p)
        q = min(term1q, term2q)

        t_cr = d_0 / v_c_ms
        t_e = ((d_0 - v_c_ms * np.pi / (2 * p)) / v_limit_ms) + (np.pi / (2 * p))
        t_l = ((d_0 - v_c_ms * np.pi / (2 * q)) / v_coast_ms) + (np.pi / (2 * q))
        print(f"DEBUG: Calculated d_0={v_c_ms}, t_e={t_e}, t_l={t_l}, t_0={t_0}, t_cr={t_cr}")

        if g_e_curr == -1:
            # Case 1: No current green phase
            gamma_intervals = ((g_s_next, g_e_next),)
        else:
            # Case 2: Current green phase exists
            gamma_intervals = ((t_0, g_e_curr), (g_s_next, g_e_next))

        if scenario == "Scenario 1":
            t_end = t_0 + 30.0
            for t in np.arange(t_0, t_end + self.dt, self.dt):
                v =  v_c_ms * 3.6  
                if v >= v_limit:
                    v = v_limit  
                profile.append((t, v))

        elif scenario == "Scenario 2"or scenario == "Scenario 4":
            """
            Scenario 2 target velocity calculations.
            """
            # Difference between current velocity and target average
            if scenario == "Scenario 2":                
                t_arr = self.calculate_scen2_t_arr(t_e, t_cr, gamma_intervals)
            elif scenario == "Scenario 4":
                t_arr = self.calculate_scen4_t_arr(t_l, t_cr, gamma_intervals)   
            
            if t_arr is None:
                print("ERROR: No valid intersection in Scenario 2 or 4.")
                return
            
            # Target average velocity given average target arrival time, t_arr
            v_h = d_0 / t_arr   # target average velocity (m/s)
            v_d = v_h - v_c_ms  # velocity difference (m/s)

            # Parameters 'm' and 'n' for Scenarios 2 and 4
            n = self.calculate_n_scen2and4(a_max, d_max, jerk_max, v_d, v_h, d_0)
            m = self.calculate_m_scen2and4(n, d_0, v_h)

            # Times used for function f(t|v_c, v_h)
            t_1 = (np.pi / (2 * m)) + (np.pi / (2 * n))
            t_2 = (d_0 / v_h) + (np.pi / (2 * n))
            t_3 = (d_0 / v_h) + (np.pi / (2 * m)) + (np.pi / (2 * n))
            t_end = t_3 + 1.0
            print(f"[f() input debug] v_c={v_c_ms:.2f}, v_h={v_h:.2f}, v_d={v_d:.2f}, m={m:.4f}, n={n:.4f}, t_1={t_1:.2f}, d_0={d_0:.2f}, t_2={t_2:.2f}, t_3={t_3:.2f}")

            for t in np.arange(t_0, t_end + self.dt, self.dt):
                if scenario == "Scenario 2":
                    v = self.f(t - t_0, v_c_ms, v_h, v_d, m, n, t_1, d_0, t_2, t_3) 
                elif scenario == "Scenario 4":
                    v = self.h(t - t_0, v_c_ms, v_h, v_d, m, n, t_1, d_0, t_2, t_3)   
                v *= 3.6
                profile.append((t, v))

        elif scenario == "Scenario 3":
            """
            Scenario 3: Stop-and-wait strategy.
            
            In this approach, the vehicle is brought to a full stop before the stop-bar and waits
            for the next green. Here, we simply set t_arr equal to the start time of the first green
            window extracted from gamma.
            """
            # Use the piecewise velocity function g for Scenario 3.
            # (Assumed definition:
            #   if 0 <= t <= t_arr:        return v_c/2 + (v_c/2) * cos(m*t)
            #   elif t_arr <= t < g_s_next:  return 0.0
            #   elif g_s_next <= t < t_5:    return v_c/2 + (v_c/2) * cos(m*(t - t_5))
            #   else:                       return v_c )
           
            # Ensure current velocity (v_c_ms is computed earlier) is greater than coasting velocity.
            if v_c_ms <= v_coast_ms:
                print("ERROR: v_c (in m/s) is below or equal to the coasting threshold. Scenario 3 cannot be computed.")
                return

            if g_s_next is None:
                print("ERROR: No valid green window start (g_s_next) found for Scenario 3.")
                return

            # Set t_arr equal to g_s_next as required.
            #t_arr = g_s_next

            # Define target acceleration parameters.
            # Assume the target velocity after acceleration is half of v_c_ms.
            v_h = v_c_ms / 2.0
            t_arr = d_0 / v_h

            # Compute acceleration profile parameters for Scenario 3 using helper functions:
            n = self.calculate_n_scen3(d_0, v_h)
            m = self.calculate_m_scen3(d_0, v_h)
            
            # Define additional timing parameters for the acceleration phase.
            # For example, let t_4 be an offset after g_s_next and t_5 mark the end of the ramp-up phase.
            t_4 = g_s_next + (np.pi / (2 * n))
            t_5 = t_4 + (np.pi / (m * 2))
            t_end = t_5 + 1.0

            for t in np.arange(t_0, t_end + self.dt, self.dt):
                v = self.g(t - t_0, v_c_ms, t_arr, g_s_next, t_5, m)
                v *= 3.6
                if v >= v_limit:
                    v = v_limit
                profile.append((t, v))
        
        self.save_profile_to_file(profile, scenario, t_0, g_e_curr, g_s_next, g_e_next,v_c)
        return profile, t_0, t_0 + t_end
    
    def save_profile_to_file(self, profile, scenario, t_start, g_e_curr, g_s_next, g_e_next, v_c):

        # Create a directory if not exists
        save_dir =  r"C:\Users\hungn\OneDrive - email.ucr.edu\Documents\EcoCAR_RtmapV2x\Velocity profile"
        os.makedirs(save_dir, exist_ok=True)

        # Format the filename
        filename = os.path.join(save_dir, f"profile_{scenario}_start_{float(t_start)}_vel_{round(v_c,2)}.json")

        Base_parameter = [{"Current green window end": round(g_e_curr,2), "Next green window start": round(g_s_next,2), "Next green window end": round(g_e_next), "Current Velocity:": f"{round(v_c,2)} km/h"}]

        # Convert the profile into a simple list
        profile_list = [{"time": round(t, 2), "velocity_kmh": round(v, 2)} for (t, v) in profile]

        # Save to JSON
        with open(filename, "w") as f:
            json.dump(Base_parameter, f, indent=2)
            json.dump(profile_list, f, indent=2)

        print(f"[Profile Saved] {filename}")


