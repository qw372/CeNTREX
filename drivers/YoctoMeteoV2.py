import numpy as np
import time
import logging
import pyvisa
import traceback

class YoctoMeteoV2:
    def __init__(self, time_offset, *constr_param1):
        # make use of the constr_param1
        self.constr_param1 = list(constr_param1)
        print(f"Constructor got passed the following parameter: {self.constr_param1}")

        self.time_offset = time_offset

        self.verification_string = "globalwarming"

        # HDF attributes generated when constructor is run
        self.new_attributes = []

        # shape and type of the array of returned data
        self.dtype = 'f'
        self.shape = (5, )

        self.warnings = []

    def __enter__(self):
        # when opened in the main file by with...as... statement, __enter__ will be called right after __init__
        return self

    def __exit__(self, *exc):
        # when with...as... statementn finished running, __exit__ will be called
        pass

    def ReadValue(self):

        return [
                time.time()-self.time_offset,
                np.sin(time.time()-self.time_offset),
                2*np.sin(time.time()-self.time_offset),
                4*np.sin(time.time()-self.time_offset),
                8*np.sin(time.time()-self.time_offset),
               ]

    def return_temp(self):
        if np.sin(time.time()-self.time_offset) > 0:
            return ["20", "normal"]
        else:
            return ["-20 (WARNING!)", "error"]

    def return_humid(self):
        return ["30", "normal"]

    def return_dewpoint(self):
        return ["10", "normal"]

    def return_pressure(self):
        return ["1024", "normal"]

    def update_tempsetpoint(self, arg):
        return arg

    def update_mintemp(self, arg):
        return arg

    def GetWarnings(self):
        warnings = self.warnings
        self.warnings = []
        return warnings
