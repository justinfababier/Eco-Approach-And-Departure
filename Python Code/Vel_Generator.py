# ---------------- TEMPLATE ---------------------------------------
# This is a template to help you start writing PythonBridge code  -
# -----------------------------------------------------------------

import rtmaps.core as rt
import rtmaps.types
from rtmaps.base_component import BaseComponent
from shapely.geometry import LineString


# Python class that will be called from RTMaps.
class rtmaps_python(BaseComponent):
    
    # Constructor has to call the BaseComponent parent class
    def __init__(self):
        BaseComponent.__init__(self)  # call base class constructor

    # Dynamic is called frequently:
    # - When loading the diagram
    # - When connecting or disconnecting a wire
    # Here you create your inputs, outputs and properties
    def Dynamic(self):
        # Adding an input called "in" of ANY type
        self.add_input("feed", rtmaps.types.FLOAT64) 
        self.add_output("v_c", rtmaps.types.FLOAT64)
        
# Birth() will be called once at diagram execution startup
    def Birth(self):
        print("Passing through Birth()")
        self.v_c = 48.0
        self.dt = 0.1

# Core() is called every time you have a new inputs available, depending on your chosen reading policy
    def Core(self):
        a_max = 10
        d_max = 10
        max_delta = 0.0
        delta_v = 0.0
        # Just copy the input to the output here
        if  hasattr(self.inputs["feed"].ioelt, "data"):
            target = self.inputs["feed"].ioelt.data
            delta_v = target - self.v_c
            #self.v_c = target
            if delta_v > 0.0:
                max_delta = a_max * self.dt
            else:
                max_delta = d_max * self.dt
            
            delta_v = max(-max_delta, min(delta_v, max_delta))
            #self.v_c += delta_v
            self.v_c = target

        # Update speed
        self.outputs["v_c"].write(self.v_c)

# Death() will be called once at diagram execution shutdown
    def Death(self):
        print("Passing through Death()")
