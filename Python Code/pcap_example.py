import rtmaps.core as rt
import rtmaps.types
from rtmaps.base_component import BaseComponent
from scapy.all import rdpcap

# Python class that will be called from RTMaps.
class rtmaps_python(BaseComponent):
    
    def __init__(self):
        BaseComponent.__init__(self)

    def Dynamic(self):
        self.add_output("pcap_out", rtmaps.types.ANY)  # Define PCAP output
        self.add_property("pcap_file", "C:/path_to_your_file.pcap")  # File path property

    def Birth(self):
        print("Loading PCAP file...")
        pcap_path = self.get_property("pcap_file")
        self.packets = rdpcap(pcap_path)  # Load PCAP into memory
        self.index = 0  # Track replay index

    def Core(self):
        if self.index < len(self.packets):
            packet = bytes(self.packets[self.index])  # Convert packet to bytes
            self.write("pcap_out", packet)  # Send packet to RTMaps
            self.index += 1
            self.sleep(0.01)  # Simulate real-time processing

    def Death(self):
        print("Finished processing PCAP.")