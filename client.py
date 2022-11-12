import lib.connection
from lib.segment import Segment
import lib.segment as segment
from inc.ClientConfig import config
from inc.ServerConfig import config as server_config

FILE_PATH = "a.txt"

class Client:
    def __init__(self):
        # Init client

        # self.ip = input("Enter IP: ")
        # self.port = int(input("Enter port: "))
        # self.filePath = input("Enter file destination path: ")
        # self.server_addr = (input("Enter server IP: "), int(input("Enter server port: ")))

        # ===================== DEBUG =====================
        self.ip = config.IP
        self.port = config.PORT
        self.filePath = FILE_PATH
        self.server_addr = (server_config.IP, server_config.PORT)
        # ===================== DEBUG =====================

        self.connection = lib.connection.Connection(self.ip, self.port)
        self.windowSize = config.WINDOW_SIZE
        print("[!] Client initialized at " + self.ip + ":" + str(self.port))
        

    def three_way_handshake(self):
        # Three Way Handshake, client-side
        print("[!] Trying to connect to " + self.server_addr[0] + ":" + str(self.server_addr[1]))
        print("[!] Start three way handshake")
        syn_segment = Segment()
        self.connection.send_data(syn_segment, self.server_addr)

    def listen_file_transfer(self):
        # File transfer, client-side
        pass


if __name__ == '__main__':
    main = Client()
    main.three_way_handshake()
    main.listen_file_transfer()
