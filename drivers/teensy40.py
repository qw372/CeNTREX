import numpy as np
import time
import logging
import pyvisa
import traceback

class teensy40:
    def __init__(self, time_offset, *constr_param1):
        # make use of the constr_param1
        self.constr_param1 = list(constr_param1)
        print(f"Constructor got passed the following parameter: {self.constr_param1}")

        self.time_offset = time_offset
        self.rm = pyvisa.ResourceManager()

        self.open_com(self.constr_param1[0])

        # make the verification string
        self.verification_string = "zzzzzz"

        # HDF attributes generated when constructor is run
        self.new_attributes = []

        # shape and type of the array of returned data
        self.dtype = 'f'
        self.shape = (2, )

        # each element in self.warnings should be in format: [time.time()-self.time_offset, "warning content"]
        self.warnings = []

    def __enter__(self):
        # when opened in the main file by with...as... statement, __enter__ will be called right after __init__
        return self

    def __exit__(self, *exc):
        # when with...as... statementn finished running, __exit__ will be called
        if self.instr:
            self.instr.close()

    def ReadValue(self):
        return [
                time.time()-self.time_offset,
                float(self.constr_param1[1]) * np.sin((time.time()-self.time_offset)/10) + np.random.random_sample()*0.3,
               ]

    def update_amp(self, arg):
        self.constr_param1[1] = arg

    def update_led(self, arg):
        self.constr_param1[2] = arg
        if arg:
            print(self.instr.query('1'))
        else:
            print(self.instr.query('0'))

    def open_com(self, arg):
        try:
            self.instr = self.rm.open_resource(str(arg))
        except pyvisa.errors.VisaIOError as err:
            logging.error("Can't connect to Teensy4.0")
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
        self.FlushReadBuffer()
        self.FlushWriteBuffer()

    def update_com(self, arg):
        self.instr.close()
        self.constr_param1[0] = str(arg)
        self.open_com(self.constr_param1[0])

    def GetWarnings(self):
        warnings = self.warnings
        self.warnings = []
        return warnings


    def FlushReadBuffer(self):
        # buffer operation can be found at https://pyvisa.readthedocs.io/en/latest/_modules/pyvisa/constants.html
        return self.rm.visalib.flush(self.instr.session, pyvisa.constants.BufferOperation.discard_read_buffer_no_io)

    def FlushWriteBuffer(self):
        # buffer operation can be found at https://pyvisa.readthedocs.io/en/latest/_modules/pyvisa/constants.html
        return self.rm.visalib.flush(self.instr.session, pyvisa.constants.BufferOperation.discard_write_buffer)
