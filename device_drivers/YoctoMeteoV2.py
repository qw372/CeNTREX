import numpy as np
import time
import logging
import traceback
import configparser
import smtplib, ssl

from yoctopuce.yocto_api import *
from yoctopuce.yocto_humidity import *
from yoctopuce.yocto_temperature import *
from yoctopuce.yocto_pressure import *

class YoctoMeteoV2:
    def __init__(self, time_offset, *constr_param):
        # make use of the constr_param
        self.constr_param = list(constr_param)
        print(f"Constructor got passed the following parameter: {self.constr_param}")

        self.init_error = ""

        # HDF attributes generated when constructor is run
        self.new_attributes = []

        # shape and type of the array of returned data
        self.dtype = 'f'
        self.shape = (5, )

        # each element in self.warnings should be in format: [time.time()-self.time_offset, "warning content"]
        self.warnings = []

        errmsg = YRefParam()
        if YAPI.RegisterHub("usb",errmsg) != YAPI.SUCCESS:
            self.init_error = ["error", "device registration error."]
            return

        self.serial_no = self.constr_param[2]
        self.humSensor = YHumidity.FindHumidity(self.serial_no + '.humidity')
        self.pressSensor = YPressure.FindPressure(self.serial_no + '.pressure')
        self.tempSensor = YTemperature.FindTemperature(self.serial_no + '.temperature')

        if not self.humSensor.isOnline():
            self.init_error = ["error", "humidity sensor offline."]
            logging.error("humidity sensor offline.")
            return

        if not self.pressSensor.isOnline():
            self.init_error = ["error", "pressure sensor offline."]
            logging.error("pressure sensor offline.")
            return

        if not self.tempSensor.isOnline():
            self.init_error = ["error", "temperature sensor offline."]
            logging.error("temperature sensor offline.")
            return

        self.time_offset = time_offset
        self.tempset = float(self.constr_param[0])
        self.minTECtemp = float(self.constr_param[1])
        self.RH_safe_margin = 5 # in percentage
        self.tempfluc = 0.5 # temp fluctuation, in deg C
        self.last_email_temp = 0
        self.last_email_humid = 0
        self.email_interval = 600 # in seconds

        self.ReadValue()

        email_settings = configparser.ConfigParser()
        email_settings.read(r"C:\Users\dur!p5\github\SrF-lab-control\device_accessories\YoctoMeteoV2\email_settings.ini")
        self.sender_email = email_settings["sender"]["email_addr"].strip()
        self.receiver_email = [x.strip() for x in email_settings["receiver"]["email_addr"].split(",")]
        self.sender_passcode = email_settings["sender"]["email_passcode"].strip()

    def __enter__(self):
        # when opened in the main file by with...as... statement, __enter__ will be called right after __init__
        return self

    def __exit__(self, *exc):
        # when with...as... statementn finished running, __exit__ will be called
        YAPI.FreeAPI()

    def ReadValue(self):
        if self.tempSensor.isOnline():
            self.temp = self.tempSensor.get_currentValue()
        else:
            self.temp = np.NaN

        if self.humSensor.isOnline():
            self.humid = self.humSensor.get_currentValue()
        else:
            self.humid = np.NaN

        if self.pressSensor.isOnline():
            self.pressure = self.pressSensor.get_currentValue()
        else:
            self.pressure = np.NaN

        self.dewpoint = self.calculate_dew(self.temp, self.humid)
        self.dew_safety = self.calculate_dew(self.temp, self.humid+self.RH_safe_margin)

        return [
                time.time()-self.time_offset,
                self.temp,
                self.humid,
                self.dewpoint,
                self.pressure,
               ]

    def return_temp(self):
        if np.isnan(self.temp):
            return ["nan (Temp sensor offline)", "error"]
        elif np.abs(self.temp-self.tempset) < self.tempfluc:
            return ["{:.2f}".format(self.temp), "normal"]
        else:
            if (time.time() - self.last_email_temp) > self.email_interval:
                self.send_email("temp")
                self.last_email_temp = time.time()
            return ["{:.2f} (WARNING!)".format(self.temp), "error"]

    def return_humid(self):
        if np.isnan(self.humid):
            return ["nan (Humidity sensor offline)", "error"]
        elif self.dew_safety < self.minTECtemp:
            return ["{:.2f}".format(self.humid), "normal"]
        else:
            if (time.time() - self.last_email_humid) > self.email_interval:
                self.send_email("humid")
                self.last_email_humid = time.time()
            return ["{:.2f} (WARNING!)".format(self.humid), "error"]

    def return_dewpoint(self):
        return ["{:.2f}".format(self.dewpoint), "normal"]

    def return_pressure(self):
        if np.isnan(self.pressure):
            return ["nan (Pressure sensor offline)", "error"]
        else:
            return ["{:.2f}".format(self.pressure), "normal"]

    def update_tempsetpoint(self, arg):
        try:
            self.tempset = float(arg)
        except Exception as err:
            self.warnings.append([time.strftime("%H:%M:%S"), f"temp setpoint update failed \n"+str(err)])

    def update_minTECtemp(self, arg):
        try:
            self.minTECtemp = float(arg)
        except Exception as err:
            self.warnings.append([time.strftime("%H:%M:%S"), f"min TEC temp update failed \n"+str(err)])

    def calculate_dew(self, temp, humid):
        # Magnus-Tetens formula, constants from [Sonntag90]
        # good for 0 < temp < 60 C
        # 0.4 C uncertainty in dew point
        a = 17.62
        b = 243.12
        c = a*temp/(b+temp)+np.log(humid/100)
        d = b*c/(a-c)
        return d

    def send_email(self, arg):
        if arg == "humid":
            msg = "Subject: SPL 20D Humidity Warning\n\n"
            # The first line starting with 'Subject: ' and ending with two \n serves as the subject line
            msg += "Warning: Diodes are at risk. "
            msg += "Relative humidity is {:.2f} %. ".format(self.humid)
            msg += "Dew point is {:.2f} degrees C. ".format(self.dewpoint)
            msg += "The lowest TEC temperature was reported as {:.2f} degrees C.\n".format(self.minTECtemp)
            msg += "\n\n\n-------------------------\n"
            msg += "Automated email sent by SrF Python lab control program."
        elif arg =="temp":
            msg = "Subject: SPL 20D Temperature Warning\n\n"
            # The first line starting with 'Subject: ' and ending with two \n serves as the subject line
            msg += "Warning: Significant temperature fluctuation/drift. "
            msg += "Current temperature is {:.2f} degrees C. ".format(self.temp)
            msg += "Temperature set point is {:.2f} degrees C.\n".format(self.tempset)
            msg += "\n\n\n-------------------------\n"
            msg += "Automated email sent by SrF Python lab control program."
        else:
            logging.warning("YoctoMeteo wrong email instruction.")
            return

        port = 465  # required by Gmail for using SMTP_SSL()
        context = ssl.create_default_context()
        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
                server.login(self.sender_email, self.sender_passcode)
                server.sendmail(self.sender_email, self.receiver_email, msg)

        except Exception:
            logging.warning("YoctoMeteo email failed sending.")
            logging.warning(traceback.format_exc())

    def GetWarnings(self):
        warnings = self.warnings
        self.warnings = []
        return warnings

    def scan(self, type, val):
        self.warnings.append([time.strftime("%H:%M:%S"), f"scan function not implemented."])

# with YoctoMeteoV2(time.time(), 20.55, 15, 'METEOMK2-F1A79') as dev:
#     for i in range(3):
#         time.sleep(10)
#         dev.ReadValue()
