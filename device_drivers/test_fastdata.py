import numpy as np
import time
import logging

class test_fastdata:
    def __init__(self, time_offset, *constr_param):
        self.time_offset = time_offset

        self.init_error = ""

        # HDF attributes generated when constructor is run
        self.new_attributes = []

        # shape and type of the array of returned data
        self.dtype = 'f'
        self.shape = (1, 2, 100)
        # 3 dimemsions in self.shape: # of records, # of channels, # of samples in each record from each channel
        # the 2nd dimension (# of channels) also correspond to # of column_names in devices .ini file

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
        # a (the 1st returned element) has to be a 3-dim np array, corresponding to self.shape
        # b (the 2nd return element) has to be a 1-dim list of dict, each dict will be the attrbute of a dset in .hdf file
        a = np.linspace(0,199,200) + (np.random.random_sample(200)*10-5)
        b = {"info": "test", "info2": "test2"}
        return [
                a.reshape(self.shape), [b]
               ]

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
