import lib.connection
from lib.segment import Segment
import lib.segment as segment
from lib.filehandler import BufferFileHandler
import socket
import configparser as cp
from lib.logger import Logger
import argparse
import time

logger = Logger(Logger.MODE_REGULAR)

class Client:
    def __init__(self, client_port: int, server_ip_address: int, broadcast_port: int, filepath: str):
        # Init client
        self.client_config = cp.ConfigParser()
        self.client_config.read("inc/client-config.ini")
        
        self.server_config = cp.ConfigParser()
        self.server_config.read("inc/server-config.ini")
        
        self.ip = self.client_config["CONN"]["IP"]
        self.port = client_port
        self.filePath = filepath
        self.server_addr = (
            server_ip_address, broadcast_port)
        self.handshake_timeout = int(self.client_config["CONN"]["HANDSHAKE_TIMEOUT"])
        self.regular_timeout = int(
            self.client_config["CONN"]["REGULAR_TIMEOUT"])

        self.connection = lib.connection.Connection(self.ip, self.port)
        self.windowSize = int(self.client_config["CONN"]["WINDOW_SIZE"])
        self.metadata_enabled = False
        logger.log("[!] Client initialized at " + self.ip + ":" + str(self.port))
        

    def three_way_handshake(self):
        # Three Way Handshake, client-side
        self.connection.set_timeout(self.handshake_timeout)
        
        logger.log("[!] Start three way handshake")
        logger.log("[!] Sending SYN segment to server " + self.server_addr[0] + ":" + str(self.server_addr[1]))
        syn_segment = Segment()
        syn_segment.set_flag([segment.SYN_FLAG])
        self.connection.send_data(syn_segment, self.server_addr)

        logger.log("[!] SYN sent, waiting for SYN-ACK")
        try:
            listening = True
            start_time = time.time()
            while listening:
                addr, syn_ack_segment, checksum_status = self.connection.listen_single_segment()
                if (addr != self.server_addr):
                    logger.log(f"[!] Packet received from {addr[0]}:{addr[1]}. Ignoring..")
                else:
                    listening = False  

                if (time.time() - start_time > self.handshake_timeout):
                    raise socket.timeout("timed out")

            if not checksum_status:
                logger.critical("[!!!] CHECKSUM FAILED")
                logger.log("[!] Connection failed")
                return

            if not syn_ack_segment.get_flag()["syn"] or not syn_ack_segment.get_flag()["ack"]:
                logger.log("[!] Connection failed")
                return

            logger.log("[!] SYN-ACK received")
            logger.log("[!] Checking enable metadata flag...")
            
            payload = syn_ack_segment.get_payload()
            if payload == (b"\xff" * 10):
                logger.log("[!] File metadata enabled")
                self.metadata_enabled = True
            else:
                logger.log("[!] File metadata disabled")

            ack_segment = Segment()
            ack_segment.set_flag([segment.ACK_FLAG])
            self.connection.send_data(ack_segment, self.server_addr)

            logger.log("[!] ACK sent")
            logger.log("[!] Connection established")
        except socket.timeout as e:
            logger.log(f"[!] Connection timeout: {str(e)}")
            exit(1)

    def listen_file_transfer(self):
        # File transfer, client-side
        self.connection.set_timeout(self.regular_timeout)
        last_segment_time = time.time()
        logger.log("[!] Listen file transfer")
        
        stop = False
        cur_num = 1
        file_handler = BufferFileHandler(self.filePath, "wb")

        if self.metadata_enabled:
            self.__receive_metadata()
            last_segment_time = time.time()

        while not stop:
            try:
                addr, segment, checksum_status = self.connection.listen_single_segment()
                last_segment_time = time.time()
                if addr != self.server_addr:
                    logger.log("[!] Segment not from server, ignore")
                    continue

                if not checksum_status:
                    logger.log("[!] Checksum failed, ignore")
                    logger.critical("[!!!] CHECKSUM FAILED")
                    continue

                if segment.get_flag()["fin"]:
                    logger.log("[!] FIN received, stop")
                    stop = True
                    logger.log("[!] Sending ACK to stop connection")
                    self.__send_ack_stop()
                    logger.log("[!] Connection closed")
                    break

                seq_num = segment.get_header()["seq_num"]
                if seq_num != cur_num:
                    logger.log(f"[!] Segment not in order, expect seq_num {cur_num}, got {seq_num} ignore")
                    continue
                
                logger.log("[!] Segment in order, write to file")
                file_handler.write(segment.get_payload())
                self.__send_ack_seq(cur_num)
                cur_num += 1
             
            except socket.timeout:
                MAX_NOT_RECEIVING_TIMEOUT = 10
                if (time.time() - last_segment_time > MAX_NOT_RECEIVING_TIMEOUT):
                    logger.warning(f"[!!!] Too many timeout, stop")
                    exit(1)

                logger.log(f"[!] Connection timeout")
                if (cur_num > 0):
                    logger.log(f"[!] Resend ACK for seq {cur_num-1}")
                    self.__send_ack_seq(cur_num - 1)
                else:
                    logger.log(f"[!] timeout on first segment, exit")
                    exit(1)

    def __receive_metadata(self):
        while True:
            try:
                addr, segment, checksum_status = self.connection.listen_single_segment()
                if addr != self.server_addr:
                    logger.log("[!] Metadata segment not from server, ignore")
                    continue

                if not checksum_status:
                    logger.log("[!] Metadata checksum failed, ignore")
                    logger.critical("[!!!] CHECKSUM FAILED")
                    continue

                if not segment.get_flag()["met"]:
                    logger.log("[!] Segment is not metadata, ignore")
                    continue

                payload = segment.get_payload()
                filename, ext = payload.split(b"\x00")
                filename = filename.decode("ascii")
                ext = ext.decode("ascii")

                logger.log("[!] ---- START OF METADATA ----")
                logger.log(f"[!] Filename : {filename}")
                logger.log(f"[!] Extension: {ext}")
                logger.log("[!] ----- END OF METADATA -----")
                break

            except socket.timeout:
                logger.log(f"[!] Metadata connection timeout")
                break
        
    def __send_ack_stop(self):
        data = Segment()
        data.set_flag([segment.ACK_FLAG])
        self.connection.send_data(data, self.server_addr)
        logger.log(f"[!] ACK stop sent to server {self.server_addr[0]}:{self.server_addr[1]}")
    
    def __send_ack_seq(self, i):
        data = Segment()
        data.set_flag([segment.ACK_FLAG])
        data.set_header({"seq_num": 0, "ack_num": i})
        self.connection.send_data(data, self.server_addr)
        logger.log(f"[!] ACK sent for seq {i} to server {self.server_addr[0]}:{self.server_addr[1]}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("<client_port>", type=int)
    parser.add_argument("<server_ip_address>", type=str)
    parser.add_argument("<broadcast_port>", type=int)
    parser.add_argument("<filepath>", type=str)
    args = vars(parser.parse_args())

    main = Client(args["<client_port>"], args["<server_ip_address>"], args["<broadcast_port>"], args["<filepath>"])
    main.three_way_handshake()
    main.listen_file_transfer()
