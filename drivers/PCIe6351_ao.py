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
            self.task.close()
        except Exception as err:
            self.init_error = ["error", "DAQ initialization failed"]
            print(err)
            logging.error(traceback.format_exc())
            self.task.close()
            return

        self.init_error = ""

        # HDF attributes generated when constructor is run
        self.new_attributes = []

        # shape and type of the array of returned data
        self.dtype = 'f'
        # self.shape updated in self.update.waveform()
        # self.shape = (1, 2, self.samp_num)

        # each element in self.warnings should be in format: [time.time()-self.time_offset, "warning content"]
        self.warnings = []
        self.explicitly_start = False

    def __enter__(self):
        # when opened in the main file by with...as... statement, __enter__ will be called right after __init__
        return self

    def __exit__(self, *exc):
        # when with...as... statementn finished running, __exit__ will be called
        # self.task.close()
        pass

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
        self.task.triggers.start_trigger.retriggerable = False
        # self.task.out_stream.output_buf_size = self.samp_num

    def ReadValue(self):
        try:
            self.daq_init()
            num_write = self.task.write(self.writing, auto_start=True, timeout=10.0)
            writing_sample = self.writing
            self.task.wait_until_done(timeout=10.0)
            self.task.close()
            # task.write() returns the actual number of samples successfully written
            # print("actual number of samples successfully written: {:d}".format(num_write))
            # print(time.time()-self.time_offset)

        except Exception as err:
            logging.error("PCIe6351 writing error!")
            logging.error(traceback.format_exc())
            writing_sample = [np.NaN]*self.samp_num
            self.task.close()

        data = np.append(self.timestamp, writing_sample)
        data = np.array(data).reshape(self.shape)
        attr = {"source": "Teensy with DDS", "trigger": "function generator"}

        return [data, [attr]]

    def update_channel(self, arg):
        self.channel = arg

    def update_trig_channel(self, arg):
        self.trig_channel = arg

    def update_samp_rate(self, arg):
        self.samp_rate = round(float(arg)*1000)

    def update_waveform(self):
        self.writing = np.zeros(round(self.t_control[0]/1000*self.samp_rate))
        self.writing = np.append(self.writing, np.ones(round(self.t_control[1]/1000*self.samp_rate))*self.y_control[0])
        self.writing = np.append(self.writing, np.linspace(self.y_control[0], self.y_control[1], round(self.t_control[2]/1000*self.samp_rate)))
        self.writing = np.append(self.writing, np.ones(round(self.t_control[3]/1000*self.samp_rate))*self.y_control[1])
        self.writing = np.append(self.writing, np.ones(round(self.t_control[4]/1000*self.samp_rate))*self.y_control[2])
        self.writing = np.append(self.writing, np.ones(round(self.t_control[5]/1000*self.samp_rate))*self.y_control[3])
        self.writing = np.append(self.writing, np.zeros(1))
        self.samp_num = len(self.writing)
        self.timestamp = np.arange(self.samp_num)*(1/self.samp_rate)*1000 # in ms
        self.shape = (1, 2, self.samp_num)

    def update_t(self, i, arg):
        self.t_control[int(i)] = float(arg)
        self.update_waveform()

    def update_y(self, i, arg):
        self.y_control[int(i)] = float(arg)
        self.update_waveform()

    def GetWarnings(self):
        warnings = self.warnings
        self.warnings = []
        return warnings

# samp_rate = 20 # in kS/s
# channel = "Dev1/ao0"
# trig_channel = "/Dev1/PFI1"
# t_control = {"t1":5, "t2":10, "t3":25, "t4":5, "t5":5, "t6":5}
# y_control = {"y1": 5, "y2": 1, "y3": 4, "y4": 3}
#
# with PCIe6351_ao(0, channel, trig_channel, samp_rate, t_control, y_control) as obj:
#     first_time = time.time()
#     data = obj.ReadValue()
#     print(time.time()-first_time)
#     data = obj.ReadValue()
#     print(time.time()-first_time)
#     data = obj.ReadValue()
#     print(time.time()-first_time)
#     data = obj.ReadValue()
#     print(time.time()-first_time)
#     t = data[0][0,0]
#     writing = data[0][0,1]
#
# plt.plot(t, writing)
# plt.show()
