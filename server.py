import lib.connection
from lib.segment import Segment
import lib.segment as segment
from lib.filehandler import BufferFileHandler
import math
# from inc.ServerConfig import config
import configparser as cp
import socket
from lib.logger import Logger

# TODO: remove later
FILE_PATH = "generate.txt"
logger = Logger()

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

        self.windowSize = int(self.config["CONN"]["WINDOW_SIZE"])
        self.buffer_size = int(self.config["CONN"]["BUFFER_SIZE"]) - 12
        self.segmentCount = math.ceil(self.fileSize / self.buffer_size)
        self.ackTimeout = int(self.config["CONN"]["TIMEOUT"])
        self.connection.set_timeout(self.ackTimeout)
        logger.log("[!] Server initialized at " + self.ip + ":" + str(self.port))

    def listen_for_clients(self):
        # Waiting client for connect
        active = True
        logger.log("[!] Waiting for client...")
        while active:
            try:
                client_addr, segment, checksum_status = self.connection.listen_single_segment()
                logger.log("[!] Client trying to connect from " + client_addr[0] + ":" + str(client_addr[1]))
                if checksum_status:
                    if segment.get_flag()["syn"]:
                        if self.three_way_handshake(client_addr):
                            logger.log(f"[!] Client with address {client_addr[0]}:{client_addr[1]} connected")
                            self.file_transfer(client_addr)                    
                else:
                    logger.log("Invalid checksum, ignore this segment")
            except socket.timeout as e:
                logger.log(f"[!] no client found {e}")
                pass
            

    def start_file_transfer(self):
        # Handshake & file transfer for all client
        pass
    
    def __send_segments(self, seq_bound_window, seq_bases, client_addr):
        logger.log(f"[!] Sending segments from {seq_bases} to {seq_bound_window + seq_bases}")
        
        # stop = False
        # stopIdx = -1
        file_handler = BufferFileHandler(self.filePath, "rb", self.buffer_size)
        
        for i in range(seq_bound_window):
            content = file_handler.get_content(seq_bases + i)
            # if (content == b''):
            #     logger.log(f"[!] EOF with i: {seq_bases + i}")
            #     stop = True
            #     stopIdx = seq_bases + i
                
            segment = Segment()
            segment.set_payload(content)
            segment.set_header({"seq_num": seq_bases+i, "ack_num": 0})
            self.connection.send_data(segment, client_addr)
            logger.log("[!] Segment " + str(seq_bases + i) + " sent")

        # return stop, stopIdx

    def file_transfer(self, client_addr : ("ip", "port")):
        # File transfer, server-side, Send file to 1 client
        logger.log("[!] Start file transfer")
        
        seq_bases = 0
        stop = False
        seq_bound_window = min(self.segmentCount, seq_bases + self.windowSize) - seq_bases

        
        while (seq_bases < self.segmentCount):
            # logger.debug(f"segment count: {self.segmentCount}. seq bases: {seq_bases}. wdwsize: {self.windowSize}")
            # logger.debug(f"SBW: {seq_bound_window}")
            if stop:
                break
            
            logger.log(f"[!] Sending segments from {seq_bases} to {seq_bases + seq_bound_window}")
            self.__send_segments(seq_bound_window, seq_bases, client_addr)
            
            seq_bases_max = seq_bases + self.windowSize
            if seq_bound_window < self.windowSize:
                stop = True
                seq_bases_max = seq_bases + seq_bound_window

            logger.log(f"[!] Waiting for ACK from {seq_bases} to {seq_bound_window} with seq_bases_max = {seq_bases_max}")
            while seq_bases < seq_bases_max:
                logger.log(f"[!] Waiting for ACK {seq_bases} till seq_bases_max {seq_bases_max}")
                try:
                    addr, resp, checksum_success = self.connection.listen_single_segment()
                    logger.log(f"[!] Checksum status: {checksum_success}")
                    logger.log(f"[!] Addr: {addr}")
                    
                    if addr != client_addr:
                        logger.log("[!] Segment from unknown client, ignore")
                        continue
                    if not checksum_success:
                        logger.log("[!] Invalid checksum, ignore")
                        continue
                    if (resp.get_flag()["ack"]):
                        ack_num = resp.get_header()["ack_num"]
                        if (ack_num == seq_bases):
                            seq_bases += 1
                            seq_bound_window = min(self.segmentCount, seq_bases + self.windowSize) - seq_bases
                            logger.log(f"[!] ACK {ack_num} received, move window to {seq_bases}")
                        elif ack_num > seq_bases:
                            logger.log(f"[!] ACK {ack_num} received, move window to {ack_num + 1}")
                            seq_bases = ack_num + 1
                            seq_bound_window = min(self.segmentCount, seq_bases + self.windowSize) - seq_bases
                        else:
                            logger.log(f"[!] ACK {ack_num} below seq_bases {seq_bases} received, ignore")
                    
                except socket.timeout:
                    logger.log(f"[!] Timeout, resend segments from {seq_bases} to {seq_bound_window}")
                    break
                
                except Exception as e:
                    logger.log(f"[!] Exception: {str(e)}")
                    logger.log(f"[!] Timeout, resend segments from {seq_bases} to {seq_bound_window}")
                    break
                
        logger.log(f"[!] File transfer completed for client [{client_addr[0]}:{client_addr[1]}]")
        logger.log(f"[!] Send FIN to client [{client_addr[0]}:{client_addr[1]}]")
        self.__send_fin_flag(client_addr)

        try:
            addr, resp, checksum_success = self.connection.listen_single_segment()
            if addr == client_addr and checksum_success and resp.get_flag()["ack"]:
                logger.log(f"[!] Client [{client_addr[0]}:{client_addr[1]}] has closed connection")
        except Exception as e:
            logger.log(f"[!] [{client_addr[0]}:{client_addr[1]}] ACK tearing down timeout, force closing connection\n")

    def __send_fin_flag(self, client_addr):
        data = Segment()
        data.set_flag([segment.FIN_FLAG])
        self.connection.send_data(data, client_addr)

    def three_way_handshake(self, client_addr: ("ip", "port")) -> bool:
        # Three way handshake, server-side, 1 client
        logger.log("[!] Start three way handshake")
        syn_ack_segment = Segment()
        syn_ack_segment.set_flag([segment.SYN_FLAG, segment.ACK_FLAG])
        self.connection.send_data(syn_ack_segment, client_addr)
        logger.log("[!] SYN-ACK sent, waiting for ACK")
        addr, ack_segment, checksum_status = self.connection.listen_single_segment()
        # TODO: check if addr is the same, if not listen again
        # cover case where multiple clients
        try:
            if addr == client_addr and checksum_status:
                if ack_segment.get_flag()["ack"]:
                    logger.log("[!] ACK received, handshake completed")
                    return True
                else:
                    logger.log("[!] ACK not received, handshake failed")
                    return False
            else:
                logger.log("[!] Invalid checksum, handshake failed")
                return False
        except socket.timeout as e:
            logger.log(f"[!] timeout, handshake failed {e}")

if __name__ == '__main__':
    main = Server()
    main.listen_for_clients()
    main.start_file_transfer()
