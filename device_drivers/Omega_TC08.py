import numpy as np
import time
import logging
import ctypes
import traceback
from picosdk.usbtc08 import usbtc08 as tc08
from picosdk.functions import assert_pico2000_ok

class Omega_TC08:
    def __init__(self, time_offset, *constr_param):
        self.time_offset = time_offset
        self.chan_num = [1,2,3,4,8]

        # self.init_error = ["warning", "test"]
        self.init_error = ""

        # HDF attributes generated when constructor is run
        self.new_attributes = []

        # shape and type of the array of returned data
        self.dtype = 'f'
        self.shape = (len(self.chan_num)+1, )

        # each element in self.warnings should be in format: [time.time()-self.time_offset, "warning content"]
        self.warnings = []

        # make use of the constr_param
        self.constr_param = constr_param
        print(f"Constructor got passed the following parameter: {self.constr_param}")

        # Create chandle and status ready for use
        self.chandle = ctypes.c_int16()
        self.status = {}

        # https://github.com/picotech/picosdk-python-wrappers/blob/master/usbtc08Examples/tc08SingleModeExample.py
        # open unit
        try:
            self.status["open_unit"] = tc08.usb_tc08_open_unit()
            assert_pico2000_ok(self.status["open_unit"])
            self.chandle = self.status["open_unit"]

            # set mains rejection to 60 Hz
            self.status["set_mains"] = tc08.usb_tc08_set_mains(self.chandle,1)
            assert_pico2000_ok(self.status["set_mains"])

            # set up channel
            # therocouples types and int8 equivalent
            # B=66 , E=69 , J=74 , K=75 , N=78 , R=82 , S=83 , T=84 , ' '=32 , X=88
            typeK = ctypes.c_int8(75)
            for i in self.chan_num:
                self.status["set_channel"] = tc08.usb_tc08_set_channel(self.chandle, i, typeK)
                assert_pico2000_ok(self.status["set_channel"])

            # get minimum sampling interval in ms
            self.status["get_minimum_interval_ms"] = tc08.usb_tc08_get_minimum_interval_ms(self.chandle)
            assert_pico2000_ok(self.status["get_minimum_interval_ms"])

        except Exception as err:
            self.init_error = ["error", "Omega USB TC-08 initialization failed."]
            logging.error(err)
            logging.error(traceback.format_exc())

        self.ReadValue()

    def __enter__(self):
        # when opened in the main file by with...as... statement, __enter__ will be called right after __init__
        return self

    def __exit__(self, *exc):
        # when with...as... statementn finished running, __exit__ will be called
        try:
            self.status["close_unit"] = tc08.usb_tc08_close_unit(self.chandle)
            assert_pico2000_ok(self.status["close_unit"])
        except Exception as err:
            logging.error(err)
            logging.error(traceback.format_exc())


    def ReadValue(self):
        # get single temperature reading
        try:
            self.temp = (ctypes.c_float * 9)() # there is one cold junction reading and 8 channels' readings
            overflow = ctypes.c_int16(0)
            units = tc08.USBTC08_UNITS["USBTC08_UNITS_CENTIGRADE"]
            self.status["get_single"] = tc08.usb_tc08_get_single(self.chandle,ctypes.byref(self.temp), ctypes.byref(overflow), units)
            assert_pico2000_ok(self.status["get_single"])
        except Exception as err:
            self.warnings.append([time.strftime("%H:%M:%S"), f"Omega USB TC-08 Read value function failed \n"+str(err)])
            return [time.time()-self.time_offset, np.NaN, np.NaN, np.NaN, np.NaN, np.NaN]

        return [
                time.time()-self.time_offset,
                *[self.temp[i] for i in self.chan_num]
               ]

    def return_value(self, ch):
        t = self.temp[ch] # temp[0] is cold conjuction temp
        if np.isnan(t):
            return ["NaN", "error"]
        elif t >= 100:
            return ["{:.2f} (Temperature too high)".format(t), "error"]
        elif t <= 5:
            return ["{:.2f} (Temperature too low)".format(t), "error"]
        else:
            return ["{:.2f}".format(t), "normal"]

    def return_ch1(self):
        return self.return_value(1)

    def return_ch2(self):
        return self.return_value(2)

    def return_ch3(self):
        return self.return_value(3)

    def return_ch4(self):
        return self.return_value(4)

    def return_ch8(self):
        return self.return_value(8)

    def scan(self, type, val):
        self.warnings.append([time.strftime("%H:%M:%S"), f"scan function not implemented in Omega USB TC-08."])

    def GetWarnings(self):
        warnings = self.warnings
        self.warnings = []
        return warnings

# with Omega_TC08(0, 0) as obj:
#     print(obj.ReadValue())
#     print(obj.GetWarnings())
