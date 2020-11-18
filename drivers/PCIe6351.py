import numpy as np
import time
import logging
import nidaqmx

class PCIe6351:
    def __init__(self, time_offset, constr_param1):
        self.time_offset = time_offset

        # make the verification string
        self.verification_string = "nomisspoints"

        # HDF attributes generated when constructor is run
        self.new_attributes = []

        # shape and type of the array of returned data
        self.dtype = 'f'
        self.shape = (1, 2, 1000)

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
        with nidaqmx.Task() as task:
            task.ai_channels.add_ai_voltage_chan("Dev1/ai0")
            d = task.read()
        # a = np.linspace(0,199,200) + (np.random.random_sample(200)*10-5)
        # b = {"info": "test", "info2": "test2"}
        # return [
        #         a.reshape(self.shape), [b]
        #        ]
        return d

    def GetWarnings(self):
        warnings = self.warnings
        self.warnings = []
        return warnings
