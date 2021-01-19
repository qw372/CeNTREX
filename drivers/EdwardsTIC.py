import numpy as np
import time
import logging
import pyvisa

class EdwardsTIC:
    def __init__(self, time_offset, *constr_param):
        self.time_offset = time_offset
        self.constr_param = constr_param
        self.com = self.constr_param[0]
        print(f"Constructor got passed the following parameter: {self.constr_param}")

        self.rm = pyvisa.ResourceManager()
        if self.open_com(self.com):
            # make the verification string
            self.verification_string = "vacuum"
        else:
            self.verification_string = False
        self.ReadValue()

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
        pass

    def ReadValue(self):
        self.instr.query('?V913')
        message = self.instr.read()
        message_header = message[:6]
        if message_header != "=V913 ":
            logging.error(f"EdwardsTIC reading error: {message}")
            return [time.time()-self.time_offset, np.NaN]
        else:
            print(message)
            return 1

    def scan(self, type, val):
        print("EdwardsTIC: no scanning implemented.")

    def GetWarnings(self):
        warnings = self.warnings
        self.warnings = []
        return warnings

    def open_com(self, arg):
        try:
            self.instr = self.rm.open_resource(str(arg))
        except pyvisa.errors.VisaIOError as err:
            logging.error("Can't connect to Novatech_409B")
            logging.error(traceback.format_exc())
            self.instr = False
            return False

        time.sleep(0.2)
        self.instr.read_termination = "\r"
        self.instr.write_termination = "\r"

        self.rm.visalib.set_buffer(self.instr.session, pyvisa.constants.BufferType.io_in, 1024)
        self.rm.visalib.set_buffer(self.instr.session, pyvisa.constants.BufferType.io_out, 1024)
        time.sleep(0.2)
        self.FlushTransmitBuffer()
        time.sleep(0.2)
        self.FlushReceiveBuffer()
        time.sleep(0.2)

        return True

    def update_com(self):
        pass

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

gauge = EdwardsTIC(0, "ASRL8::INSTR")
