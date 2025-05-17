import rtmaps.core as rt
import rtmaps.types
from rtmaps.base_component import BaseComponent
from shapely.geometry import LineString
import time
import math


class rtmaps_python(BaseComponent):
    """
    RTMaps component that:
    1) Does not receive any inputs.
    2) Internally defines two geographic coordinates:
    - Start (last node of lane 1): (longitude = -117.3386457, latitude = 33.9757505)
    - End (first node of lane 1): (longitude = -117.3396957, latitude = 33.9757438)
    3) Constructs a linear path (LineString) from the start to the end point.
    4) Interpolates 100 evenly spaced GPS coordinate pairs (longitude, latitude) along that path.
    5) Outputs each interpolated pair sequentially through:
   - longitude: FLOAT64 representing the interpolated longitude
   - latitude: FLOAT64 representing the interpolated latitude
    """
    def __init__(self):
        BaseComponent.__init__(self)

    def Dynamic(self):
        self.add_output("longitude", rtmaps.types.FLOAT64)
        self.add_output("latitude", rtmaps.types.FLOAT64)
        self.add_input("v_c", rtmaps.types.FLOAT64)  # km/h
      

    def Birth(self):
        # Define start and end GPS points (converted from microdegrees to degrees)
        #start = (-117.3386457, 33.9757505)  # last node
        #end   = (-117.3396957, 33.9757438)  # first node
        self.latitude = 33.9757505               # constant latitude
        self.longitude = -117.3381457            # starting longitude
        self.earth_radius = 6371000              # meters
        self.v_c = 48                            # default velocity in km/h
        self.last_update_time = time.time()      # track last update time

        print("GPS Generator initialized with velocity input.")

    def Core(self):
        # Get current time and calculate actual time step
        current_time = time.time()
        dt = current_time - self.last_update_time
        self.last_update_time = current_time

        # Limit dt to prevent large jumps
        dt = min(dt, 0.1)  # Cap at 100ms to prevent large jumps

        # Ensure input is available
        if not self.inputs["v_c"].ioelt:
            #print("No velocity input available.")
            v_c = self.v_c
        else:    
            # Read velocity input
            v_c = self.inputs["v_c"].ioelt.data  # in km/h
            self.v_c = v_c

        v_c_ms = v_c * (5.0 / 18.0)           # current velocity in m/s
        
        # Compute longitudinal degree distance
        meters_per_deg_lon = (math.pi / 180) * self.earth_radius * math.cos(math.radians(self.latitude))
        
        # Calculate step size based on actual time elapsed
        step_m = v_c_ms * dt
        delta_lon_deg = step_m / meters_per_deg_lon

        # Debug prints
        #print(f"dt: {dt:.3f}s, v_c: {v_c:.1f} km/h, v_c_ms: {v_c_ms:.1f} m/s, step_m: {step_m:.3f}m, delta_lon: {delta_lon_deg:.7f}°")

        # Update position
        self.longitude -= delta_lon_deg

        # Write outputs
        self.write("latitude", self.latitude)
        self.write("longitude", self.longitude)
        #print(f"[GPS Generator] v_c: {v_c:.2f} km/h, step: {step_m:.2f} m, new lon: {self.longitude:.7f}")
         


        
            

    def Death(self):
        print("Generated 100 GPS points from last node to first.")
