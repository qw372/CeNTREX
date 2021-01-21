import numpy as np
import time, sys
import logging
import pyvisa
import traceback
import PyQt5.QtWidgets as qt

class EdwardsTIC:
    def __init__(self, time_offset, *constr_param):
        self.time_offset = time_offset
        self.constr_param = constr_param
        self.com = self.constr_param[0]
        self.low_limit = float(self.constr_param[1])
        self.upp_limit = float(self.constr_param[2])
        print(f"Constructor got passed the following parameter: {self.constr_param}")
        self.init_error = ""

        # HDF attributes generated when constructor is run
        self.new_attributes = []

        # shape and type of the array of returned data
        self.dtype = 'f'
        self.shape = (2, )

        # each element in self.warnings should be in format: [time.time()-self.time_offset, "warning content"]
        self.warnings = []

        self.rm = pyvisa.ResourceManager()
        if self.open_com(self.com):
            sself.init_error = ""
        else:
            self.init_error = ["error", "failed opening COM port"]
            return
        # self.turn_on_gauge(True)

        self.ReadValue()
        p, state = self.return_pressure()
        if state != "normal":
            self.init_error = ["warning",  f"Ion gause pressure {p} mbar is not in right range."]

    def __enter__(self):
        # when opened in the main file by with...as... statement, __enter__ will be called right after __init__
        return self

    def __exit__(self, *exc):
        # when with...as... statementn finished running, __exit__ will be called
        # self.turn_on_gauge(False)

        if self.instr:
            self.instr.close()

    def ReadValue(self):
        message = self.instr.query('?V914') # '914' is gauge two
        # e.g. message = "=V913 10.00e-03;59;11;0;0"
        message_header = message[:6]
        pressure, unit, state, alertID, priority = message[6:].split(";")
        if message_header != "=V914 ":
            logging.error(f"EdwardsTIC reading error (message header): {message}")
            return [time.time()-self.time_offset, np.NaN]
        elif priority != '0':
            # '0'means ok
            logging.error(f"EdwardsTIC priority error: {message}")
            return [time.time()-self.time_offset, np.NaN]
        elif alertID != '0':
            # '0' means no alert
            logging.error(f"EdwardsTIC alertID error: {message}")
            return [time.time()-self.time_offset, np.NaN]
        # elif state not in ['11', '7']:
        elif state != '11':
            # '11' means gauge on, '7' means initializing
            logging.error(f"Ion gauge state error: {message}")
            return [time.time()-self.time_offset, np.NaN]
        elif unit != '59':
            # '59' means pressure unit pascals
            logging.error(f"EdwardsTIC reading unit error: {message}")
            return [time.time()-self.time_offset, self.pressure]

        self.pressure = float(pressure)/100 # convert ot mbar
        return [time.time()-self.time_offset, self.pressure]

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
            logging.error("Can't connect to EdwardsTIC.")
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

    def update_com(self, arg):
        self.instr.close()
        self.com = str(arg)
        self.open_com(self.com)

    def turn_on_gauge(self, on):
        if on:
            c = '1'
        else:
            c = '0'
        message = self.instr.query(f'!C914 {c}')
        message_header = message[:6]
        state = message[6:]
        if (message_header != "*C914 ") or (state != '0'):
            logging.error(f"EdwardsTIC turn-on error (message header): {message}")

    def return_pressure(self):
        if (self.pressure >= self.low_limit) and (self.pressure <= self.upp_limit):
            return [np.format_float_scientific(self.pressure, precision=2), "normal"]
        else:
            return [np.format_float_scientific(self.pressure, precision=2), "error"]

    def update_lower_limit(self, arg):
        try:
            l_lim = float(arg)
        except ValueError as err:
            logging.error("EdwardsTIC: unable to convert lower limit to float")
            return

        if l_lim >= self.upp_limit:
            logging.warning("EdwardsTIC: lower limit larger than upper limit.")
        else:
            self.low_limit = l_lim

    def update_upper_limit(self, arg):
        try:
            u_lim = float(arg)
        except ValueError as err:
            logging.error("EdwardsTIC: unable to convert upper limit to float")
            return

        if u_lim <= self.low_limit:
            logging.warning("EdwardsTIC: upper limit less than lower limit.")
        else:
            self.upp_limit = u_lim

    def return_lower_limit(self):
        return np.format_float_scientific(self.low_limit, precision=2)

    def return_upper_limit(self):
        return np.format_float_scientific(self.upp_limit, precision=2)

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

# gauge = EdwardsTIC(0, "ASRL3::INSTR", "1e-8", "1e-6")
# print(gauge.return_pressure())
