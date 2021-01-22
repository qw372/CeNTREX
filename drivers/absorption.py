import numpy as np
import time
import logging
import traceback
import nidaqmx
import socket
import struct
import matplotlib.pyplot as plt

class absorption:
    def __init__(self, time_offset, *constr_param):
        self.time_offset = time_offset
        self.constr_param = constr_param
        self.channel = self.constr_param[0]
        self.laser = self.constr_param[1]
        self.laser_list = ["laser0", "laser1"]
        self.laser0 = self.constr_param[2]
        self.laser1 = self.constr_param[3]
        self.tcp_host = self.constr_param[4]
        self.tcp_port = int(self.constr_param[5])
        print(f"Constructor got passed the following parameter: {self.constr_param}")

        self.init_error = ""

        # HDF attributes generated when constructor is run
        self.new_attributes = []

        # shape and type of the array of returned data
        self.dtype = 'f'
        self.shape = (1, 2, int(self.laser1["npoints"]) if self.laser == "laser1" else int(self.laser0["npoints"]))

        # each element in self.warnings should be in format: [time.time()-self.time_offset, "warning content"]
        self.warnings = []

        try:
            self.daq_init()
        except Exception as err:
            self.init_error = ["error", "DAQ initialization failed"]
            logging.error(err)
            logging.error(traceback.format_exc())

        try:
            self.tcp_init()
        except Exception as err:
            if self.init_error:
                self.init_error = ["error", "DAQ and TCP initialization failed"]
            else:
                self.init_error = ["error", "TCP initialization failed"]
            logging.error(err)
            logging.error(traceback.format_exc())

    def __enter__(self):
        # when opened in the main file by with...as... statement, __enter__ will be called right after __init__
        return self

    def __exit__(self, *exc):
        # when with...as... statementn finished running, __exit__ will be called
        try:
            self.task.close()
        except AttributeError:
            pass

        try:
            self.sock.close()
        except AttributeError:
            pass

    def daq_init(self):
        self.task = nidaqmx.Task()
        self.task.ai_channels.add_ai_voltage_chan(
                self.channel,
                min_val=-1,
                max_val=2,
                units=nidaqmx.constants.VoltageUnits.VOLTS
            )

    def tcp_init(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.tcp_host, self.tcp_port))

    def ReadValue(self):
        lasernum = 1 if self.laser == "laser1" else 0
        l = self.laser1 if self.laser == "laser1" else self.laser0
        l_seq = np.linspace(float(l["start freq."]), float(l["end freq."]), int(l["npoints"]))
        pd = []
        for f in l_seq:
            try:
                bytearray = struct.pack('>H', lasernum) # the first 2 bytes are laser number: 0 or 1
                bytearray += struct.pack('>d', f) # the rest 8 bytes are laser frequency
                self.sock.sendall(bytearray)
                re = self.sock.recv(1024)
            except Exception as err:
                self.warnings.append([time.time()-self.time_offset, f"laser {lasernum} freq. TCP failed.\n"+str(err)])

            time.sleep(0.1)

            try:
                r = self.task.read(number_of_samples_per_channel=1)
            except Exception as err:
                self.warnings.append([time.time()-self.time_offset, f"laser {lasernum} DAQ ai reading failed.\n"+str(err)])
                r = np.NaN
            pd.append(r)

        data = np.append(l_seq, np.array(pd))
        data = np.array(data).reshape((1, 2, -1))
        attr = {"laser": self.laser, "scan start": l["start freq."], "scan end": l["end freq."], "npoints": l["npoints"]}
        return [data, [attr]]

    def update_channel(self, arg):
        old_ch = self.channel
        self.channel = arg
        try:
            self.task.close()
        except AttributeError:
            pass

        try:
            self.daq_init()
        except Exception as err:
            self.channel = old_ch
            self.warnings.append([time.time()-self.time_offset, f"failed to update ai channel, currrent channel: {self.channel}"])

    def update_laser(self, arg):
        if arg in self.laser_list:
            self.laser = arg
        else:
            self.warnings.append([time.time()-self.time_offset, f"{arg} not found in laser list, current laser {self.laser}"])

    def update_laser0(self, i, arg):
        try:
            if i == "0":
                self.laser0["start freq."] = float(arg)
            elif i == "1":
                self.laser0["end freq."] = float(arg)
            elif i == "2":
                self.laser0["npoints"] = int(arg)
            else:
                self.warnings.append([time.time()-self.time_offset, f"laser0: parameter index {i} doesn't exist"])
        except ValueError as err:
            self.warnings.append([time.time()-self.time_offset, f"failed to convert laser0 setting, currrent setting: {self.laser0}"])

    def update_laser1(self, i, arg):
        try:
            if i == "0":
                self.laser0["start freq."] = float(arg)
            elif i == "1":
                self.laser0["end freq."] = float(arg)
            elif i == "2":
                self.laser0["npoints"] = int(arg)
            else:
                self.warnings.append([time.time()-self.time_offset, f"laser1: parameter index {i} doesn't exist"])
        except ValueError as err:
            self.warnings.append([time.time()-self.time_offset, f"failed to convert laser1 setting, currrent setting: {self.laser1}"])

    def GetWarnings(self):
        warnings = self.warnings
        self.warnings = []
        return warnings

l0 = {"start freq.": "150", "end freq.": "350", "npoints": "50"}
l1 = {"start freq.": "100", "end freq.": "30", "npoints": "60"}
with absorption(time.time(), "Dev2/ai3", "laser0", l0, l1, "127.0.0.1", "65534") as ab:
    data, attr = ab.ReadValue()
    plt.plot(data[0])
    plt.show()
