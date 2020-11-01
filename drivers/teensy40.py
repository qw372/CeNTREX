import numpy as np
import time
import logging

class teensy40:
    def __init__(self, time_offset, constr_param1):
        self.time_offset = time_offset

        # make the verification string
        self.verification_string = "zzzzzz"

        # HDF attributes generated when constructor is run
        self.new_attributes = []

        # shape and type of the array of returned data
        self.dtype = 'f'
        self.shape = (2, )

        self.warnings = []

        # make use of the constr_param1
        self.constr_param1 = float(constr_param1)
        print(f"Constructor got passed the following parameter: {self.constr_param1}")

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        pass

    def ReadValue(self):
        return [
                time.time()-self.time_offset,
                self.constr_param1 * np.sin((time.time()-self.time_offset)/2.0),
               ]
    def update_constr_param1(self, arg):
        self.constr_param1 = float(arg)

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
