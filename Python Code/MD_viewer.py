import rtmaps.core as rt
import rtmaps.types
from rtmaps.base_component import BaseComponent

class rtmaps_python(BaseComponent):
    """
    RTMaps component that:
      - Receives three inputs (MAP_i, SPAT_i, BSM_i) each as arrays of UINTEGER8
      - Converts the entire array of bytes to a single hexadecimal string
      - Outputs that string to MAP_o, SPAT_o, and BSM_o
    """
    
    def __init__(self):
        BaseComponent.__init__(self)

    def Dynamic(self):
        # Define inputs as 8-bit unsigned integer arrays.
        self.add_input("MAP_i", rtmaps.types.UINTEGER8)
        self.add_input("SPAT_i", rtmaps.types.UINTEGER8)
        self.add_input("BSM_i", rtmaps.types.UINTEGER8)

        # Define outputs as TEXT_ASCII for the hex representation.
        self.add_output("MAP_o", rtmaps.types.TEXT_ASCII)
        self.add_output("SPAT_o", rtmaps.types.TEXT_ASCII)
        self.add_output("BSM_o", rtmaps.types.TEXT_ASCII)

    def Birth(self):
        print("Passing through Birth()")

    def Core(self):
            
        try:   
            input_index = self.input_that_answered

            if input_index == 0:
                map_hex = self.to_hex_string(self.inputs["MAP_i"].ioelt)
                self.write("MAP_o", map_hex)
                print("MAP:"+ map_hex)

            elif input_index == 1:
                spat_hex = self.to_hex_string(self.inputs["SPAT_i"].ioelt)
                self.write("SPAT_o", spat_hex)
                print("SPAT:"+ spat_hex)

            elif input_index == 2:
                bsm_hex = self.to_hex_string(self.inputs["BSM_i"].ioelt)
                self.write("BSM_o", bsm_hex)
                print("BSM:"+ bsm_hex)

            elif input_index == -1:
                print("Timeout reached — no new input")

        except Exception as e:
            print("Crash in Core():", e)
    
    def Death(self):
        print("Passing through Death()")

# Helper function to convert an Ioelt's data (array of bytes) into a single hex string
    def to_hex_string(self, ioelt):
        # If the ioelt exists, has a 'data' attribute, and isn't empty:
        if ioelt and hasattr(ioelt, 'data') and len(ioelt.data) > 0:
        # Convert each byte in the array to a two-digit hex string, then concatenate
            return ''.join(format(byte, '02x') for byte in ioelt.data)
        return" "
    