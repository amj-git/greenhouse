#One Wire temp sensor interface

from datetime import datetime
from datetime import timedelta


w1_dir = '/sys/bus/w1/devices/'

use_w1_reset=False   #Set True to use the power cycling mechanism
                    #This is only necessary if using bit-bashed one-wire
sw_5v_pin=22        #This pin sets the 5V power for the temperature sensors on / off
                    #it is used to reset misbehaving sensors (particularly DB18B20's)



last_w1_reset_time=datetime.now()

def w1_read_temp_raw(fname):
    try:
        f = open(fname, 'r')
    except IOError:
        return(None)
    lines = f.readlines()
    f.close()
    return lines

def w1_read_temp(addr,h_gpio):
    fname=w1_dir + addr +'/w1_slave'
    lines = w1_read_temp_raw(fname)
    if(lines==None):
        print("Device File Not Found "+fname)
        w1_reset(h_gpio)
        return(None,None)
    retry_counter=0
    while lines[0].strip()[-3:] != 'YES':
        print(lines)
        time.sleep(0.2)
        lines = w1_read_temp_raw(fname)
        retry_counter=retry_counter+1
        if(lines==None):
            print("Device File Not Found")
            w1_reset(h_gpio)
            return(None,None)
        if(retry_counter>4):
            print("4 bad checksums in a row")
            w1_reset(h_gpio)
            return(None,None)
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        temp_f = temp_c * 9.0 / 5.0 + 32.0
        return temp_c, temp_f
   
#this function cycles the temperature sensor power in an attempt to recover from sensors locking up
#it is only allowed to happen once every 15 minutes
def w1_reset(h_gpio):
    global last_w1_reset_time
    if use_w1_reset:
        print("w1_reset: Called")
        mytime=datetime.now()                   
        diff=datetime.now()-last_w1_reset_time
        if (diff>timedelta(minutes=15)):
            last_w1_reset_time=datetime.now()
            h_gpio.write(sw_5v_pin,0)  #turn off the power and wait 10 secs
            print("w1_reset: POWER OFF")
            sleep(10) 
            h_gpio.write(sw_5v_pin,1)  #turn on the power
            print("w1_reset: POWER ON")
        else:
            print("w1_reset: Skipping")