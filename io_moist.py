#Moisture Sensor Reader

import time
try:
    import pigpio  
    _pigpio_ok=True
except ImportError:
    _pigpio_ok=False
from time import sleep

class sensor:
    
    '''A class to read moisture sensors
        pi=handle to pigpio
        gpio_ref=pin number of reference pin. This pin generates PWM
             which goes to all comparators
        gpio_det[]=array of pin numbers for comparator outputs 
    '''
    
    def __init__(self, h_gpio, gpio_ref, gpio_det):
        self._h_gpio = pi
        self._gpio_ref = gpio_ref
        self._gpio_det = gpio_det
      
        self._h_gpio.set_mode(self._gpio_ref,pigpio.OUTPUT)  #set up PWM on REF pin
      
        #set the input pins
        for det_pin in self._gpio_det:
            self._h_gpio.set_mode(det_pin,pigpio.INPUT)
            
        self._h_gpio.set_PWM_range(self._gpio_ref,255) #1 byte
        self._h_gpio.set_PWM_frequency(self._gpio_ref,100000) #set highest freq
        self._pwm_freq=(self._h_gpio.get_PWM_frequency(self._gpio_ref)) #should get 8kHz
        
        self._set_ref(128)  #set the output to 50% initially

    def _set_ref(self,val):
        self._h_gpio.set_PWM_dutycycle(self._gpio_ref,val)
        
    def read(self):
        data=[]
        for det_pin in self._gpio_det:
            for pwm_val in range(0,255,16):
                self._set_ref(pwm_val)
                sleep(0.25)
            self._set_ref(128)
            data.append(128+det_pin)
        return data