import numpy as np
import time
import logging
import traceback
import pco
import PyQt5.QtWidgets as qt


class PixelflyUSB:
    def __init__(self, time_offset, *constr_param):
        time.sleep(2)
        self.time_offset = time_offset
        self.constr_param = constr_param
        self.parent = self.constr_param[0]
        self.window_outerbox = self.constr_param[1][0]
        self.window_layout = self.constr_param[1][1]
        print(f"Constructor got passed the following parameter: {self.constr_param}")
        self.window_layout.clear()
        # self.parent.app.processEvents()

        if not self.window_outerbox.isVisible():
            self.window_outerbox.show()
        box, self.frame = qt.QWidget(), qt.QGridLayout()
        box.setLayout(self.frame)
        self.window_layout.addWidget(box, 0, 0)
        self.frame.addWidget(qt.QLabel("Push for Window"), 0, 0)
        self.frame.addWidget(qt.QLabel("Push for Window"), 0, 1)
        self.frame.addWidget(qt.QLabel("Push for Window"), 0, 2)
        # make the verification string
        self.verification_string = "diffraction_limit"

        # HDF attributes generated when constructor is run
        self.new_attributes = []

        # shape and type of the array of returned data
        self.dtype = 'f'
        self.shape = ()

        # each element in self.warnings should be in format: [time.time()-self.time_offset, "warning content"]
        self.warnings = []

    def __enter__(self):
        # when opened in the main file by with...as... statement, __enter__ will be called right after __init__
        return self

    def __exit__(self, *exc):
        # when with...as... statementn finished running, __exit__ will be called
        pass

    def ReadValue(self):


        return 0

    def GetWarnings(self):
        warnings = self.warnings
        self.warnings = []
        return warnings
