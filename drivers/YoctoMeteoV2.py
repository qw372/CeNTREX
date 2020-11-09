import numpy as np
import time
import logging
import traceback
import smtplib, ssl

class YoctoMeteoV2:
    def __init__(self, time_offset, *constr_param1):
        # make use of the constr_param1
        self.constr_param1 = list(constr_param1)
        print(f"Constructor got passed the following parameter: {self.constr_param1}")

        self.time_offset = time_offset
        self.tempset = float(self.constr_param1[0])
        self.minTECtemp = float(self.constr_param1[1])
        self.RH_safe_margin = 5 # in percentage
        self.tempfluc = 0.5 # temp fluctuation, in deg C
        self.last_email_temp = 0
        self.last_email_humid = 0
        self.email_interval = 600 # in seconds

        self.ReadValue()

        self.sender_email = "yalebufferlab@gmail.com"
        self.receiver_email = ["qian.wang.qw95@yale.edu", "qian.wang.372@gmail.com"]
        self.sender_passcode = "A6nMrHATgfzDF"

        self.verification_string = "globalwarming"

        # HDF attributes generated when constructor is run
        self.new_attributes = []

        # shape and type of the array of returned data
        self.dtype = 'f'
        self.shape = (5, )

        self.warnings = []

    def __enter__(self):
        # when opened in the main file by with...as... statement, __enter__ will be called right after __init__
        return self

    def __exit__(self, *exc):
        # when with...as... statementn finished running, __exit__ will be called
        pass

    def ReadValue(self):
        self.temp = np.sin(time.time()-self.time_offset)
        self.humid = np.sin(time.time()-self.time_offset) + 1
        self.dewpoint = self.calculate_dew(self.temp, self.humid)
        self.dew_safety = self.calculate_dew(self.temp, self.humid+self.RH_safe_margin)
        self.pressure = np.sin(time.time()-self.time_offset) + 3

        return [
                time.time()-self.time_offset,
                self.temp,
                self.humid,
                self.dewpoint,
                self.pressure,
               ]

    def return_temp(self):
        if np.abs(self.temp-self.tempset) < self.tempfluc:
            return ["{:.2f}".format(self.temp), "normal"]
        else:
            if (time.time() - self.last_email_temp) > self.email_interval:
                self.send_email("temp")
                self.last_email_temp = time.time()
            return ["{:.2f} (WARNING!)".format(self.temp), "error"]

    def return_humid(self):
        if self.dew_safety < self.minTECtemp:
            return ["{:.2f}".format(self.humid), "normal"]
        else:
            if (time.time() - self.last_email_humid) > self.email_interval:
                self.send_email("humid")
                self.last_email_humid = time.time()
            return ["{:.2f} (WARNING!)".format(self.humid), "error"]

    def return_dewpoint(self):
        return ["{:.2f}".format(self.dewpoint), "normal"]

    def return_pressure(self):
        return ["{:.2f}".format(self.pressure), "normal"]

    def update_tempsetpoint(self, arg):
        self.tempset = float(arg)
        return "{:.2f}".format(self.tempset)

    def update_minTECtemp(self, arg):
        self.minTECtemp = float(arg)
        return "{:.2f}".format(self.minTECtemp)

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
            # the first line start with 'Subject' and end with two \n serves as the subject line
            msg += "Warning: Diodes are at risk. "
            msg += "Relative humidity is {:.2f} %. ".format(self.humid)
            msg += "Dew point is {:.2f} degrees C. ".format(self.dewpoint)
            msg += "The lowest TEC temperature was reported as {:.2f} degrees C.\n".format(self.minTECtemp)
            msg += "\n\n\n-------------------------\n"
            msg += "Automated email sent by SrF Python lab control program."
        elif arg =="temp":
            msg = "Subject: SPL 20D Temperature Warning\n\n"
            # the first line start with 'Subject' and end with two \n serves as the subject line
            msg += "Warning: Significant temperature fluctuation/drift. "
            msg += "Current temperature is {:.2f} degrees C. ".format(self.temp)
            msg += "Temperature set point is {:.2f} degrees C.\n".format(self.tempset)
            msg += "\n\n\n-------------------------\n"
            msg += "Automated email sent by Python lab control program."
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
