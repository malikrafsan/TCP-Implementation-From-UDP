import socket
from .segment import Segment

class Connection:
    def __init__(self, ip : str, port : int):
        # Init UDP socket
        self.ip  = ip
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.ip, self.port))

    def send_data(self, msg : Segment, dest : ("ip", "port")):
        # Send single segment into destination
        print(f"Send Data to {dest[0]}:{dest[1]}")
        print(f"Data: {msg}")
        self.socket.sendto(msg.get_bytes(), dest)

    # def listen_single_segment(self) -> Segment:
    def listen_single_segment(self):
        # Listen single UDP datagram within timeout and convert into segment
        data, addr = self.socket.recvfrom(32768)
        segment = Segment()
        segment.set_from_bytes(data)
        segment_checksum = segment.valid_checksum()
        return addr, segment, segment_checksum

    def close_socket(self):
        # Release UDP socket
        self.socket.close()
        
    def set_timeout(self, timeout):
        self.socket.settimeout(timeout)
        