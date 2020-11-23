import numpy as np
import time
import logging
import traceback
import nidaqmx
import matplotlib.pyplot as plt


class PCIe6351_do:
    def __init__(self, time_offset, *constr_param):
        self.time_offset = time_offset
        self.constr_param = constr_param
        self.channel = self.constr_param[0]
        self.trig_channel = self.constr_param[1]
        self.samp_rate = round(float(self.constr_param[2])*1000) # in S/s
        self.ctrl_param = []
        for key in self.constr_param[3]:
            l = []
            for elem in self.constr_param[3][key]:
                l.append(float(elem))
            self.ctrl_param.append(l)
        print(f"Constructor got passed the following parameter: {self.constr_param}")

        # generate a waveform for analog output
        self.update_waveform()

        try:
            self.daq_init()
            self.task.close()
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
        self.task.do_channels.add_do_chan(
                self.channel,
                line_grouping=nidaqmx.constants.LineGrouping.CHAN_FOR_ALL_LINES
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
        self.writing = np.array([])
        for i, timing in enumerate(self.ctrl_param[0]):
            samp_num_part = round(float(timing)/1000.0*self.samp_rate)
            output_part = np.zeros(samp_num_part)
            for j in range(len(self.ctrl_param)-1):
                output_part += np.ones(samp_num_part)*int(self.ctrl_param[j+1][i])*np.power(2, j)
            self.writing = np.append(self.writing, output_part)
        self.writing = np.append(self.writing, np.array([0]))
        self.writing = [int(elem) for elem in self.writing]
        self.samp_num = len(self.writing)
        self.timestamp = np.arange(self.samp_num)*(1/self.samp_rate)*1000 # in ms
        self.shape = (1, 2, self.samp_num)

    def update_control(self, i, j, arg):
        if int(i) == 0:
            self.ctrl_param[int(i)][int(j)] = float(arg)
        else:
            self.ctrl_param[int(i)][int(j)] = 1 if arg in ["1", "2", 1, 2] else 0
        self.update_waveform()

    def GetWarnings(self):
        warnings = self.warnings
        self.warnings = []
        return warnings

# samp_rate = 20 # in kS/s
# channel = "Dev1/port0/line0:2"
# trig_channel = "/Dev1/PFI1"
# ctrl_param = {"timing": [10, 10, 10, 10, 10], "ch0": [1, 0, 1, 0, 0], "ch1": [0, 1, 0, 1, 0], "ch2": [1, 0, 1, 0, 1]}
#
# with PCIe6351_do(0, channel, trig_channel, samp_rate, ctrl_param) as obj:
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
