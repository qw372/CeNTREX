import numpy as np
import time
import logging
import traceback
import nidaqmx
import matplotlib.pyplot as plt


class PCIe6351_ai:
    def __init__(self, time_offset, *constr_param):
        self.time_offset = time_offset
        self.constr_param = constr_param
        self.channel = self.constr_param[0]
        self.trig_channel = self.constr_param[1]
        self.samp_rate = round(float(self.constr_param[2])*1000)
        self.samp_num = int(self.constr_param[3])
        print(f"Constructor got passed the following parameter: {self.constr_param}")

        try:
            self.daq_init()
        except Exception as err:
            self.verification_string = "failed"
            print(err)
            logging.error(traceback.format_exc())
            self.task.close()
            return

        # make the verification string
        self.verification_string = "nomisspoints"

        # HDF attributes generated when constructor is run
        self.new_attributes = []

        # shape and type of the array of returned data
        self.dtype = 'f'
        self.shape = (1, 2, self.samp_num)

        # each element in self.warnings should be in format: [time.time()-self.time_offset, "warning content"]
        self.warnings = []

    def __enter__(self):
        # when opened in the main file by with...as... statement, __enter__ will be called right after __init__
        return self

    def __exit__(self, *exc):
        # when with...as... statementn finished running, __exit__ will be called
        self.task.stop()
        self.task.close()

    def daq_init(self):

        self.task = nidaqmx.Task()
        self.task.ai_channels.add_ai_voltage_chan(
                                                 self.channel,
                                                 min_val=-10.0,
                                                 max_val=10.0,
                                                 units=nidaqmx.constants.VoltageUnits.VOLTS
                                                 )
        self.task.timing.cfg_samp_clk_timing(
                                            rate = self.samp_rate,
                                            # source = "/Dev1/ai/SampleClock", # same source from this channel
                                            active_edge = nidaqmx.constants.Edge.RISING,
                                            sample_mode = nidaqmx.constants.AcquisitionType.FINITE,
                                            samps_per_chan = self.samp_num
                                            )
        self.task.triggers.start_trigger.cfg_dig_edge_start_trig(
                                                                trigger_source = self.trig_channel,
                                                                trigger_edge = nidaqmx.constants.Edge.RISING
                                                                )
        self.task.triggers.start_trigger.retriggerable = True
        # If retriggerbale = False, for CONTINUOUS or FINITE reading mode,
        # only the first read can be triggered by the specified trigger source,
        # and following readings start when task.read() is called,
        # unless the task is started and stopped repeatedly.
        # For FINITE reading mode,
        # if the number of read samples reaches samps_per_chan in cfg_samp_clk_timing,
        # then this task will stop and start automatically.
        # For CONTINUOUS reading mode,
        # a task won't start or stop automatically.

        self.task.start()

    def ReadValue(self):
        try:
            reading = self.task.read(number_of_samples_per_channel=self.samp_num, timeout=10.0) # what will happen if time out?

        except Exception as err:
            logging.error("PCIe6351 reading error!")
            # logging.error(traceback.format_exc())
            reading = [np.NaN]*self.samp_num

        time = np.arange(self.samp_num) * (1/self.samp_rate*1000) # in ms
        data = np.append(time, np.array(reading))
        data = np.array(data).reshape(self.shape)
        attr = {"source": "Teensy with DDS", "trigger": "function generator"}

        return [data, [attr]]

    def update_channel(self, arg):
        if self.task:
            self.task.close()

        self.channel = arg
        try:
            self.daq_init()

        except Exception as err:
            print(err)
            logging.error("PCIe-6351 failed updating channel.")
            logging.error(traceback.format_exc())
            self.task.close()

    def update_trig_channel(self, arg):
        if self.task:
            self.task.close()

        self.trig_channel = arg
        try:
            self.daq_init()

        except Exception as err:
            print(err)
            logging.error("PCIe-6351 failed updating trigger channel.")
            logging.error(traceback.format_exc())
            self.task.close()

    def update_samp_rate(self, arg):
        if self.task:
            self.task.close()

        self.samp_rate = round(float(arg)*1000)
        try:
            self.daq_init()

        except Exception as err:
            print(err)
            logging.error("PCIe-6351 failed updating sampling rate.")
            logging.error(traceback.format_exc())
            self.task.close()

    def update_samp_num(self, arg):
        if self.task:
            self.task.close()

        self.samp_num = int(arg)
        try:
            self.daq_init()
            self.shape = (1, 2, self.samp_num)

        except Exception as err:
            print(err)
            logging.error("PCIe-6351 failed updating number of samples.")
            logging.error(traceback.format_exc())
            self.task.close()

    def GetWarnings(self):
        warnings = self.warnings
        self.warnings = []
        return warnings

# samp_rate = 20
# samp_num = 1000
# channel = "Dev1/ai0"
# trig_channel = "/Dev1/PFI1"
#
# with PCIe6351_ai(0, channel, trig_channel, samp_rate, samp_num) as obj:
#     obj.ReadValue()
#     data = obj.ReadValue()
#     t = data[0][0,0]
#     reading = data[0][0,1]
#
# plt.plot(t, reading)
# plt.show()
