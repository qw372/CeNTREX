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
        self.samp_rate = round(float(self.constr_param[2])*1000) # in S/s
        self.t_control = []
        for key in self.constr_param[3]:
            self.t_control.append(float(self.constr_param[3][key])) # in ms
        self.y_control = []
        for key in self.constr_param[4]:
            self.y_control.append(float(self.constr_param[4][key])) # in ms
        print(f"Constructor got passed the following parameter: {self.constr_param}")

        # generate a waveform for analog output
        self.update_waveform()

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
        # self.shape updated in self.update.waveform()
        # self.shape = (1, 2, self.samp_num)

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

    def ReadValue(self):
        try:
            num_write = self.task.write(self.writing, auto_start=True, timeout=10.0)
            # task.write() returns the actual number of samples successfully written
            # print("actual number of samples successfully written: {:d}".format(num_write))

        except Exception as err:
            logging.error("PCIe6351 writing error!")
            logging.error(traceback.format_exc())
            writing = [np.NaN]*self.samp_num

        data = np.append(self.timestamp, self.writing)
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

    def update_waveform(self):
        self.writing = np.zeros(round(self.t_control[0]/1000*self.samp_rate))
        self.writing = np.append(self.writing, np.ones(round(self.t_control[1]/1000*self.samp_rate))*self.y_control[0])
        self.writing = np.append(self.writing, np.linspace(self.y_control[0], self.y_control[1], round(self.t_control[2]/1000*self.samp_rate)))
        self.writing = np.append(self.writing, np.ones(round(self.t_control[3]/1000*self.samp_rate))*self.y_control[1])
        self.writing = np.append(self.writing, np.ones(round(self.t_control[4]/1000*self.samp_rate))*self.y_control[2])
        self.writing = np.append(self.writing, np.ones(round(self.t_control[5]/1000*self.samp_rate))*self.y_control[3])
        self.samp_num = len(self.writing)
        self.timestamp = np.arange(self.samp_num)*(1/self.samp_rate)*1000 # in ms
        self.shape = (1, 2, self.samp_num)

    def update_t(self, i, arg):
        self.t_control[int(i)] = float(arg)
        self.update_waveform()

    def update_y(self, arg):
        self.y_control[int(i)] = float(arg)
        self.update_waveform()

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
