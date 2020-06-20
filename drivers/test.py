import pyvisa
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

        self.warnings = []

        # make use of the constr_param1
        print(f"Constructor got passed the following parameter: {constr_param1}")

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        pass

    def ReadValue(self):
        return [ 
                time.time()-self.time_offset,
                np.random.randint(100),
               ]

    def GetWarnings(self):
        warnings = self.warnings
        self.warnings = []
        return warnings

    def beep(self):
        print("Beeping!")

    def takeinput(self, param):
        print(f"Received the parameter: {param}")
