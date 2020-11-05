import pyvisa
import numpy as np

rm = pyvisa.ResourceManager()
print(rm.list_resources())

print(np.dtype([('a', 'str'), ('b', 'int')]))
