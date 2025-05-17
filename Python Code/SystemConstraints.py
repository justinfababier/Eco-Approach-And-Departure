import rtmaps.core as rt
import rtmaps.types
from rtmaps.base_component import BaseComponent  # base class

class rtmaps_python(BaseComponent):
    
    def __init__(self):
        BaseComponent.__init__(self)

    def Dynamic(self):
        # self.add_input("in", rtmaps.types.ANY)  # define an input

        self.add_output("a_max", rtmaps.types.INTEGER64)
        self.add_output("d_max", rtmaps.types.INTEGER64)
        self.add_output("jerk_max", rtmaps.types.INTEGER64)
        
    def Birth(self):
        print("Passing through Birth()")

    def Core(self):
        # Just copy the input to the output here
        out = 10
        self.write("a_max", out)
        self.write("d_max", out)
        self.write("jerk_max", out)

    def Death(self):
        print("Passing through Death()")
