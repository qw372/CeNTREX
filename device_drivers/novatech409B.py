import numpy as np
import time
import logging
import pyvisa
import traceback

class novatech409B:
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
        self.shape = (12, )

        # each element in self.warnings should be in format: [time.time()-self.time_offset, "warning content"]
        self.warnings = []
        self.com = constr_param[0]

        try:
            self.rm = pyvisa.ResourceManager()
            self.open_com(self.com)
        except Exception as err:
            self.init_error = ["error", f"Can't open COM port {self.com}."]
            logging.error(err)
            logging.error(traceback.format_exc())
            return

        self.update_ch0_amp(constr_param[1])
        self.update_ch0_freq(constr_param[2])
        self.update_ch0_phase(constr_param[3])
        self.update_ch1_amp(constr_param[4])
        self.update_ch1_freq(constr_param[5])
        self.update_ch1_phase(constr_param[6])
        self.update_ch2_amp(constr_param[7])
        self.update_ch2_freq(constr_param[8])
        self.update_ch2_phase(constr_param[9])
        self.update_ch3_amp(constr_param[10])
        self.update_ch3_freq(constr_param[11])
        self.update_ch3_phase(constr_param[12])

        self.ReadValue()

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
        try:
            self.instr.query('QUE') # remove serial echo
            self.rf_info = []
            for i in range(4):
                rf_message = self.instr.read().split(' ')
                rf_info_raw = {}
                rf_info_raw['freq'] = int(rf_message[0], 16)*0.1/1000000.0 # convert to MHz
                rf_info_raw['phase'] = int(rf_message[1], 16)*360.0/16384.0 # convert to deg
                rf_info_raw['amp'] = int(rf_message[2], 16)/10.23 # convert to %
                self.rf_info.append(rf_info_raw)
            self.instr.read() # remove the last line from buffer
            return [
                    time.time()-self.time_offset,
                    self.rf_info[0]['amp'], self.rf_info[0]['freq'], self.rf_info[0]['phase'],
                    self.rf_info[1]['amp'], self.rf_info[1]['freq'], self.rf_info[1]['phase'],
                    self.rf_info[2]['amp'], self.rf_info[2]['freq'], self.rf_info[2]['phase'],
                    self.rf_info[3]['amp'], self.rf_info[3]['freq'], self.rf_info[3]['phase'],
                   ]
        except Exception as err:
            self.warnings.append([time.strftime("%H:%M:%S"), "ReadVaule function failed"+str(err)])
            return [time.time()-self.time_offset]+[np.NaN]*12

    def scan(self, type, val):
        # e.g. type = ch0_amp(percent)
        type = type.split("_")
        ch = type[0][2]

        if type[1] == "amp(percent)":
            self.update_value(ch, "amp", val)
        elif type[1] == "freq(MHz)":
            self.update_value(ch, "freq", val)
        else:
            self.warnings.append([time.strftime("%H:%M:%S"), "scan type not supported"])

    def update_value(self, ch, param, value):
        try:
            if param == "freq":
                cmd = "F" + str(ch) + " " + "{:.7f}".format(float(value))
            elif param == "amp":
                cmd = f"V{ch} {round(float(value)*10.23)}"
            elif param == "phase":
                cmd = f"P{ch} {round(float(value)/360.0*16384.0)}"
            else:
                self.warnings.append([time.strftime("%H:%M:%S"), "param not supported"])
                return
            self.instr.query(cmd)
            re = self.instr.read()
        except Exception as err:
            self.warnings.append([time.strftime("%H:%M:%S"), f"Ch {ch} {param} update failed. \n"+str(err)])

    def return_value(self, ch, param):
        ch = int(ch)
        if param == "freq":
            return "{:.3f}".format(self.rf_info[ch]['freq'])
        elif param == "amp":
            return "{:.2f}".format(self.rf_info[ch]['amp'])
        elif param == "phase":
            return "{:.2f}".format(self.rf_info[ch]['phase'])
        else:
            self.warnings.append([time.strftime("%H:%M:%S"), "param not supported"])

    def open_com(self, arg):
        self.instr = self.rm.open_resource(str(arg))

        time.sleep(0.2)
        self.instr.baud_rate = 19200
        self.instr.data_bits = 8
        self.instr.parity = pyvisa.constants.Parity.none
        self.instr.stop_bits = pyvisa.constants.StopBits.one
        self.instr.read_termination = "\r\n"
        self.instr.write_termination = "\n"
        self.instr.chunk_size = 1024
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
            self.com = arg
            self.open_com(self.com)
        except Exception as err:
            self.warnings.append([time.strftime("%H:%M:%S"), f"Can't open COM port {self.com}\n"+str(err)])

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

    def update_ch0_freq(self, arg):
        self.update_value(0, "freq", arg)

    def update_ch0_amp(self, arg):
        self.update_value(0, "amp", arg)

    def update_ch0_phase(self, arg):
        self.update_value(0, "phase", arg)

    def update_ch1_freq(self, arg):
        self.update_value(1, "freq", arg)

    def update_ch1_amp(self, arg):
        self.update_value(1, "amp", arg)

    def update_ch1_phase(self, arg):
        self.update_value(1, "phase", arg)

    def update_ch2_freq(self, arg):
        self.update_value(2, "freq", arg)

    def update_ch2_amp(self, arg):
        self.update_value(2, "amp", arg)

    def update_ch2_phase(self, arg):
        self.update_value(2, "phase", arg)

    def update_ch3_freq(self, arg):
        self.update_value(3, "freq", arg)

    def update_ch3_amp(self, arg):
        self.update_value(3, "amp", arg)

    def update_ch3_phase(self, arg):
        self.update_value(3, "phase", arg)

    def return_ch0_freq(self):
        return self.return_value(0, "freq")

    def return_ch0_amp(self):
        return self.return_value(0, "amp")

    def return_ch0_phase(self):
        return self.return_value(0, "phase")

    def return_ch1_freq(self):
        return self.return_value(1, "freq")

    def return_ch1_amp(self):
        return self.return_value(1, "amp")

    def return_ch1_phase(self):
        return self.return_value(1, "phase")

    def return_ch2_freq(self):
        return self.return_value(2, "freq")

    def return_ch2_amp(self):
        return self.return_value(2, "amp")

    def return_ch2_phase(self):
        return self.return_value(2, "phase")

    def return_ch3_freq(self):
        return self.return_value(3, "freq")

    def return_ch3_amp(self):
        return self.return_value(3, "amp")

    def return_ch3_phase(self):
        return self.return_value(3, "phase")
