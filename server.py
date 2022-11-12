import lib.connection
from lib.segment import Segment
import lib.segment as segment
import math
# from inc.ServerConfig import config
import configparser as cp

# TODO: remove later
FILE_PATH = "README.md"

class Server:
    def __init__(self):
        # Init server
        # self.ip = input("Enter server IP: ")
        # self.port = int(input("Enter server port: "))
        # self.filePath = input("Enter file source path: ")

        # ===================== DEBUG =====================
        self.config = cp.ConfigParser()
        self.config.read("inc/server-config.ini")
        
        self.ip = self.config["CONN"]["IP"]
        self.port = int(self.config["CONN"]["PORT"])
        self.filePath = FILE_PATH
        # ===================== DEBUG =====================

        self.connection = lib.connection.Connection(self.ip, self.port)

        fileReader = open(self.filePath, "rb")
        self.file = fileReader.read()
        self.fileSize = fileReader.tell()
        fileReader.close()

        self.windowSize = 1024
        self.segmentCount = math.ceil(self.fileSize / self.windowSize)
        self.ackTimeout = 5
        print("[!] Server initialized at " + self.ip + ":" + str(self.port))

    def listen_for_clients(self):
        # Waiting client for connect
        active = True
        print("[!] Waiting for client...")
        while active:
            data, client_addr = self.connection.listen_single_segment()
            print("[!] Client connected from " + client_addr[0] + ":" + str(client_addr[1]))
            # if segment_checksum:
            #     if segment.get_flag().SYN:
            #         if self.three_way_handshake(client_addr):
            #             print(f"[!] Client with address {client_addr[0]}:{client_addr[1]} connected")
            # else:
            #     print("Invalid checksum, ignore this segment")
            

    def start_file_transfer(self):
        # Handshake & file transfer for all client
        pass

    def file_transfer(self, client_addr : ("ip", "port")):
        # File transfer, server-side, Send file to 1 client
        pass

    def three_way_handshake(self, client_addr: ("ip", "port")) -> bool:
       # Three way handshake, server-side, 1 client
       pass


if __name__ == '__main__':
    main = Server()
    main.listen_for_clients()
    main.start_file_transfer()
