import sys
from PyQt5 import QtGui, QtCore, QtWidgets

class Window(QtWidgets.QMainWindow):

    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.setGeometry(50, 50, 500, 300)
        self.setWindowTitle("testing")
        self.show()

app = QtWidgets.QApplication(sys.argv)
Gui = Window()
sys.exit(app.exec_())
