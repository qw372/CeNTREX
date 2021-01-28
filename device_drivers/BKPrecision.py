import numpy as np
import time
import logging
import pyvisa
import traceback

class BKPrecision:
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
        self.shape = (3, )

        # each element in self.warnings should be in format: [time.time()-self.time_offset, "warning content"]
        self.warnings = []

        self.com = self.constr_param[0]
        try:
            self.rm = pyvisa.ResourceManager()
            self.open_com(self.com)
            error = self.instr.query('ERR?')
            while error != '0':
                # clear errors in momery
                # self.warnings.append([time.strftime("%H:%M:%S"), f"Device error code: "+error])
                error = self.instr.query('ERR?')
        except Exception as err:
            self.init_error = ["error", f"Can't open COM port {self.com}."]
            logging.error(err)
            logging.error(traceback.format_exc())
            return

        self.update_vlimit(self.constr_param[1])
        self.update_climit(self.constr_param[2])
        self.update_current(self.constr_param[3])
        self.update_voltage(self.constr_param[4])
        self.update_turnon(self.constr_param[5])

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
            self.iout = self.instr.query('IOUT?') # output current
            self.vout = self.instr.query('VOUT?') # output voltage
            self.state = self.instr.query('OUT?') # on or off
            self.mode = self.instr.query('OUT:STAT?') # cc or cv mode
            error = self.instr.query('ERR?') # query error
            while error != '0':
                self.warnings.append([time.strftime("%H:%M:%S"), f"Device error code: "+error])
                error = self.instr.query('ERR?')
            return [time.time()-self.time_offset, self.iout, self.vout]
        except Exception as err:
            self.warnings.append([time.strftime("%H:%M:%S"), f"Read value function failed \n"+str(err)])
            return [time.time()-self.time_offset, np.NaN, np.NaN]

    def scan(self, type, val):
        self.warnings.append([time.strftime("%H:%M:%S"), f"scan function not implemented."])

    def open_com(self, arg):
        self.instr = self.rm.open_resource(arg)

        time.sleep(0.2)
        self.instr.baud_rate = 57600
        self.instr.data_bits = 8
        self.instr.parity = pyvisa.constants.Parity.none
        self.instr.stop_bits = pyvisa.constants.StopBits.one
        self.instr.read_termination = "\r\n"
        self.instr.write_termination = "\r\n"
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

    def update_vlimit(self, arg):
        try:
            self.vlimit = float(arg)
            self.instr.write(f"OVSET {self.vlimit}") # set overvoltage protection value
            self.instr.write(f"OVP 1") # turn on overvoltage protection
        except Exception as err:
            self.warnings.append([time.strftime("%H:%M:%S"), f"Can't set overvoltage protection value.\n"+str(err)])

    def update_climit(self, arg):
        try:
            self.climit = float(arg)
            self.instr.write(f"OISET {self.climit}") # set overcurrent protection value
            self.instr.write(f"OCP 1") # turn on overcurrent protection
        except Exception as err:
            self.warnings.append([time.strftime("%H:%M:%S"), f"Can't set overcurrent protection value.\n"+str(err)])

    def update_current(self, arg):
        try:
            curr = float(arg)
            if curr > self.climit:
                curr = self.climit
                self.warnings.append([time.strftime("%H:%M:%S"), f"current setting larger than overcurrent protection value. Rounded to overcurrent protection value: {self.climit} A."])
            self.instr.write(f"CURR {curr}") # set current
        except Exception as err:
            self.warnings.append([time.strftime("%H:%M:%S"), f"Can't set current.\n"+str(err)])

    def update_voltage(self, arg):
        try:
            volt = float(arg)
            if volt > self.vlimit:
                volt = self.vlimit
                self.warnings.append([time.strftime("%H:%M:%S"), f"voltage setting larger than overvoltage protection value. Rounded to overvoltage protection value: {self.vlimit} V."])
            self.instr.write(f"Volt {volt}") # set current
        except Exception as err:
            self.warnings.append([time.strftime("%H:%M:%S"), f"Can't set voltage.\n"+str(err)])

    def update_turnon(self, arg):
        try:
            on = int(arg)
            self.instr.write(f"OUT {on}") # set current
        except Exception as err:
            self.warnings.append([time.strftime("%H:%M:%S"), f"Can't turn on the current supply.\n"+str(err)])

    def return_current(self):
        return [self.iout, "normal"]

    def return_voltage(self):
        return [self.vout, "normal"]

    def return_state(self):
        return [self.state, "normal"]

    def return_mode(self):
        return [self.mode, "normal"]

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

# vlimit = 5
# climit = 30
# constcurr = 21
# resistance = 53
# currentout = 10
# turnon = 1
# with BKPrecision(time.time(), "ASRL11::INSTR", vlimit, climit, constcurr, resistance, currentout, turnon) as bk:
#     print(bk.ReadValue())
#     bk.update_turnon(0)
