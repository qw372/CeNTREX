import numpy as np
import time
import logging
import traceback
import nidaqmx
import h5py


class AOM_VVA:
    def __init__(self, time_offset, *constr_param):
        self.time_offset = time_offset
        self.constr_param = constr_param
        self.update_aochannel(self.constr_param[0])
        self.update_trigchannel(self.constr_param[1])
        self.update_turnon(self.constr_param[7])
        print(f"Constructor got passed the following parameter: {self.constr_param}")

        self.samp_rate = 5000 # Samples/s

        self.init_error = ""

        # HDF attributes generated when constructor is run
        self.new_attributes = []

        # shape and type of the array of returned data
        self.dtype = 'f'
        self.shape = (6,)

        # each element in self.warnings should be in format: [time.strftime("%H:%M:%S"), "warning content"]
        self.warnings = []

        try:
            self.MOTintensity = float(self.constr_param[2])
            self.holdintensity = float(self.constr_param[3])
            self.MOTduration = float(self.constr_param[4])
            self.rampduration = float(self.constr_param[5])
            self.holdduration = float(self.constr_param[6])
        except Exception as err:
            self.init_error = ["error", "can't convert given parameters to floating point numbers"]
            logging.error(err)
            logging.error(traceback.format_exc())
            return

        self.update_waveform()

        try:
            self.daq_ao_init()
            self.ao_task.close()
        except Exception as err:
            self.init_error = ["error", "DAQ initialization failed"]
            logging.error(err)
            logging.error(traceback.format_exc())
            return

        try:
            # make laser intensity as MOT intensity level when it's not used for other things.
            self.ao_init_task = nidaqmx.Task("AOM_VVA_init")
            self.ao_init_task.ao_channels.add_ao_voltage_chan(
                    self.ao_channel,
                    min_val=-3,
                    max_val=0,
                    units=nidaqmx.constants.VoltageUnits.VOLTS
                )
            self.ao_init_task.write(self.waveform[-1])
            self.ao_init_task.close()
        except Exception as err:
            self.init_error = ["error", "DAQ update initial output failed"]
            logging.error(err)
            logging.error(traceback.format_exc())
            return

    def __enter__(self):
        # when opened in the main file by with...as... statement, __enter__ will be called right after __init__
        return self

    def __exit__(self, *exc):
        # when with...as... statementn finished running, __exit__ will be called
        try:
            self.ao_task.close()
        except Exception as err:
            pass

    def daq_ao_init(self):
        self.ao_task = nidaqmx.Task("AOM_VVA")
        self.ao_task.ao_channels.add_ao_voltage_chan(
                self.ao_channel,
                min_val=-3,
                max_val=0,
                units=nidaqmx.constants.VoltageUnits.VOLTS
            )
        self.ao_task.timing.cfg_samp_clk_timing(
                rate = self.samp_rate,
                # source = "/Dev1/ai/SampleClock", # same source from this channel
                active_edge = nidaqmx.constants.Edge.RISING,
                sample_mode = nidaqmx.constants.AcquisitionType.FINITE,
                samps_per_chan = self.samp_num
            )
        self.ao_task.triggers.start_trigger.cfg_dig_edge_start_trig(
                trigger_source = self.trig_channel,
                trigger_edge = nidaqmx.constants.Edge.RISING
            )

    def ReadValue(self):
        if self.turnon:
            try:
                self.daq_ao_init()
                num_write = self.ao_task.write(self.waveform, auto_start=True, timeout=5.0)
                return_list = [self.MOTintensity, self.holdintensity, self.MOTduration, self.rampduration, self.holdduration]

                t = time.time()
                while not self.ao_task.is_task_done():
                    time.sleep(0.01)
                    if (time.time()-t) > 3.0:
                        # what if the DAQ is just triggered at the end of this period and doesn't have enough time to finish?
                        # anyway it should work the same as wait_until_done function, except it doesn't raise errors
                        return_list = [0, 0, 0, 0, 0]
                        break

                self.ao_task.close()
                return [time.time()-self.time_offset, *return_list]

            except Exception as err:
                self.warnings.append([time.strftime("%H:%M:%S"), f"DAQ writing error.\n"+str(err)])
                self.ao_task.close()
                return [time.time()-self.time_offset, np.NaN, np.NaN, np.NaN, np.NaN, np.NaN]
        else:
            return [time.time()-self.time_offset, 0, 0, 0, 0, 0]

    def update_aochannel(self, arg):
        self.ao_channel = arg

    def update_trigchannel(self, arg):
        self.trig_channel = arg

    def update_MOTintensity(self, arg):
        try:
            c = float(arg)
        except ValueError as err:
            self.warnings.append([time.strftime("%H:%M:%S"), f"failed to convert MOT intensity, current setting: {self.MOTintensity} %"])
            return

        self.MOTintensity = c
        self.update_waveform()

    def update_holdintensity(self, arg):
        try:
            c = float(arg)
        except ValueError as err:
            self.warnings.append([time.strftime("%H:%M:%S"), f"failed to convert hold intensity, current setting: {self.holdintensity} %"])
            return

        self.holdintensity = c
        self.update_waveform()

    def update_MOTduration(self, arg):
        try:
            t = float(arg)
        except ValueError as err:
            self.warnings.append([time.strftime("%H:%M:%S"), f"failed to convert MOT duration, current setting: {self.MOTduration} ms"])
            return

        self.MOTduration = t
        self.update_waveform()

    def update_rampduration(self, arg):
        try:
            t = float(arg)
        except ValueError as err:
            self.warnings.append([time.strftime("%H:%M:%S"), f"failed to convert ramp duration, current setting: {self.rampduration} ms"])
            return

        self.rampduration = t
        self.update_waveform()

    def update_holdduration(self, arg):
        try:
            t = float(arg)
        except ValueError as err:
            self.warnings.append([time.strftime("%H:%M:%S"), f"failed to convert hold duration, current setting: {self.holdduration} ms"])
            return

        self.holdduration = t
        self.update_waveform()

    def update_waveform(self):
        self.waveform = np.ones(int(self.MOTduration*self.samp_rate/1000))*self.MOTintensity
        self.waveform = np.append(self.waveform, np.linspace(self.MOTintensity, self.holdintensity, int(self.rampduration*self.samp_rate/1000)))
        self.waveform = np.append(self.waveform, np.ones(int(self.holdduration*self.samp_rate/1000))*self.holdintensity)
        self.waveform = np.append(self.waveform, self.MOTintensity)

        filename = 'C:/Users/dur!p5/github/SrF-lab-control/device_accessories/AOM_VVA/LookUpTable_lastest.hdf'
        with h5py.File(filename, 'r') as f:
            lut = np.array(f["LookUpTable"])
            lut_voltage = [lut[i][0] for i in range(len(lut))]
            lut_laserintensity = [lut[i][1] for i in range(len(lut))]
            self.waveform = np.interp(self.waveform, lut_laserintensity, lut_voltage, left=lut_voltage[0], right=lut_voltage[-1])

        self.samp_num = len(self.waveform)

    def update_turnon(self, arg):
        self.turnon = bool(arg)

    def scan(self, type, val):
        self.warnings.append([time.strftime("%H:%M:%S"), f"scan function not implemented."])

    def GetWarnings(self):
        warnings = self.warnings
        self.warnings = []
        return warnings

# aochannel = "Dev3/ao0"
# trigchannel = "/Dev3/PFI1"
# MOTintensity = 80
# holdintensity = 20
# MOTduration = 500
# rampduration = 50
# holdduration = 20
# turnon = True
#
# constr_params = [aochannel, trigchannel, MOTintensity, holdintensity, MOTduration, rampduration, holdduration, turnon]
# with AOM_VVA(time.time(), *constr_params) as dev:
#     print(dev.waveform)
