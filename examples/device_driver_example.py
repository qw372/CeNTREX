import numpy as np
import time
import logging

class test_slowdata:
    def __init__(self, time_offset, constr_param):
        self.time_offset = time_offset

        # make the verification string
        self.verification_string = "the test string"

        # HDF attributes generated when constructor is run
        self.new_attributes = []

        # shape and type of the array of returned data
        # it's only required for double_connect_dev
        self.dtype = 'f'
        self.shape = (2, )

        # each element in self.warnings should be in format: [time.time()-self.time_offset, "warning content"]
        self.warnings = []

        # make use of the constr_param,
        # constr_param is a list, including values from someParam1 and someParam2
        self.constr_param = constr_param
        print(f"Constructor got passed the following parameter: {self.constr_param}")

    def __enter__(self):
        # when opened in the main file by with...as... statement, __enter__ will be called right after __init__
        return self

    def __exit__(self, *exc):
        # when with...as... statementn finished running, __exit__ will be called
        pass

    # a must-have function for devices that can return data
    def ReadValue(self):
        # self.warnings.append([time.time()-self.time_offset, "warning test 2"])
        return [
                time.time()-self.time_offset,
                np.random.random_sample(),
               ]

    # a must-function for devices that want to be scanned
    def scan(self, type, val):
        if type == "p1(unit1)":
            pass
        elif type == "p2(unit2)":
            pass
        else:
            print("Sequencer: scan type not supported")

    def GetWarnings(self):
        warnings = self.warnings
        self.warnings = []
        return warnings

    def update_someParam1(self, arg):
        pass

    def update_someParam2(self, arg):
        pass
