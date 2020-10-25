import numpy as np

class control:
    def __init__(self, parent):
        self.name = 'control'
        self.parent = parent

    def test(self):
        self.parent.devices = [1, 2]


class cen:
    def __init__(self):
        self.age = 99
        self.con = control(self)


obj1 = cen()
obj1.con.test()

print(obj1.con.name)
print(obj1.devices)
