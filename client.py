import lib.connection
from lib.segment import Segment
import lib.segment as segment
from lib.filehandler import BufferFileHandler
# from inc.ClientConfig import config
# from inc.ServerConfig import config as server_config
import configparser as cp

FILE_PATH = "a.txt"

class Client:
    def __init__(self):
        # Init client

        # self.ip = input("Enter IP: ")
        # self.port = int(input("Enter port: "))
        # self.filePath = input("Enter file destination path: ")
        # self.server_addr = (input("Enter server IP: "), int(input("Enter server port: ")))

        # ===================== DEBUG =====================
        self.client_config = cp.ConfigParser()
        self.client_config.read("inc/client-config.ini")
        
        self.server_config = cp.ConfigParser()
        self.server_config.read("inc/server-config.ini")
        
        self.ip = self.client_config["CONN"]["IP"]
        self.port = int(self.client_config["CONN"]["PORT"])
        self.filePath = FILE_PATH
        self.server_addr = (
            self.server_config["CONN"]["IP"], int(self.server_config["CONN"]["PORT"]))
        # ===================== DEBUG =====================

        self.connection = lib.connection.Connection(self.ip, self.port)
        self.windowSize = int(self.client_config["CONN"]["WINDOW_SIZE"])
        print("[!] Client initialized at " + self.ip + ":" + str(self.port))
        

    def three_way_handshake(self):
        # Three Way Handshake, client-side
        print("[!] Start three way handshake")
        print("[!] Sending SYN segment to server " + self.server_addr[0] + ":" + str(self.server_addr[1]))
        syn_segment = Segment()
        syn_segment.set_flag([segment.SYN_FLAG])
        self.connection.send_data(syn_segment, self.server_addr)

        print("[!] SYN sent, waiting for SYN-ACK")
        addr, syn_ack_segment, checksum_status = self.connection.listen_single_segment()
        if checksum_status:
            if syn_ack_segment.get_flag()["syn"] and syn_ack_segment.get_flag()["ack"]:
                print("[!] SYN-ACK received")
                ack_segment = Segment()
                ack_segment.set_flag([segment.ACK_FLAG])
                self.connection.send_data(ack_segment, self.server_addr)
                print("[!] ACK sent")
                print("[!] Connection established")
            else:
                print("[!] Connection failed")
        else:
            print("[!] Connection failed")

    def listen_file_transfer(self):
        # File transfer, client-side
        print("[!] Listen file transfer")
        
        stop = False
        cur_num = 0
        file_handler = BufferFileHandler(self.filePath, "wb")
        while not stop:
            try:
                addr, segment, checksum_status = self.connection.listen_single_segment()
                self.__display_info_segment(addr, segment, checksum_status)
                
                if addr != self.server_addr:
                    print("[!] Segment not from server, ignore")
                    continue
                if not checksum_status:
                    print("[!] Checksum failed, ignore")
                    continue
                if segment.get_flag()["fin"]:
                    print("[!] FIN received, stop")
                    stop = True
                    print("[!] Sending ACK to stop connection")
                    self.__send_ack_stop()
                if segment.get_header()["seq_num"] != cur_num:
                    print("[!] Segment not in order, ignore")
                    continue
                
                print("[!] Segment in order, write to file")
                file_handler.write(segment.get_payload())
                self.__send_ack_seq(cur_num)
                cur_num += 1
            except Exception as e:
                print("[!] Exception: " + str(e))
                break
                
    
    def __display_info_segment(self, addr, segment, checksum_status):
        print(f"[!] Received Segment {segment}")
        print(f"[!] Checksum status: {checksum_status}")
        print(f"[!] Addr: {addr}")
        
    def __send_ack_stop(self):
        data = Segment()
        data.set_flag([segment.ACK_FLAG])
        self.connection.send_data(data, self.server_addr)
        print(f"[!] ACK stop sent to server {self.server_addr[0]}:{self.server_addr[1]}")
    
    def __send_ack_seq(self, i):
        data = Segment()
        data.set_flag([segment.ACK_FLAG])
        data.set_header({"seq_num": 0, "ack_num": i})
        self.connection.send_data(data, self.server_addr)
        print(f"[!] ACK sent for seq {i} to server {self.server_addr[0]}:{self.server_addr[1]}")

if __name__ == '__main__':
    main = Client()
    main.three_way_handshake()
    main.listen_file_transfer()
