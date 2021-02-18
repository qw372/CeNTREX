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
        # each element in self.warnings should be in format: [time.strftime("%H:%M:%S"), "warning content"]
        self.warnings = []

        self.time_offset = time_offset
        self.constr_param = constr_param
        print(f"Constructor got passed the following parameter: {self.constr_param}")
        self.channel = self.constr_param[0]
        self.update_samp_rate(self.constr_param[1])
        self.update_samp_num(self.constr_param[2])
        self.update_settle_time(self.constr_param[3])
        self.laser_list = ["laser0", "laser1"]
        self.update_laser(self.constr_param[4])
        self.update_scan(self.constr_param[5])
        self.laser0 = self.constr_param[6]
        self.laser1 = self.constr_param[7]
        self.tcp_host = self.constr_param[8]
        self.tcp_port = int(self.constr_param[9])

        self.init_error = ""

        # HDF attributes generated when constructor is run
        self.new_attributes = []

        # shape and type of the array of returned data
        self.dtype = 'f'
        self.shape = (1, 2, -1)

        try:
            self.daq_init()
        except Exception as err:
            self.init_error = ["error", "DAQ initialization failed"]
            logging.error(err)
            logging.error(traceback.format_exc())

        try:
            self.task.close()
        except AttributeError:
            pass

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
        self.task.timing.cfg_samp_clk_timing(
                rate = self.samp_rate,
                sample_mode = nidaqmx.constants.AcquisitionType.FINITE,
                samps_per_chan = self.samp_num
            )

    def tcp_init(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.tcp_host, self.tcp_port))

    def ReadValue(self):
        if not self.scan_active:
            data = np.array([[[0], [0]]])
            attr = {"state": "scan disabled"}
            return [data, [attr]]

        lasernum = 1 if self.laser == "laser1" else 0
        l = self.laser1 if self.laser == "laser1" else self.laser0
        l_seq = np.linspace(float(l["start freq."]), float(l["end freq."]), int(l["npoints"]))
        l_seq = np.append(l_seq, l_seq[::-1]) # append reverse array
        pd = []

        for f in l_seq:
            try:
                bytearray = struct.pack('>H', lasernum) # the first 2 bytes are laser number: 0 or 1
                bytearray += struct.pack('>d', f) # the rest 8 bytes are laser frequency
                self.sock.sendall(bytearray)
                re = self.sock.recv(1024)
            except Exception as err:
                self.warnings.append([time.strftime("%H:%M:%S"), f"laser {lasernum} freq. TCP failed.\n"+str(err)])

            time.sleep(self.settle_time)

            try:
                self.daq_init()
                self.task.start()
                r_list = self.task.read(number_of_samples_per_channel=self.samp_num, timeout=10)
                r = np.mean(r_list)
            except Exception as err:
                self.warnings.append([time.strftime("%H:%M:%S"), f"laser {lasernum} DAQ ai reading failed.\n"+str(err)])
                r = np.NaN

            try:
                self.task.close()
            except AttributeError:
                pass

            pd.append(r)

        pd = np.array(pd).reshape((2, -1))
        pd = np.array([pd[0], pd[1][::-1]])
        pd = np.mean(pd, axis=0)
        l_seq = l_seq.reshape((2, -1))
        data = np.append(l_seq[0], pd)
        data = np.array(data).reshape((1, 2, -1))
        attr = {"laser": self.laser, "scan start": l["start freq."], "scan end": l["end freq."], "npoints": l["npoints"]}
        return [data, [attr]]

    def update_channel(self, arg):
        old_ch = self.channel
        self.channel = arg
        try:
            self.daq_init()
        except Exception as err:
            self.channel = old_ch
            self.warnings.append([time.strftime("%H:%M:%S"), f"failed to update ai channel, currrent channel: {self.channel}. "+str(err)])

        try:
            self.task.close()
        except AttributeError:
            pass

    def update_samp_rate(self, arg):
        try:
            self.samp_rate = round(float(arg)*1000)
            if self.samp_rate < 1000:
                self.samp_rate = 1000
                raise ValueError("sampling rate less than 1 kS/s")
        except Exception as err:
            self.warnings.append([time.strftime("%H:%M:%S"), f"failed to update samp rate, currrent sampling rate: {self.samp_rate} S/s. "+str(err)])

    def update_samp_num(self, arg):
        try:
            self.samp_num = int(arg)
            if self.samp_num < 10:
                self.samp_rate = 10
                raise ValueError("# of samples less than 10")
        except Exception as err:
            self.warnings.append([time.strftime("%H:%M:%S"), f"failed to update samp num, currrent # of samples: {self.samp_num}. "+str(err)])

    def update_settle_time(self, arg):
        try:
            self.settle_time = float(arg)
            if self.settle_time < 0.05:
                self.settle_time = 0.05
                raise ValueError("settle time less than 0.05 s")
        except Exception as err:
            self.warnings.append([time.strftime("%H:%M:%S"), f"failed to update settling time, currrent settling time: {self.settle_time}. "+str(err)])

    def update_laser(self, arg):
        if arg in self.laser_list:
            self.laser = arg
        else:
            self.warnings.append([time.strftime("%H:%M:%S"), f"{arg} not found in laser list, current laser {self.laser}. "])

    def update_scan(self, arg):
        try:
            self.scan_active = bool(int(arg))
        except Exception as err:
            self.warnings.append([time.strftime("%H:%M:%S"), f"Can't change scan state.\n"+str(err)])

    def update_laser0(self, i, arg):
        try:
            if str(i) == "0":
                f = float(arg)
                if (f < 0) or (f > 500):
                    f = np.clip(f, 0, 500)
                    self.warnings.append([time.strftime("%H:%M:%S"), f"laser0: freq setting out of range"])
                self.laser0["start freq."] = f
            elif str(i) == "1":
                f = float(arg)
                if (f < 0) or (f > 500):
                    f = np.clip(f, 0, 500)
                    self.warnings.append([time.strftime("%H:%M:%S"), f"laser0: freq setting out of range"])
                self.laser0["end freq."] = f
            elif str(i) == "2":
                self.laser0["npoints"] = int(arg)
            else:
                self.warnings.append([time.strftime("%H:%M:%S"), f"laser0: parameter index {i} doesn't exist"])
        except Exception as err:
            self.warnings.append([time.strftime("%H:%M:%S"), f"failed to convert laser0 setting, currrent setting: {self.laser0}. "+str(err)])

    def update_laser1(self, i, arg):
        try:
            if str(i) == "0":
                f = float(arg)
                if (f < 0) or (f > 500):
                    f = np.clip(f, 0, 500)
                    self.warnings.append([time.strftime("%H:%M:%S"), f"laser1: freq setting out of range"])
                self.laser0["start freq."] = f
            elif str(i) == "1":
                f = float(arg)
                if (f < 0) or (f > 500):
                    f = np.clip(f, 0, 500)
                    self.warnings.append([time.strftime("%H:%M:%S"), f"laser0: freq setting out of range"])
                self.laser0["end freq."] = f
            elif str(i) == "2":
                self.laser0["npoints"] = int(arg)
            else:
                self.warnings.append([time.strftime("%H:%M:%S"), f"laser1: parameter index {i} doesn't exist"])
        except Exception as err:
            self.warnings.append([time.strftime("%H:%M:%S"), f"failed to convert laser1 setting, currrent setting: {self.laser1}. "+str(err)])

    def scan(self, type, val):
        self.warnings.append([time.strftime("%H:%M:%S"), f"scan function not implemented."])

    def GetWarnings(self):
        warnings = self.warnings
        self.warnings = []
        return warnings

# l0 = {"start freq.": "270", "end freq.": "430", "npoints": "50"}
# l1 = {"start freq.": "100", "end freq.": "30", "npoints": "60"}
# with absorption(time.time(), "Dev3/ai3", "100", "50000", "0.3", "laser0", l0, l1, "127.0.0.1", "65534") as ab:
#     data, attr = ab.ReadValue()
#     plt.plot(data[0][0], data[0][1], "ro")
#     plt.show()
