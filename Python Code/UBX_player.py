import rtmaps.core as rt
import rtmaps.types
from rtmaps.base_component import BaseComponent
from sys import argv

from pyubx2.ubxreader import (
    ERR_LOG,
    GET,
    UBX_PROTOCOL,
    VALCKSUM,
    UBXReader,
    NMEA_PROTOCOL,
    RTCM3_PROTOCOL,
)



class rtmaps_python(BaseComponent):
    """
    RTMaps component that:
      - play a ubx file and stream longtitude and latitude
    """
    
    def __init__(self):
        BaseComponent.__init__(self)

    def Dynamic(self):
        # Define inputs as 8-bit unsigned integer arrays.

        # Define outputs as TEXT_ASCII for the hex representation.
        self.add_output("Longtitude", rtmaps.types.FLOAT64)
        self.add_output("Latitude", rtmaps.types.FLOAT64)

    def Birth(self):
        print("Passing through Birth()")

    def Core(self):
        filename = r"C:\Users\hungn\OneDrive - email.ucr.edu\Documents\EcoCAR_RtmapV2x\.EAD RTMaps Code\.EAD RTMaps Code\test_data_captures\rawgps.ubx"

        print(f"Opening file {filename}...")
        with open(filename, "rb") as stream:

            count = 0

            ubr = UBXReader(
                stream,
                protfilter=UBX_PROTOCOL | NMEA_PROTOCOL | RTCM3_PROTOCOL,
                quitonerror=ERR_LOG,
                validate=VALCKSUM,
                msgmode=GET,
                parsebitfield=True,
                errorhandler=errhandler,
            )
            for _, raw_data in ubr:
                lat = getattr(raw_data, 'lat', 'N/A')  # Default to 'N/A' if 'lat' doesn't exist
                lon = getattr(raw_data, 'lon', 'N/A')  # Default to 'N/A' if 'lon' doesn't exist
                
                if lat is not None and lon is not 'N/A':
                    lat = float(lat)  # Convert to float if it's a string or other type
                    lon = float(lon)  # Convert to float if it's a string or other type
                else:
                    lat = 0.0
                    lon = 0.0
                self.write("Longtitude", lon)
                self.write("Latitude", lat)
                #self.write("Ubx_stream", raw_data)
                count += 1

        print(f"\n{count} messages read.\n")
        print("Test Complete")

    def Death(self):
        print("Passing through Death()")

    

# Helper function to convert an Ioelt's data (array of bytes) into a single hex string
def to_hex_string(ioelt):
    # If the ioelt exists, has a 'data' attribute, and isn't empty:
    if ioelt and hasattr(ioelt, 'data') and ioelt.data.size > 0:
        # Convert each byte in the array to a two-digit hex string, then concatenate
        return ''.join(format(byte, '02x') for byte in ioelt.data)
    return ""

def errhandler(err):
    """
    Handles errors output by iterator.
    """

    print(f"\nERROR: {err}\n")
