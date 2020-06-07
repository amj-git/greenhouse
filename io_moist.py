#Moisture Sensor Reader

import time

try:
    import pigpio  
    _pigpio_ok=True
except ImportError:
    _pigpio_ok=False
from time import sleep

HW_PWM_PINS=[12,13,18,19]  #HW PWM only available on these pins

class sensor:
    
    '''A class to read moisture sensors
        pi=handle to pigpio
        gpio_ref=pin number of reference pin. This pin generates PWM
             which goes to all comparators
        gpio_det[]=array of pin numbers for comparator outputs 
    '''
    
    def __init__(self, h_gpio, gpio_ref, gpio_det):
        self._h_gpio = h_gpio
        self._gpio_ref = gpio_ref
        self._gpio_det = gpio_det
      
        #use HW PWM if supported by the selected pin
        if self._gpio_ref in HW_PWM_PINS:
            self._hw_pwm=True
        else:
            self._hw_pwm=False
            
        #Set up the REF pin
        if self._hw_pwm:
            #HW PWM
            self._h_gpio.set_mode(self._gpio_ref,pigpio.ALT5)  #set up PWM on REF pin
            self._pwm_freq=500000  #500kHz
        else:
            #SW PWM
            self._h_gpio.set_mode(self._gpio_ref,pigpio.OUTPUT)  #set up PWM on REF pin
            self._h_gpio.set_PWM_range(self._gpio_ref,100)
            self._h_gpio.set_PWM_frequency(self._gpio_ref,100000) #set highest freq
            self._pwm_freq=(self._h_gpio.get_PWM_frequency(self._gpio_ref)) #should get 8kHz
        
        self._set_ref(50)  #set the output to 50% initially
      
        #set the input (DET) pins
        for det_pin in self._gpio_det:
            self._h_gpio.set_mode(det_pin,pigpio.INPUT)
            
    def _set_ref(self,val):
        '''Accepts values of 0 to 100
        '''
        if self._hw_pwm:
            self._h_gpio.hardware_PWM(self._gpio_ref,\
                                      self._pwm_freq,\
                                      round(val*10000))
        else:
            self._h_gpio.set_PWM_dutycycle(self._gpio_ref,val)
        
    def read(self):
        data=[]
        for det_pin in self._gpio_det:
            for pwm_val in range(0,100,5):
                self._set_ref(pwm_val)
                sleep(1/20)
            self._set_ref(50)
            data.append(50+det_pin)
        return data