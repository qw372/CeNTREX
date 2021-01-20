import numpy as np
import time
import logging

class test_slowdata:
    def __init__(self, time_offset, *constr_param):
        self.time_offset = time_offset

        self.init_error = ["warning", "test"]

        # HDF attributes generated when constructor is run
        self.new_attributes = []

        # shape and type of the array of returned data
        self.dtype = 'f'
        self.shape = (2, )

        # each element in self.warnings should be in format: [time.time()-self.time_offset, "warning content"]
        self.warnings = []

        # make use of the constr_param
        self.constr_param = constr_param
        print(f"Constructor got passed the following parameter: {self.constr_param}")

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
                np.sin((time.time()-self.time_offset)/2.0),
               ]
    def scan(self, type, val):
        print(f"{type}, {val}")

    def GetWarnings(self):
        warnings = self.warnings
        self.warnings = []
        return warnings

    def beep(self):
        print("Beeping ({self.constr_param})!")

    def takeinput(self, param):
        print(f"Received the parameter: {self.constr_param}.{param}")

    def wait_seconds(self, dt):
        print(f"Gonna sleep for {dt} seconds.")
        time.sleep(dt)
