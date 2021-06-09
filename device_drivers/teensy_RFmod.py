import numpy as np
import time
import logging
import pyvisa
import traceback
import h5py

class teensy_RFmod:
    def __init__(self, time_offset, *constr_param):
        # make use of the constr_param
        self.time_offset = time_offset
        self.constr_param = constr_param
        print(f"Constructor got passed the following parameter: {self.constr_param}")

        self.init_error = ""

        # HDF attributes generated when constructor is run
        self.new_attributes = []

        # shape and type of the array of returned data
        self.dtype = 'f'
        self.shape = (7, )

        # each element in self.warnings should be in format: [time.time()-self.time_offset, "warning content"]
        self.warnings = []

        self.com = self.constr_param[0]
        try:
            self.rm = pyvisa.ResourceManager()
            self.open_com(self.com)
        except Exception as err:
            self.init_error = ["error", f"Can't open COM port {self.com}."]
            logging.error(err)
            logging.error(traceback.format_exc())
            return

        try:
            self.rampduration = float(self.constr_param[1]) # in ms
            self.holdduration = float(self.constr_param[2]) # in ms
            self.motfreq = float(self.constr_param[3]) # in MHz
            self.cmotfreq = float(self.constr_param[4]) # in MHz
            self.motamp = float(self.constr_param[5]) # in percent
            self.cmotamp = float(self.constr_param[6]) # in percent
            self.timestep_ms = float(self.constr_param[7]) # in ms
        except Exception as err:
            self.init_error = ["error", f"Failed to convert parameters."]
            logging.error(err)
            logging.error(traceback.format_exc())
            return

        self.update_rampduraiton(self.rampduration) # amplitude will be updated in this step as well
        self.update_holdduraiton(self.holdduration)
        self.update_motfreq(self.motfreq)
        self.update_cmotfreq(self.cmotfreq)

    def __enter__(self):
        # when opened in the main file by with...as... statement, __enter__ will be called right after __init__
        return self

    def __exit__(self, *exc):
        # when with...as... statementn finished running, __exit__ will be called
        try:
            self.instr.close()
        except AttributeError:
            pass

    def ReadValue(self):
        return [time.time()-self.time_offset, self.rampduration, self.holdduration, self.motfreq, self.cmotfreq, self.motamp, self.cmotamp]

    def scan(self, type, val):
        self.warnings.append([time.strftime("%H:%M:%S"), f"scan function not implemented."])

    def open_com(self, arg):
        self.instr = self.rm.open_resource(arg)

        time.sleep(0.2)
        self.instr.baud_rate = 19200
        self.instr.data_bits = 8
        self.instr.parity = pyvisa.constants.Parity.none
        self.instr.stop_bits = pyvisa.constants.StopBits.one
        self.instr.read_termination = "\n"
        self.instr.write_termination = "\n"
        self.instr.flow_control = pyvisa.constants.ControlFlow.none

        self.rm.visalib.set_buffer(self.instr.session, pyvisa.constants.BufferType.io_in, 1024)
        self.rm.visalib.set_buffer(self.instr.session, pyvisa.constants.BufferType.io_out, 1024)
        time.sleep(0.2)
        self.FlushTransmitBuffer()
        time.sleep(0.2)
        self.FlushReceiveBuffer()
        time.sleep(0.2)

    def update_com(self, arg):
        try:
            self.instr.close()
            self.com = str(arg)
            self.open_com(self.com)
        except Exception as err:
            self.warnings.append([time.strftime("%H:%M:%S"), f"Can't open COM port {self.com}\n"+str(err)])

    def update_rampduraiton(self, arg):
        try:
            t = float(arg)
        except Exception as err:
            self.warnings.append([time.strftime("%H:%M:%S"), f"Can't set ramp duration.\n"+str(err)])
            return

        self.rampduration = t
        self.instr.query(f"s{int(self.rampduration/self.timestep_ms)},{int(self.holdduration/self.timestep_ms)}")

        self.update_amp_waveform()

    def update_holdduraiton(self, arg):
        try:
            t = float(arg)
        except Exception as err:
            self.warnings.append([time.strftime("%H:%M:%S"), f"Can't set hold duration.\n"+str(err)])
            return

        self.holdduration = t
        self.instr.query(f"s{int(self.rampduration/self.timestep_ms)},{int(self.holdduration/self.timestep_ms)}")

    def update_motfreq(self, arg):
        try:
            f = float(arg)*1e6 # convert MHz to Hz
        except Exception as err:
            self.warnings.append([time.strftime("%H:%M:%S"), f"Can't set MOT frequency.\n"+str(err)])
            return

        self.motfreq = f
        self.instr.query(f"f{self.motfreq},{self.cmotfreq}") # mot frequency has to be higher than cmot frequency

    def update_cmotfreq(self, arg):
        try:
            f = float(arg)*1e6 # convert MHz to Hz
        except Exception as err:
            self.warnings.append([time.strftime("%H:%M:%S"), f"Can't set CMOT frequency.\n"+str(err)])
            return

        self.cmotfreq = f
        self.instr.query(f"f{self.motfreq},{self.cmotfreq}") # mot frequency has to be higher than cmot frequency

    def update_motamp(self, arg):
        try:
            a = float(arg)
        except Exception as err:
            self.warnings.append([time.strftime("%H:%M:%S"), f"Can't set MOT rf amplitude.\n"+str(err)])
            return

        self.motamp = a
        self.update_amp_waveform()

    def update_cmotamp(self, arg):
        try:
            a = float(arg)
        except Exception as err:
            self.warnings.append([time.strftime("%H:%M:%S"), f"Can't set CMOT rf amplitude.\n"+str(err)])
            return

        self.cmotamp = a
        self.update_amp_waveform()

    def update_amp_waveform(self):
        laser_amp_list = np.linspace(self.motamp, self.cmotamp, int(self.rampduration/self.timestep_ms))
        freq_list = np.linspace(self.motfreq, self.cmotfreq, int(self.rampduration/self.timestep_ms))
        filename = 'C:/Users/dur!p5/github/SrF-lab-control/device_accessories/teensy_RFmod/LookUpTable_lastest.hdf'
        with h5py.File(filename, 'r') as f:
            lut = np.array(f["LookUpTable"])
            lut_amp = [lut[i][0] for i in range(len(lut))]
            dtp = list(f["LookUpTable"].dtype.fields.keys())[1:] # get column names, which is frequency information
            lut_freq = [float(i.split("/")[0]) for i in dtp]
            fnum = len(lut[0])-1 # number of frequency data points
            for i in range(fnum):
                amp = [lut[j][i+1] for j in range(len(lut))]
                if i==0:
                    dds_amp_list = np.interp(laser_amp_list, amp, lut_amp)
                else:
                    dds_amp_list = np.vstack((dds_amp_list, np.interp(laser_amp_list, amp, lut_amp)))
            dds_amp_list = dds_amp_list.T
            output_list = np.array([])
            for i in range(len(freq_list)):
                output_list = np.append(output_list, np.interp(freq_list[i], lut_freq, dds_amp_list[i]))

        # output_list = np.linspace(self.motamp, self.cmotamp, int(self.rampduration/self.timestep_ms))
        # output_list = np.sqrt(output_list)*10
        s = ",".join(["{:.2f}".format(i) for i in output_list]) # only keep 2 decimals in case of anything wierd in serial message.
        # print(s)

        m = self.instr.query(f"o{s}")

    def GetWarnings(self):
        warnings = self.warnings
        self.warnings = []
        return warnings

    def FlushReceiveBuffer(self):
        # buffer operation can be found at https://pyvisa.readthedocs.io/en/latest/_modules/pyvisa/constants.html
        # re = self.rm.visalib.flush(self.instr.session, pyvisa.constants.BufferOperation.discard_receive_buffer)
        # print(re)
        self.instr.flush(pyvisa.constants.BufferOperation.discard_receive_buffer)

    def FlushTransmitBuffer(self):
        # buffer operation can be found at https://pyvisa.readthedocs.io/en/latest/_modules/pyvisa/constants.html
        # re = self.rm.visalib.flush(self.instr.session, pyvisa.constants.BufferOperation.flush_transmit_buffer)
        # print(re)
        self.instr.flush(pyvisa.constants.BufferOperation.discard_transmit_buffer)

# COM_port = "ASRL18::INSTR"
# rampduration = 50 # in ms
# holdduration = 200 # in ms
# motfreq = 73 # in MHz
# cmotfreq = 65 # in MHz
# motamp = 70 # in percent
# cmotamp = 20 # in percent
# timestep_ms = 0.1 # in ms
# with teensy_RFmod(time.time(), COM_port, rampduration, holdduration, motfreq, cmotfreq, motamp, cmotamp, timestep_ms) as dev:
#     t = time.time()
#     dev.update_amp_waveform()
#     print(time.time()-t)
