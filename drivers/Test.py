import numpy as np
import time
import logging

class Test:
    def __init__(self, time_offset, constr_param1):
        self.time_offset = time_offset

        # make the verification string
        self.verification_string = "the test string"

        # HDF attributes generated when constructor is run
        self.new_attributes = []

        # shape and type of the array of returned data
        self.dtype = 'f'
        self.shape = (2, )

        # each element in self.warnings should be in format: [time.time()-self.time_offset, "warning content"]
        self.warnings = []

        # make use of the constr_param1
        self.constr_param1 = constr_param1
        print(f"Constructor got passed the following parameter: {self.constr_param1}")

    def __enter__(self):
        # when opened in the main file by with...as... statement, __enter__ will be called right after __init__
        return self

    def __exit__(self, *exc):
        # when with...as... statementn finished running, __exit__ will be called
        pass

    def ReadValue(self):
        self.warnings.append([time.time()-self.time_offset, "warning test 2"])
        return [
                time.time()-self.time_offset,
                np.sin((time.time()-self.time_offset)/2.0),
               ]

    def GetWarnings(self):
        warnings = self.warnings
        self.warnings = []
        return warnings

    def beep(self):
        print("Beeping ({self.constr_param1})!")

    def takeinput(self, param):
        print(f"Received the parameter: {self.constr_param1}.{param}")

    def wait_seconds(self, dt):
        print(f"Gonna sleep for {dt} seconds.")
        time.sleep(dt)
