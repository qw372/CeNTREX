import numpy as np
import time
import logging
import pyvisa
import traceback

class terranova751a:
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
        self.shape = (4, )

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

        # self.update_pres_unit(self.constr_param[1])
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
            re = self.instr.query('*CU?').split(':') # read current
            self.current = float(re[1].split(',')[0])
        except Exception as err:
            self.warnings.append([time.strftime("%H:%M:%S"), f"Read current failed \n"+str(err)])
            self.current = np.NaN

        try:
            re = self.instr.query('*VO?').split(':') # read current
            self.voltage = float(re[1].split(',')[0])
        except Exception as err:
            self.warnings.append([time.strftime("%H:%M:%S"), f"Read voltage failed \n"+str(err)])
            self.voltage = np.NaN

        try:
            re = self.instr.query('*PR?').split(':') # read current
            self.pressure = float(re[1].split(',')[0])
        except Exception as err:
            self.warnings.append([time.strftime("%H:%M:%S"), f"Read pressure failed \n"+str(err)])
            self.pressure = np.NaN

        try:
            re = self.instr.query('*ST?').split(':') # read current
            self.status = re[1].split(',')[1]
        except Exception as err:
            self.warnings.append([time.strftime("%H:%M:%S"), f"Read machine status failed \n"+str(err)])
            self.status = np.NaN

        return [time.time()-self.time_offset, self.current, self.voltage, self.pressure]

    def scan(self, type, val):
        self.warnings.append([time.strftime("%H:%M:%S"), f"scan function not implemented."])

    def open_com(self, arg):
        self.instr = self.rm.open_resource(arg)

        time.sleep(0.2)
        self.instr.baud_rate = 9600
        self.instr.data_bits = 8
        self.instr.parity = pyvisa.constants.Parity.none
        self.instr.stop_bits = pyvisa.constants.StopBits.one
        self.instr.read_termination = "\r"
        self.instr.write_termination = "\r"
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
            self.update_pres_unit(self.constr_param[1])
        except Exception as err:
            self.warnings.append([time.strftime("%H:%M:%S"), f"Can't open COM port {self.com}\n"+str(err)])

    def update_pres_unit(self, arg):
        try:
            re = self.instr.query(f"*UN:{arg}") # set pressure unit
            print(re)
        except Exception as err:
            self.warnings.append([time.strftime("%H:%M:%S"), f"Can't set pressure unit.\n"+str(err)])

    def return_current(self):
        return [np.format_float_scientific(self.current, precision=2), "normal"]

    def return_voltage(self):
        return [np.format_float_scientific(self.voltage, precision=2), "normal"]

    def return_pressure(self):
        return [np.format_float_scientific(self.pressure, precision=1), "normal"]

    def return_status(self):
        return [self.status, "normal"]

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

# with terranova751a(time.time(), "ASRL23::INSTR", 'mBar') as obj:
#     print(obj.current)
#     print(obj.voltage)
#     print(obj.pressure)
#     print(obj.status)
#     print(obj.warnings)
