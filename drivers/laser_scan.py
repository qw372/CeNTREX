import numpy as np
import time
import logging

class laser_scan:
    def __init__(self, time_offset, *constr_param):
        self.time_offset = time_offset
        self.laser_freq = [float(i) for i in constr_param]
        self.verification_string = "laser"

        # shape and type of the array of returned data
        self.dtype = 'f'
        self.shape = (2, )

        # each element in self.warnings should be in format: [time.time()-self.time_offset, "warning content"]
        self.warnings = []

        # make use of the constr_param
        self.constr_param = constr_param
        print(f"Constructor got passed the following parameter: {self.constr_param}")

        server_addr = configparser.ConfigParser()
        server_addr.read(r"C:\Users\DeMille Group\github\SrF-lab-control-accessory\ngs.ini")
        self.sender_email = email_settings["sender"]["email_addr"].strip()
        self.receiver_email = [x.strip() for x in email_settings["receiver"]["email_addr"].split(",")]

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
