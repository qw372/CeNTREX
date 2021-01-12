import numpy as np
import time
import logging
import socket
import struct

class laser_scan:
    def __init__(self, time_offset, *constr_param):
        self.time_offset = time_offset
        self.laser_freq = [float(i) for i in constr_param]
        self.verification_string = "laser"

        # shape and type of the array of returned data
        self.dtype = 'f'
        self.shape = (3, )

        # each element in self.warnings should be in format: [time.time()-self.time_offset, "warning content"]
        self.warnings = []

        # make use of the constr_param
        self.constr_param = constr_param
        print(f"Constructor got passed the following parameter: {self.constr_param}")

        server_addr = configparser.ConfigParser()
        server_addr.read(r"C:\Users\DeMille Group\github\SrF-lab-control-accessory\Lasers\server_address.ini")
        self.host = server_addr["Server address"]["host"].strip()
        self.port = float(server_addr["Server address"]["port"])

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect((self.host, self.port))
            self.verification_string = "laser"
        except Exception as err:
            print("laser scan: TCP connection failed.")
            self.verification_string = "fail"

    def __enter__(self):
        # when opened in the main file by with...as... statement, __enter__ will be called right after __init__
        return self

    def __exit__(self, *exc):
        # when with...as... statementn finished running, __exit__ will be called
        pass

    def ReadValue(self):
        # self.warnings.append([time.time()-self.time_offset, "warning test 2"])
        return [
                time.time()-self.time_offset,
                *self.laser_freq,
               ]

    def scan(self, type, val):
        if type = "laser0(MHZ)":
            self.update_laser0_freq(val)
        elif type = "laser1(MHZ)":
            self.update_laser1_freq(val)
        else:
            print("laser scan: scan type not supported.")

    def update_laser0_freq(self, freq):
        self.laser_freq[0] = float(freq)
        bytearray = struct.pack('>H', 0)
        bytearray += struct.pack('>d', float(self.laser_freq[0]))
        self.sock.sendall(bytearray)
        re = self.sock.recv(1024)

    def update_laser1_freq(self, freq):
        self.laser_freq[1] = float(freq)
        bytearray = struct.pack('>H', 1)
        bytearray += struct.pack('>d', float(self.laser_freq[1]))
        self.sock.sendall(bytearray)
        re = self.sock.recv(1024)

    def GetWarnings(self):
        warnings = self.warnings
        self.warnings = []
        return warnings
