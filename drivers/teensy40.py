import numpy as np
import time
import logging
import pyvisa
import traceback

class teensy40:
    def __init__(self, time_offset, *constr_param1):
        self.time_offset = time_offset
        self.rm = pyvisa.ResourceManager()
        try:
            self.instr = self.rm.open_resource('ASRL4::INSTR')
        except pyvisa.errors.VisaIOError as err:
            logging.error("Can't connect to Teensy4.0")
            logging.error(traceback.format_exc())
            self.instr = False
            return

        self.instr.baud_rate = 9600
        self.instr.data_bits = 8
        self.instr.parity = pyvisa.constants.Parity.none
        self.instr.stop_bits = pyvisa.constants.StopBits.one
        self.instr.read_termination = "\n"
        self.instr.write_termination = "\n"

        self.rm.visalib.flush(self.instr.session, pyvisa.constants.BufferOperation.discard_read_buffer_no_io)
        # self.ClearBuffer()

        # make the verification string
        self.verification_string = "zzzzzz"

        # HDF attributes generated when constructor is run
        self.new_attributes = []

        # shape and type of the array of returned data
        self.dtype = 'f'
        self.shape = (2, )

        self.warnings = []

        # make use of the constr_param1
        self.constr_param1 = list(constr_param1)
        print(f"Constructor got passed the following parameter: {self.constr_param1}")

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
                float(self.constr_param1[0]) * np.sin((time.time()-self.time_offset)/2.0),
               ]

    def update_amp(self, arg):
        self.constr_param1[0] = arg

    def update_led(self, arg):
        self.constr_param1[1] = arg
        print(self.instr.query(str(arg)))
        # print(arg)
        # print(isinstance(arg, int))
        # print("self.led_status = " + str(arg))

    def GetWarnings(self):
        warnings = self.warnings
        self.warnings = []
        return warnings

    def ClearBuffer(self):
        try:
            self.instr.read()
        except:
            pass


rm = pyvisa.ResourceManager()
print(rm.list_resources())

b = 3.34444-5.33345
a = [float("{:.3f}".format(b)), 1]
print(str(a))
