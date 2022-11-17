import socket
import fcntl
import struct
from .segment import Segment

class Connection:
    def __init__(self, ip : str, port : int):
        # Init UDP socket
        self.ip  = ip
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.ip, self.port))

    @staticmethod
    def __get_interface_ip_addr(ifname) -> str:
        ifname = ifname.encode('utf-8')
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(
            s.fileno(),
            0x8915,  # SIOCGIFADDR
            struct.pack("256s", ifname[:15])
        )[20:24])

    @staticmethod
    def select_ip_address():
        interfaces = socket.if_nameindex()
        ip_addresses = [Connection.__get_interface_ip_addr(ifname) for _, ifname in interfaces]
        while True:
            print("[!] Network interfaces and ip adresses available: ")
            for (i, ifname) in interfaces:
                print(f"{i}. {ifname} -> {ip_addresses[i-1]}")

            try:
                selected = int(input(f"[?] Select network interface [1-{len(interfaces)}]: "))
            except ValueError as e:
                print("[!] Error:", e)
                continue

            if selected >= 1 and selected <= len(ip_addresses):
                break
            print("[!] Error: index out of range")
        return ip_addresses[selected-1]


    def send_data(self, msg : Segment, dest : ("ip", "port")):
        # Send single segment into destination
        # print(f"Send Data to {dest[0]}:{dest[1]}")
        # print(f"Data: {msg}")
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
        