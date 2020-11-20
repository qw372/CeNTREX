import numpy as np
import time
import logging
import traceback
import nidaqmx
import matplotlib.pyplot as plt


class PCIe6351_ao:
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
        self.task.ao_channels.add_ao_voltage_chan(
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
        self.task.out_stream.output_buf_size = self.samp_num*10 # make buffer size large enough
        # self.task.start()

    def ReadValue(self):
        time = np.arange(self.samp_num) * (1/self.samp_rate*1000) # in ms
        # print(len(time))
        try:
            writing = np.sin(time) * (time/time[-1]*2 + np.random.random_sample()*0.2)
            num_write = self.task.write(writing, auto_start=True, timeout=10.0)
            # task.write() returns the actual number of samples successfully written
            # print("actual number of samples successfully written: {:d}".format(num_write))

        except Exception as err:
            logging.error("PCIe6351 writing error!")
            logging.error(traceback.format_exc())
            writing = [np.NaN]*self.samp_num

        data = np.append(time, np.array(writing))
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
# channel = "Dev1/ao0"
# trig_channel = "/Dev1/PFI1"
#
# with PCIe6351_ao(0, channel, trig_channel, samp_rate, samp_num) as obj:
#     data = obj.ReadValue()
#     data = obj.ReadValue()
#     t = data[0][0,0]
#     writing = data[0][0,1]
#
# plt.plot(t, writing)
# plt.show()
