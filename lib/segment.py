import struct
import copy

# Constants
SYN_FLAG = 0b00010
ACK_FLAG = 0b10000
FIN_FLAG = 0b00001


class SegmentFlag:
    def __init__(self, flag: int = None):
        # Init flag variable from flag byte
        if flag is not None:
            self._flags = {
                "syn": flag & SYN_FLAG,
                "ack": flag & ACK_FLAG,
                "fin": flag & FIN_FLAG
            }
        else:
            self._flags = {
                "syn": 0,
                "ack": 0,
                "fin": 0
            }

    def get_flag_int(self) -> int:
        # Convert this object to flag in byte form
        flag = self._flags["syn"] | self._flags["ack"] | self._flags["fin"]
        return flag

    def get_flag(self) -> dict:
        return self._flags


class Segment:
    # -- Internal Function --
    def __init__(self):
        # Initalize segment
        self._seq_num = 0
        self._ack_num = 0
        self._flag = SegmentFlag()
        self._checksum = 0
        self._payload = b""

    def __str__(self):
        # Optional, override this method for easier print(segmentA)
        output = ""
        output += f"SEQ: {self._seq_num}\n"
        output += f"ACK: {self._ack_num}\n"
        output += f"FLG: {self._flag.get_flag_int()}\n"
        output += f"CHK: {self._checksum}\n"
        output += f"DAT: {self._payload}\n"
        return output

    def __calculate_checksum(self) -> (bytes, int):
        # Calculate checksum here, return the data and the checksum result

        # TODO: change ACK_FLAG
        dummy_checksum = 0
        data = struct.pack("!IIBxH", self._seq_num, self._ack_num,
                           self._flag.get_flag_int(), dummy_checksum)
        data += self._payload

        # fletcher-16
        c0 = 0
        c1 = 0
        i = 0

        while i < len(data):
            c0 = (c0 + data[i]) % 0xFF
            c1 = (c1 + c0) % 0xFF
            i += 1

        checksum = (c1 << 8) | c0

        return (data, checksum)

    # -- Setter --

    def set_header(self, header: dict):
        self._seq_num = header["seq_num"]
        self._ack_num = header["ack_num"]

    def set_payload(self, payload: bytes):
        self._payload = self.__copy_payload(payload)

    def __copy_payload(self, payload):
        p1 = bytearray(copy.deepcopy(payload))
        p2 = bytearray(copy.deepcopy(payload))
        p3 = bytearray(copy.deepcopy(payload))

        return bytes(p1 + p2 + p3)

    def set_flag(self, flag_list: list):
        flags = 0b0
        for flag in flag_list:
            flags = flags | flag
        self._flag = SegmentFlag(flags)

    # -- Getter --

    def get_flag(self) -> dict:
        return self._flag.get_flag()

    def get_header(self) -> dict:
        return {
            "ack_num": self._ack_num,
            "seq_num": self._seq_num,
            "flag": self._flag.get_flag_int()
        }

    def get_payload(self) -> bytes:
        arr = bytearray(self._payload)
        return bytes(arr[:len(arr)//3])
    
    def error_correction(self):
        self._payload = self.__error_correcting(self._payload)

    def __error_correcting(self, payload):
        arrcontent = bytearray(payload)
        ln = len(arrcontent)

        c1 = arrcontent[:ln//3]
        c2 = arrcontent[ln//3:ln//3*2]
        c3 = arrcontent[ln//3*2:]

        return self.__correcting(c1, c2, c3)

    def __correcting(self, c1, c2, c3):
        arrc1 = bytearray(c1)
        arrc2 = bytearray(c2)
        arrc3 = bytearray(c3)

        res = bytearray()
        ln = min(len(arrc1), len(arrc2), len(arrc3))
        for i in range(ln):
            if arrc1[i] == arrc2[i]:
                res.append(arrc1[i])
            elif arrc1[i] == arrc3[i]:
                res.append(arrc1[i])
            elif arrc2[i] == arrc3[i]:
                res.append(arrc2[i])
            else:
                res.append(arrc1[i])

        return self.__copy_payload(bytes(res))


    # -- Marshalling --

    def set_from_bytes(self, src: bytes):
        # From pure bytes, unpack() and set into python variable
        # I: unsigned int; B: unsigned char; H: unsigned short; x: padding
        payload_length = len(src) - 12

        unpacked = struct.unpack(f"!IIBxH{payload_length}s", src)

        self._seq_num = unpacked[0]
        self._ack_num = unpacked[1]
        self._flag = SegmentFlag(unpacked[2])

        self._checksum = unpacked[3]
        self._payload = unpacked[4]

    def get_bytes(self) -> bytes:
        # Convert this object to pure bytes
        data, checksum = self.__calculate_checksum()
        data = data[:10] + int.to_bytes(checksum, 2, "big") + data[12:]

        return data

    # -- Checksum --

    def valid_checksum(self) -> bool:
        # Use __calculate_checksum() and check integrity of this object
        _, checksum = self.__calculate_checksum()

        valid = (checksum == self._checksum)
        if not valid:
            self.error_correction()
            _, checksum = self.__calculate_checksum()
            valid = (checksum == self._checksum)
        
        return valid


# testing
if __name__ == '__main__':
    payload = "😭💀🗿"

    s1 = Segment()

    # setter
    s1.set_header({"seq_num": 3000, "ack_num": 35000})
    s1.set_payload(bytes(payload, "utf-8"))
    s1.set_flag([SYN_FLAG, ACK_FLAG, FIN_FLAG])

    # getter
    print("--- GETTER ---")
    print("s1 flag:", s1.get_flag())
    print("s1 head:", s1.get_header())
    print("s1 data:", s1.get_payload())
    print("s1 byte:", s1.get_bytes())

    # copy instance
    print("\n--- S2 ---")
    s2 = Segment()
    s2.set_from_bytes(s1.get_bytes())
    print("s2 valid?", s2.valid_checksum())
    print("s2 checksum:", s2._checksum)
    print("s2 flag:", s2.get_flag())
    print("s2 head:", s2.get_header())
    print("s2 data:", s2.get_payload())
    print("s2 byte:", s2.get_bytes())
    print("s2 len :", len(s2.get_bytes()))
    print("-- modify s2 data --")
    s2_bytes = s2.get_bytes()
    print(s2_bytes[13])
    s2_bytes = s2_bytes[:13] + b"\x99" + s2_bytes[14:]
    s2.set_from_bytes(s2_bytes)
    print("s2 len :", len(s2.get_bytes()))
    print("s2 valid?", s2.valid_checksum())
    print("s2 byte:", s2.get_bytes())
