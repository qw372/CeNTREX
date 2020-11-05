import numpy as np
import time
import logging
import pyvisa
import traceback

class novatech409B:
    def __init__(self, time_offset, *constr_param1):
        # make use of the constr_param1
        self.constr_param1 = list(constr_param1)
        print(f"Constructor got passed the following parameter: {self.constr_param1}")

        self.time_offset = time_offset
        self.ch = int(self.constr_param1[1][2])

        self.rm = pyvisa.ResourceManager()
        self.open_com(self.constr_param1[0])

        # make the verification string
        self.verification_string = "bzbzbz"

        # HDF attributes generated when constructor is run
        self.new_attributes = []

        # shape and type of the array of returned data
        self.dtype = ('f','int','f','f','f')
        self.shape = (5, )

        self.warnings = []
        # self.update_amp(self.constr_param1[1])
        # self.update_freq(self.constr_param1[2])
        # self.update_phase(self.constr_param1[3])

    def __enter__(self):
        # when opened in the main file by with...as... statement, __enter__ will be called right after __init__
        return self

    def __exit__(self, *exc):
        # when with...as... statementn finished running, __exit__ will be called
        if self.instr:
            self.instr.close()

    def ReadValue(self):
        self.instr.query('QUE') # remove serial echo
        rf_info = []
        for i in range(4):
            rf_message = self.instr.read().split(' ')
            rf_info_raw = {}
            rf_info_raw['freq'] = int(rf_message[0], 16)*0.1/1000000.0 # convert to MHz
            rf_info_raw['phase'] = int(rf_message[1], 16)*360.0/16384.0 # convert to deg
            rf_info_raw['amp'] = int(rf_message[2], 16)/10.23 # convert to %
            rf_info.append(rf_info_raw)

        self.instr.read() # remove the last line from buffer

        # time.sleep(0.2)
        # self.FlushReceiveBuffer()
        # time.sleep(0.2)
        # self.FlushTransmitBuffer()
        # time.sleep(0.2)

        return [
                time.time()-self.time_offset,
                self.ch,
                rf_info[self.ch]['amp'],
                rf_info[self.ch]['freq'],
                rf_info[self.ch]['phase'],
               ]

    def update_ch(self, arg):
        self.constr_param1[1] = arg
        self.ch = int(arg[2])

    def update_amp(self, arg):
        self.constr_param1[2] = arg
        amp_cmd = "V" + str(self.ch) + " " + str(round(float(arg)*10.23))
        self.instr.query(amp_cmd)
        re = self.instr.read()
        # print(re + " amp")

    def update_freq(self, arg):
        self.constr_param1[3] = arg
        freq_cmd = "F" + str(self.ch) + " " + "{:.7f}".format(float(arg))
        self.instr.query(freq_cmd)
        re = self.instr.read()
        # print(re + " freq")

    def update_phase(self, arg):
        self.constr_param1[4] = arg
        phase_cmd = "P" + str(self.ch) + " " + str(round(float(arg)/360.0*16384.0))
        self.instr.query(phase_cmd)
        re = self.instr.read()
        # print(re + " phase")

    def open_com(self, arg):
        try:
            self.instr = self.rm.open_resource(str(arg))
        except pyvisa.errors.VisaIOError as err:
            logging.error("Can't connect to Novatech_409B")
            logging.error(traceback.format_exc())
            self.instr = False
            return

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
        self.instr.close()
        self.constr_param1[0] = str(arg)
        self.open_com(self.constr_param1[0])

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

'''
obj = novatech409B(0, 'ASRL9::INSTR', '10', '20', '10')
print("--------------")

print(obj.ReadValue())
print("---------------")
obj.ReadValue()
'''
