import rtmaps.core as rt
import rtmaps.types
from rtmaps.base_component import BaseComponent
import numpy as np
import pdb

class rtmaps_python(BaseComponent):
    """
    RTMaps component that:
      - Receives an input (MAP_hex or SPAT_hex) as a hexadecimal ASCII string
      - Converts each hex string to an array of UINTEGER8 (byte array)
      - Outputs that byte array to MAP_hex or SPAT_byte
    """

    
    def __init__(self):
        BaseComponent.__init__(self)

    def Dynamic(self):
        # Define inputs as 8-bit unsigned integer arrays.
        self.add_input("SPAT_hex", rtmaps.types.TEXT_ASCII)

        # Define outputs as TEXT_ASCII for the hex representation.
        self.add_output("SPAT_byte", rtmaps.types.UINTEGER8)

    def Birth(self):
        print("Passing through Birth()")

    def Core(self):
        # Retrieve each input’s ASCII
        spat_hex = self.inputs["SPAT_hex"].ioelt.data
        #print(f"SPAT_hex input: '{spat_hex}'") 

        # Convert each input’s entire data array into a hex string
        spat_byte = to_byte_string(spat_hex)

        # Write out the results
        #print( spat_byte)
        self.write("SPAT_byte", spat_byte)

    def Death(self):
        print("Passing through Death()")

# Helper function to convert an Ioelt's data (array of bytes) into a single hex string
def to_byte_string(hex_str):
    # Strip BOM (Byte Order Mark) if it exists
    #hex_str = hex_str.lstrip('\ufeff')  # Remove BOM if present

     # Clean up any unnecessary whitespace, newlines, tabs, etc.
    hex_str = hex_str.replace(" ", "").replace("\n", "").replace("\r", "").replace("\t", "")

    # Print the cleaned-up string for debugging
    #print(f"Cleaned hex string: '{hex_str}'")

    # Check if the hex string is valid (even length and contains only hex digits)
    if hex_str and len(hex_str) % 2 == 0 and all(c in '0123456789abcdefABCDEF' for c in hex_str):
        # Convert each pair of characters (representing a byte) into integers and return as a numpy array
        return np.array([int(hex_str[i:i+2], 16) for i in range(0, len(hex_str), 2)], dtype=np.uint8)
    
    print("Invalid hex string provided.")
    return np.array([], dtype=np.uint8)  # Return an empty array if invalid hex string
