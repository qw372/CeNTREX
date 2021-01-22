import numpy as np
import time
import logging
import traceback
import nidaqmx


class dispenser:
    def __init__(self, time_offset, *constr_param):
        self.time_offset = time_offset
        self.constr_param = constr_param
        self.channel = self.constr_param[0]
        self.Kepco_setting = float(self.constr_param[1])
        self.heat = int(self.constr_param[2])
        print(f"Constructor got passed the following parameter: {self.constr_param}")

        self.init_error = ""

        # HDF attributes generated when constructor is run
        self.new_attributes = []

        # shape and type of the array of returned data
        self.dtype = 'f'
        self.shape = (2,)

        # each element in self.warnings should be in format: [time.time()-self.time_offset, "warning content"]
        self.warnings = []

        try:
            self.daq_init()
        except Exception as err:
            self.init_error = ["error", "DAQ initialization failed"]
            logging.error(err)
            logging.error(traceback.format_exc())

    def __enter__(self):
        # when opened in the main file by with...as... statement, __enter__ will be called right after __init__
        return self

    def __exit__(self, *exc):
        # when with...as... statementn finished running, __exit__ will be called
        try:
            self.task.close()
        except AttributeError:
            pass

    def daq_init(self):
        self.task = nidaqmx.Task()
        self.task.ao_channels.add_ao_voltage_chan(
                self.channel,
                min_val=0,
                max_val=1,
                units=nidaqmx.constants.VoltageUnits.VOLTS
            )

    def ReadValue(self):
        w = self.Kepco_setting if self.heat else 0
        try:
            self.task.write(self.Kepco_setting)
            return [time.time()-self.time_offset, w]
        except Exception as err:
            self.warnings.append([time.time()-self.time_offset, "dispenser writing failed"])
            return [time.time()-self.time_offset, np.NaN]

    def update_channel(self, arg):
        old_ch = self.channel
        self.channel = arg
        try:
            self.task.close()
        except AttributeError:
            pass

        try:
            self.daq_init()
        except Exception as err:
            self.channel = old_ch
            self.warnings.append([time.time()-self.time_offset, f"failed to update ao channel, currrent channel: {self.channel}"])

    def update_heat(self, arg):
        self.heat = int(arg)

    def update_Kepco(self, arg):
        try:
            k = float(arg)
        except ValueError as err:
            self.warnings.append([time.time()-self.time_offset, f"failed to convert Kepco setting, currrent setting: {self.Kepco_setting}"])
            return

        self.Kepco_setting = k

    def GetWarnings(self):
        warnings = self.warnings
        self.warnings = []
        return warnings

# with dispenser(0, "Dev2/ao3", 0.35, 2) as d:
#     for i in range(500):
#         print(d.ReadValue())
