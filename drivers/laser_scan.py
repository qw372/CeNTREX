import numpy as np
import time
import logging
import socket
import struct
import configparser

class laser_scan:
    def __init__(self, time_offset, *constr_param):
        self.time_offset = time_offset
        self.laser_freq = [float(i) for i in constr_param[:2]]
        self.host = constr_param[2]
        self.port = int(constr_param[3])
        self.init_error = ""

        # shape and type of the array of returned data
        self.dtype = 'f'
        self.shape = (3, )

        # each element in self.warnings should be in format: [time.time()-self.time_offset, "warning content"]
        self.warnings = []

        # HDF attributes generated when constructor is run
        self.new_attributes = []

        # make use of the constr_param
        self.constr_param = constr_param
        print(f"Constructor got passed the following parameter: {self.constr_param}")

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect((self.host, self.port))
        except Exception as err:
            self.init_error = ["error", "TCP connection falied."]

    def __enter__(self):
        # when opened in the main file by with...as... statement, __enter__ will be called right after __init__
        return self

    def __exit__(self, *exc):
        # when with...as... statementn finished running, __exit__ will be called
        try:
            self.sock.close()
        except AttributeError:
            pass

    def ReadValue(self):
        # self.warnings.append([time.time()-self.time_offset, "warning test 2"])
        return [
                time.time()-self.time_offset,
                *self.laser_freq,
               ]

    def scan(self, type, val):
        if type == "laser0(MHz)":
            self.update_laser0_freq(val)
        elif type == "laser1(MHz)":
            self.update_laser1_freq(val)
        else:
            self.warnings.append([time.strftime("%H:%M:%S"), f"scan type not supported."])

    def update_laser0_freq(self, freq):
        try:
            self.laser_freq[0] = float(freq)
            bytearray = struct.pack('>H', 0)
            bytearray += struct.pack('>d', float(self.laser_freq[0]))
            self.sock.sendall(bytearray)
            re = self.sock.recv(1024)
        except Exception as err:
            self.warnings.append([time.strftime("%H:%M:%S"), f"laser0 scan {freq} failed. \n{err}"])

    def update_laser1_freq(self, freq):
        try:
            self.laser_freq[1] = float(freq)
            bytearray = struct.pack('>H', 1)
            bytearray += struct.pack('>d', float(self.laser_freq[1]))
            self.sock.sendall(bytearray)
            re = self.sock.recv(1024)
        except Exception as err:
            self.warnings.append([time.strftime("%H:%M:%S"), f"laser1 scan {freq} failed. \n{err}"])

    def return_laser0_freq(self):
        return "{:.1f}".format(self.laser_freq[0])

    def return_laser1_freq(self):
        return "{:.1f}".format(self.laser_freq[1])

    def GetWarnings(self):
        warnings = self.warnings
        self.warnings = []
        return warnings

# a = laser_scan(0, 100, 200)
# a.update_laser0_freq(200)
# a.__exit__()
