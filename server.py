import lib.connection
from lib.segment import Segment
import lib.segment as segment
from lib.filehandler import BufferFileHandler
import math
# from inc.ServerConfig import config
import configparser as cp
import socket
from lib.logger import Logger
import argparse
import pathlib
import time

logger = Logger(Logger.MODE_REGULAR)

class Server:
    def __init__(self, port: int, filepath: str, send_metadata: bool = False):
        self.config = cp.ConfigParser()
        self.config.read("inc/server-config.ini")
        
        self.ip = lib.connection.Connection.select_ip_address()
        self.port = port
        self.filePath = filepath
        self.fileSize = BufferFileHandler(self.filePath, "rb").file_size()

        self.connection = lib.connection.Connection(self.ip, self.port)
        self.send_metadata = send_metadata
        self.windowSize = int(self.config["CONN"]["WINDOW_SIZE"])
        self.buffer_size = (int(self.config["CONN"]["BUFFER_SIZE"]) - 12) // 3
        self.segmentCount = math.ceil(self.fileSize / self.buffer_size)
        self.ackTimeout = int(self.config["CONN"]["TIMEOUT"])
        self.connection.set_timeout(self.ackTimeout)
        logger.log("[!] Server initialized at " + self.ip + ":" + str(self.port))
        self.clientList = []

    def listen_for_clients(self):
        # Waiting client for connect
        listening = True
        logger.log("[!] Waiting for client...")
        while listening:
            try:
                client_addr, segment, checksum_status = self.connection.listen_single_segment()
                logger.log("[!] Received request from " + client_addr[0] + ":" + str(client_addr[1]))
                if checksum_status:
                    if segment.get_flag()["syn"]:
                        self.clientList.append(client_addr)
                        prompt = input("[?] Listen more? (y/n) ")
                        if prompt != 'y':
                            listening = False                
                else:
                    logger.critical("[!!!] CHECKSUM FAILED, DISCARDING PACKET")
            except socket.timeout as e:
                logger.log(f"[!] No client found {e}")
                pass
            

    def __print_client_list(self):
        logger.log()
        logger.log("Client list:")
        for (i, client) in enumerate(self.clientList):
            logger.log(f"{i+1}. {client[0]}:{client[1]}")
        logger.log()

    def start_file_transfer(self):
        # Handshake & file transfer for all client
        self.__print_client_list()
        logger.log("[!] Commencing file transfer...")
        for client_no, client_addr in enumerate(self.clientList):
            if self.three_way_handshake(client_addr, client_no+1):
                logger.log(f"[!] Client with address {client_addr[0]}:{client_addr[1]} connected")
                
                if self.send_metadata:
                    self.__send_metadata(client_addr)
                self.file_transfer(client_addr, client_no+1)       
    
    def __send_segments(self, seq_bound_window, seq_bases, client_addr, client_no):
        logger.log(f"[!] [CLIENT {client_no}] Sending segments from {seq_bases} to {seq_bound_window + seq_bases}")
        file_handler = BufferFileHandler(self.filePath, "rb", self.buffer_size)
        
        for i in range(seq_bound_window):
            content = file_handler.get_content(seq_bases + i - 1)
            segment = Segment()
            segment.set_payload(content)
            segment.set_header({"seq_num": seq_bases+i, "ack_num": 0})
            self.connection.send_data(segment, client_addr)
            logger.log(f"[!] [CLIENT {client_no}] Segment " + str(seq_bases + i) + " sent")

    def file_transfer(self, client_addr : ("ip", "port"), client_no : int):
        logger.log(f"[!] [CLIENT {client_no}] Start file transfer")
        last_ack_time = time.time()
        seq_bases = 1
        seq_bound_window = min(self.segmentCount+1, seq_bases + self.windowSize) - seq_bases
        
        while (seq_bases < (self.segmentCount+1)):
            logger.debug(f"SEG COUNT {self.segmentCount}")
            logger.debug(f"SEG BASES {seq_bases}")
            logger.debug(f"SEQ WINDOW SIZE {self.windowSize}")
            logger.debug(f"SEQ BOUND WINDOW {seq_bound_window}")
            logger.log(f"[!] [CLIENT {client_no}] Sending segments from {seq_bases} to {seq_bases + seq_bound_window}")
            self.__send_segments(seq_bound_window, seq_bases, client_addr, client_no)
            
            seq_bases_max = seq_bases + self.windowSize
            if seq_bound_window < self.windowSize:
                seq_bases_max = seq_bases + seq_bound_window

            logger.log(f"[!] [CLIENT {client_no}] Waiting for ACK from {seq_bases} to {seq_bound_window} with seq_bases_max = {seq_bases_max}")
            while seq_bases < seq_bases_max:
                logger.log(f"[!] [CLIENT {client_no}] Waiting for ACK {seq_bases} till seq_bases_max {seq_bases_max}")
                try:
                    addr, resp, checksum_success = self.connection.listen_single_segment()
                    last_ack_time = time.time()
                    logger.log(f"[!] [CLIENT {client_no}] Checksum status: {checksum_success}")
                    logger.log(f"[!] [CLIENT {client_no}] Addr: {addr}")
                    
                    if addr != client_addr:
                        logger.log(f"[!] [CLIENT {client_no}]  Segment from unknown client, ignore")
                        continue
                    if not checksum_success:
                        logger.critical(f"[!!!] [CLIENT {client_no}] Invalid checksum, ignore")
                        continue
                    if (resp.get_flag()["ack"]):
                        ack_num = resp.get_header()["ack_num"]
                        if (ack_num == seq_bases):
                            seq_bases += 1
                            seq_bound_window = min(self.segmentCount+1, seq_bases + self.windowSize) - seq_bases
                            logger.log(f"[!] [CLIENT {client_no}] ACK {ack_num} received, move window to {seq_bases}")
                        elif ack_num > seq_bases:
                            logger.log(f"[!] [CLIENT {client_no}] ACK {ack_num} received, move window to {ack_num + 1}")
                            seq_bases = ack_num + 1
                            seq_bound_window = min(self.segmentCount+1, seq_bases + self.windowSize) - seq_bases
                        else:
                            logger.log(f"[!] [CLIENT {client_no}] ACK {ack_num} below seq_bases {seq_bases} received, ignore")
                    
                except socket.timeout:
                    MAX_NOT_RECEIVING_TIMEOUT = 10
                    if time.time() - last_ack_time > MAX_NOT_RECEIVING_TIMEOUT:
                        logger.warning(f"[!!!] [CLIENT {client_no}] No ACK received for {MAX_NOT_RECEIVING_TIMEOUT} seconds, skip to next client")
                        return
                    logger.log(f"[!] [CLIENT {client_no}] Timeout, resend segments from {seq_bases} to {seq_bound_window}")
                    break
                
                except Exception as e:
                    logger.log(f"[!] [CLIENT {client_no}] Exception: {str(e)}")
                    logger.log(f"[!] [CLIENT {client_no}] Timeout, resend segments from {seq_bases} to {seq_bound_window}")
                    break
                
        logger.log(f"[!] [CLIENT {client_no}] File transfer completed for client [{client_addr[0]}:{client_addr[1]}]")
        logger.log(f"[!] [CLIENT {client_no}] Send FIN to client [{client_addr[0]}:{client_addr[1]}]")
        self.__send_fin_flag(client_addr)

        try:
            addr, resp, checksum_success = self.connection.listen_single_segment()
            if addr == client_addr and checksum_success and resp.get_flag()["ack"]:
                logger.log(f"[!] [CLIENT {client_no}] [{client_addr[0]}:{client_addr[1]}] has closed connection")
        except Exception as e:
            logger.log(f"[!] [CLIENT {client_no}] [{client_addr[0]}:{client_addr[1]}] ACK tearing down timeout, force closing connection\n")

    def __send_fin_flag(self, client_addr):
        data = Segment()
        data.set_flag([segment.FIN_FLAG])
        self.connection.send_data(data, client_addr)

    def three_way_handshake(self, client_addr: ("ip", "port"), client_no) -> bool:
        # Three way handshake, server-side, 1 client
        logger.log(f"[!] [CLIENT {client_no}] Start three way handshake to client {client_addr[0]}:{client_addr[1]}")
        syn_ack_segment = Segment()
        syn_ack_segment.set_flag([segment.SYN_FLAG, segment.ACK_FLAG])

        if self.send_metadata:
            enable_metadata_flag = b"\xff" * 10
            syn_ack_segment.set_payload(enable_metadata_flag)

        self.connection.send_data(syn_ack_segment, client_addr)
        try:
            logger.log(f"[!] [CLIENT {client_no}] SYN-ACK sent, waiting for ACK")
            addr, ack_segment, checksum_status = self.connection.listen_single_segment()
            if addr == client_addr and checksum_status:
                if ack_segment.get_flag()["ack"]:
                    logger.log(f"[!] [CLIENT {client_no}] ACK received, handshake completed")
                    return True
                else:
                    logger.log(f"[!] [CLIENT {client_no}] ACK not received, handshake failed")
                    return False
            else:
                logger.log(f"[!] [CLIENT {client_no}] Invalid checksum, handshake failed")
                return False
        except socket.timeout as e:
            logger.log(f"[!] [CLIENT {client_no}] timeout, handshake failed {e}")
            return False

    def __send_metadata(self, client_addr: ("ip", "port")):
        path = pathlib.Path(self.filePath)
        filename = path.stem
        ext = path.suffix
        
        payload = bytes(filename, "ascii") + b"\x00" + bytes(ext, "ascii")
        data = Segment()
        data.set_flag([segment.MET_FLAG])
        data.set_payload(payload)

        self.connection.send_data(data, client_addr)
        

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("<broadcast_port>", type=int)
    parser.add_argument("<filepath>", type=str)
    parser.add_argument("-m", default=False, action="store_true", help="Flag to send metadata")
    args = vars(parser.parse_args())

    main = Server(args["<broadcast_port>"], args["<filepath>"], args["m"])
    main.listen_for_clients()
    main.start_file_transfer()
