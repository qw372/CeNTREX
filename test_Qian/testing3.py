import pyvisa

rm = pyvisa.ResourceManager()
print(rm)
print(rm.list_resources())
