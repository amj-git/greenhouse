try:
    import smbus  #we use pigpio for the DHT22s.  The ADAFruit library is unreliable.
                    #note you have to start the pigpio demon first before running
    _smbus_ok=True
except ImportError:
    _smbus_ok=False

import time

# Define some constants from the datasheet

BH1750_DEFAULT     = 0x23 # Default device I2C address
POWER_DOWN = 0x00 # No active state
POWER_ON   = 0x01 # Power on
RESET      = 0x07 # Reset data register value

# Start measurement at 4lx resolution. Time typically 16ms.
CONTINUOUS_LOW_RES_MODE = 0x13
# Start measurement at 1lx resolution. Time typically 120ms
CONTINUOUS_HIGH_RES_MODE_1 = 0x10
# Start measurement at 0.5lx resolution. Time typically 120ms
CONTINUOUS_HIGH_RES_MODE_2 = 0x11
# Start measurement at 1lx resolution. Time typically 120ms
# Device is automatically set to Power Down after measurement.
ONE_TIME_HIGH_RES_MODE_1 = 0x20
# Start measurement at 0.5lx resolution. Time typically 120ms
# Device is automatically set to Power Down after measurement.
ONE_TIME_HIGH_RES_MODE_2 = 0x21
# Start measurement at 1lx resolution. Time typically 120ms
# Device is automatically set to Power Down after measurement.
ONE_TIME_LOW_RES_MODE = 0x23

def convertToNumber(data):
  # Simple function to convert 2 bytes of data
  # into a decimal number. Optional parameter 'decimals'
  # will round to specified number of decimal places.
  result=(data[1] + (256 * data[0])) / 1.2
  return (result)

class io_bh1750:
    def __init__(self,addr=BH1750_DEFAULT):
        #self._bus = smbus.SMBus(0) # Rev 1 Pi uses 0
        if _smbus_ok:
            self._bus = smbus.SMBus(1)  # Rev 2 Pi uses 1
            self._addr=addr
            
    def read(self):
        if _smbus_ok:
            try:
                data = self._bus.read_i2c_block_data(self._addr,ONE_TIME_HIGH_RES_MODE_1)
                return convertToNumber(data) 
            except IOError:
                return -999
                   


def main():

  l_sensor=io_bh1750()
  
  while True:
    lightLevel=l_sensor.read()
    print("Light Level : " + format(lightLevel,'.2f') + " lx")
    time.sleep(0.5)

if __name__=="__main__":
   main()