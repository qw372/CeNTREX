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
        self.rm = pyvisa.ResourceManager()

        self.open_com(self.constr_param1[0])

        # make the verification string
        self.verification_string = "bzbzbz"

        # HDF attributes generated when constructor is run
        self.new_attributes = []

        # shape and type of the array of returned data
        self.dtype = 'f'
        self.shape = (4, )

        self.warnings = []
        self.update_amp(self.constr_param1[1])
        self.update_freq(self.constr_param1[2])
        self.update_phase(self.constr_param1[3])

    def __enter__(self):
        # when opened in the main file by with...as... statement, __enter__ will be called right after __init__
        return self

    def __exit__(self, *exc):
        # when with...as... statementn finished running, __exit__ will be called
        if self.instr:
            self.instr.close()

    def ReadValue(self):
        self.instr.query('QUE') # serial echo
        print(self.instr.read())


        print(self.instr.read())
        print(self.instr.read())
        print(self.instr.read())
        print(self.instr.read())

        self.FlushReceiveBuffer()
        time.sleep(0.5)
        self.FlushTransmitBuffer()
        time.sleep(0.5)

        return [
                time.time()-self.time_offset,
                float(self.constr_param1[1]) * np.sin((time.time()-self.time_offset)/2.0),
                float(self.constr_param1[1]) * np.sin((time.time()-self.time_offset)/2.0),
                float(self.constr_param1[1]) * np.sin((time.time()-self.time_offset)/2.0),
               ]

    def update_amp(self, arg):
        self.constr_param1[1] = arg
        amp_cmd = "V0 " + str(round(float(arg)*10.23))
        self.instr.query(amp_cmd)
        re = self.instr.read()
        print(re + "amp")

    def update_freq(self, arg):
        self.constr_param1[2] = arg
        freq_cmd = "F0 " + "{:.7f}".format(float(arg))
        self.instr.query(freq_cmd)
        re = self.instr.read()
        print(re + "freq")

    def update_phase(self, arg):
        self.constr_param1[3] = arg
        phase_cmd = "P0 " + str(round(float(arg)/360.0*16384.0))
        self.instr.query(phase_cmd)
        re = self.instr.read()
        print(re + "phase")

    def open_com(self, arg):
        try:
            self.instr = self.rm.open_resource(str(arg))
        except pyvisa.errors.VisaIOError as err:
            logging.error("Can't connect to Novatech_409B")
            logging.error(traceback.format_exc())
            self.instr = False
            return

        self.instr.baud_rate = 19200
        self.instr.data_bits = 8
        self.instr.parity = pyvisa.constants.Parity.none
        self.instr.stop_bits = pyvisa.constants.StopBits.one
        self.instr.read_termination = "\n"
        self.instr.write_termination = "\n"

        time.sleep(0.2)
        self.FlushTransmitBuffer()
        time.sleep(0.2)

        # turn off serial echo
        # self.instr.write("E D")
        # self.instr.write('R')
        #time.sleep(0.2)
        # print(self.instr.read())
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
        re = self.rm.visalib.flush(self.instr.session, pyvisa.constants.BufferOperation.discard_read_buffer_no_io)
        print(re)
        return re

    def FlushTransmitBuffer(self):
        # buffer operation can be found at https://pyvisa.readthedocs.io/en/latest/_modules/pyvisa/constants.html
        re = self.rm.visalib.flush(self.instr.session, pyvisa.constants.BufferOperation.discard_transmit_buffer)
        print(re)
        return re

obj = novatech409B(0, 'ASRL8::INSTR', '10', '10', '10')
print("--------------")

obj.ReadValue()
print("---------------")
obj.ReadValue()

print(obj.rm.list_resources())
