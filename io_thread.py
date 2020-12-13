'''
io_thread.py

Routines for reading and writing to hardware.

Each read/write subsystem is contained in a separate thread.
All threads are based on the base class IO_Thread

The IO_Threads are managed by IO_Thread_Manager 

Each IO output parameter is described by a dictionary with the
following entries:-
'pdesc'=description of the parameter
'ptype'=type of parameter  
'pdatatype'=datatype of parameter - can be 'float', 'int', 'bool', 'string'
'pmin'=min value of parameter
'pmax'=max value of the parameter
'punits'=A string containing the units of the parameter (e.g. 'deg C')
'tname'=The name of the thread.  This is included for convenience

IO_Thread.get_op_desc() returns an dictionary of the above description dictionaries
The key of this dictionary is the name of the parameter.

So for example IO_Thread.get_op_desc()['Temp']['ptype'] will return the type
of the output parameter named 'Temp'

ptype can be used by the GUI to decide what to do with the data, what icons to
use etc.  It saves looking at the thread type.  Here are the options:-
temp - temperature reading
humid - humidity level reading
light - light level reading
moist - moisture level reading
windowsw - window switch status
doorsw - door switch status
heater - heater state
fan - fan state
sprinkler - sprinkler state
winpos - window opener position


The actual output data is pushed to the specified queue on the heartbeat.
The format of the data is a dictionary as follows
'tname'=name of the originating IO_Thread
'time'=time of data
'pname'=parameter name matching the descriptions above
'data'=value of parameter

etc

The various HW support is included by deriving classes from IO_Thread
these implement _startup(), _heartbeat(), _shutdown(), _set_op_desc()
The _heartbeat() function adds data to the output queue

'''
try:
    import pigpio  #we use pigpio for the DHT22s.  The ADAFruit library is unreliable.
                    #note you have to start the pigpio demon first before running
    _pigpio_ok=True
except ImportError:
    _pigpio_ok=False

import signal
import time
import threading
import os
import sys
import glob
from time import sleep
from datetime import datetime, timedelta
from threading import Thread
from random import seed,random
import queue
from io_buffer import IO_Buffer

from io_w1 import sw_5v_pin, w1_read_temp
from io_bh1750 import io_bh1750, BH1750_DEFAULT
import io_dht22
from process_control import pr_cont
import io_moist

#START class IO_Thread------------------------------------------------
class IO_Thread(Thread):

    '''init
    out_q     =   queue for output data
    sim_hw    =   True to work without HW and generate simulated data
                  False to run normally with HW
    period    =   Thread Heartbeat period in seconds.  heartbeat() is called
                  based on this.
    threadname =  String to identify the thread
    '''
    def __init__(self,**kwargs):
        Thread.__init__(self)
        self.daemon=True
        self.__running=True
        self._out_q=kwargs.get('out_q',0)
        self._sim_hw=kwargs.get('sim_hw',False)
        self._period=kwargs.get('period',10)
        self._has_master=False
        self._slave_thread=kwargs.get('slave_thread',None)  #another thread's heartbeat can be triggered if you set this to another IOThread object
        self._threadname=kwargs.get('threadname','Unnamed Thread')
        self._op_desc=dict()
        self._set_op_desc() #set the parameter descriptions
        
    def term(self):
        self.__running=False
        
    def __del__(self):
        #add any tidy-up here
        pass
    
    #manual heartbeat trigger.  This is used by a master thread to trigger a slave - used in controllers
    def trigger_heartbeat(self,lasttime):
        self._has_master=True
        self._heartbeat(lasttime)
    
    def run(self):
        pr_cont.set_name(self._threadname) #allows process to be idenfified in htop
        self._startup()
        while(self.__running):
            lasttime=datetime.now()
            if self._slave_thread is not None:  #trigger slaves first so data can be used right away
                self._slave_thread.trigger_heartbeat(lasttime)
            if not self._has_master:  #trigger the heartbeat unless I'm a slave
                self._heartbeat(lasttime)
            if not self.__running: #speed up shutdown
                break
            endtime=datetime.now()
            delta=(endtime-lasttime).total_seconds()
            sleep_time=self._period-delta
            if(sleep_time<0):
                sleep_time=0
            sleep(sleep_time)
        self._shutdown()
        print("IO_Thread: "+self._threadname+" Stopped")
        
    def set_iob(self,iob):
        self._iob=iob    
    
    '''_startup
    Things to do before starting the heartbeat - override as necessary
    '''
    def _startup(self):
        if self._sim_hw:
            #print("IO_Thread: "+self._threadname+" _startup()")
            pass
            
    '''_heartbeat
    This is called periodically
    triggertime is the time at the start of the heartbeat
    '''
    def _heartbeat(self,triggertime):
        if self._sim_hw:
            #print("IO_Thread: "+self._threadname+" _heartbeat()")
                                 
            #generate random values for each parameter
            for pname in self._op_desc:
                min=self._op_desc[pname]['pmin'];
                max=self._op_desc[pname]['pmax'];
                val=min+(max-min)*random()  #random between min and max    
                self._add_to_out_q(pname,val,triggertime)
                
            
    '''_shutdown
    Things to do to clear up before stopping
    '''
    def _shutdown(self):
        if self._sim_hw:
            #print("IO_Thread: "+self._threadname+" _shutdown()")
            pass
    
    '''__set_op_desc
    Override this to set the descriptions
    Follow the format of the simulated example
    '''
    def _set_op_desc(self):
        if self._sim_hw:
            #for sim HW, make a temperature and humidity params
            self._op_desc['Temp']={
              'pdesc':'Temperature',
              'ptype':'temp',
              'pdatatype':'float',
              'pmin':-10,
              'pmax':40,
              'punits':u'\xb0C' }
            self._op_desc['Humid']={
              'pdesc':'Humidity',
              'ptype':'humid',
              'pdatatype':'float',
              'pmin':0,
              'pmax':100,
              'punits':'%'}
            
                 
    '''get_op_desc
    
    '''
    def get_op_desc(self):
        return self._op_desc
        
    def set_pigpio(self,h_gpio):  
        self._h_gpio=h_gpio  
        
    def get_threadname(self):
        return self._threadname
    
    #adds the dictionary op_data to the queue, tagging on the standard extras
    def _add_to_out_q(self,pname,data,triggertime):
        op_data=dict()
        op_data['tname']=self._threadname
        op_data['time']=triggertime
        op_data['pname']=pname
        op_data['data']=data
        try:
            self._out_q.put(op_data,block=False)
        except queue.Full:  #consumer must have stopped - throw data away
            print("IO_Thread: "+self._threadname+" _heartbeat(): Unable to output data - Queue is full")
    
        
#END class IO_Thread------------------------------------------------        
    
#BEGIN class IO_Thread_ExampleIO------------------------------------------------
'''Template for derived IO types
   You must implement the functions below, optionally calling the parent functions
'''
class IO_Thread_ExampleIO(IO_Thread):
    def __init__(self,**kwargs):
        IO_Thread.__init__(self,**kwargs)
    
    def _set_op_desc(self):
        IO_Thread._set_op_desc(self)
    
    def _startup(self):
        IO_Thread._startup(self)
        
    def _heartbeat(self,triggertime):
        IO_Thread._heartbeat(self,triggertime)
        
    def _shutdown(self):
        IO_Thread._shutdown(self)
#END class IO_Thread_ExampleIO------------------------------------------------    

#BEGIN class IO_Thread_DS18B20------------------------------------------------
'''DS18B20 One-Wire Temperature Sensors
We assume these are appearing in /sys/bus/w1/devices
The RPI w1 interface can be used but it is terribly unreliable
It is recommended to instead use a ds2482 interface chip on I2C
Both interfaces save data to the same IO file, so it doesn't matter
to this class    
'''
class IO_Thread_DS18B20(IO_Thread):
    def __init__(self,**kwargs):
        IO_Thread.__init__(self,**kwargs)
        self._addr=kwargs.get('addr',False)
    
    def _set_op_desc(self):        
        self._op_desc['Temp']={
              'pdesc':'Temperature',
              'ptype':'temp',
              'pdatatype':'float',
              'pmin':-10,
              'pmax':40,
              'punits':u'\xb0C'}   #degree symbol is u'\xb0'
        
    def _startup(self):
        IO_Thread._startup(self)
        
    def _heartbeat(self,triggertime):
        if self._sim_hw:
            IO_Thread._heartbeat(self,triggertime)
        else:
            temp_c,temp_f=w1_read_temp(self._addr,self._h_gpio)
            #print("IO_Thread: "+self._threadname+" _heartbeat() temp_c=",temp_c)
            op_data=dict()
            if temp_c is not None:
                self._add_to_out_q('Temp',temp_c,triggertime)
            
    def _shutdown(self):
        IO_Thread._shutdown(self)
#END class IO_Thread_DS18B20------------------------------------------------    


#BEGIN class IO_Thread_BH1750------------------------------------------------
'''BH1750 Light Sensors
    addr=i2c bus address
  See the file io_bh1750
'''
class IO_Thread_BH1750(IO_Thread):
    def __init__(self,**kwargs):
        IO_Thread.__init__(self,**kwargs)
        self._addr=kwargs.get('addr',BH1750_DEFAULT)
    
    def _set_op_desc(self):        
        self._op_desc['Light']={
              'pdesc':'Light Illuminance',
              'ptype':'light',
              'pdatatype':'float',
              'pmin':0,
              'pmax':100000,
              'punits':'lx'}
                
    def _startup(self):
        IO_Thread._startup(self)
        if not self._sim_hw:
            self._l_sensor=io_bh1750(self._addr)
        
    def _heartbeat(self,triggertime):
        if self._sim_hw:
            IO_Thread._heartbeat(self,triggertime)
        else:
            light=self._l_sensor.read()
            #print("IO_Thread: "+self._threadname+" _heartbeat() light=",light)
            if light!=-999:
                self._add_to_out_q('Light',light,triggertime)
            else:
                print(self._threadname+" BH1750 Sensor: Read Error")
        
    def _shutdown(self):
        if not self._sim_hw:
            del self._l_sensor
        IO_Thread._shutdown(self)
                
#END class IO_Thread_BH1750------------------------------------------------    

#BEGIN class IO_Thread_DHT22------------------------------------------------
'''DHT22 Temperature/Humidity Sensors
'''
class IO_Thread_DHT22(IO_Thread):
    def __init__(self,**kwargs):
        IO_Thread.__init__(self,**kwargs)
        self._pin=kwargs.get('pin',False)
    
    def _set_op_desc(self):        
        self._op_desc['Temp']={
              'pdesc':'Temperature',
              'ptype':'temp',
              'pdatatype':'float',
              'pmin':-10,
              'pmax':40,
              'punits':u'\xb0C' }
        self._op_desc['Humid']={
              'pdesc':'Humidity',
              'ptype':'humid',
              'ptype':'float',
              'pmin':0,
              'pmax':100,
              'punits':'%' }
                
    def _startup(self):
        IO_Thread._startup(self)
        if not self._sim_hw:
            self._dht_obj=io_dht22.sensor(self._h_gpio, self._pin)
        
    def _heartbeat(self,triggertime):
        if self._sim_hw:
            IO_Thread._heartbeat(self,triggertime)
        else:
            self._dht_obj.trigger()
            sleep(0.2)
            humid=self._dht_obj.humidity()
            temp_c=self._dht_obj.temperature()
            
            #print("IO_Thread: "+self._threadname+" _heartbeat() temp_c=",temp_c," humid=",humid)  
            if (temp_c!=-999) and (humid !=-999):
                self._add_to_out_q('Temp',temp_c,triggertime)
                self._add_to_out_q('Humid',humid,triggertime)
            else:
                print(self._threadname+" DHT22 Sensor: Read Error")
        
    def _shutdown(self):
        if not self._sim_hw:
            del self._dht_obj
        IO_Thread._shutdown(self)
#END class IO_Thread_DHT22------------------------------------------------    

#BEGIN class IO_Thread_Moist------------------------------------------------
'''Moisture Sensors
'''
class IO_Thread_Moist(IO_Thread):
    def __init__(self,**kwargs):
        self._ref_pin=kwargs.get('ref_pin',False)
        self._det_pins=kwargs.get('det_pins',False)
        IO_Thread.__init__(self,**kwargs)
    
    #get the parameter name associated with the kth sensor
    #k starts at 0
    def _get_pname(self,k):
        return '%d' % (k+1)
    
    def _set_op_desc(self):
        for k,det_pin in enumerate(self._det_pins):
            #print ('IO_Thread_Moist._set_op_desc: k=',k,'det_pin=',det_pin)
            pname=self._get_pname(k)
            self._op_desc[pname]={
                  'pdesc':'Moisture',
                  'ptype':'moist',
                  'pdatatype':'float',
                  'pmin':0,
                  'pmax':100,
                  'punits':'%' }
                
    def _startup(self):
        IO_Thread._startup(self)
        if not self._sim_hw:
            self._moist_obj=io_moist.sensor(self._h_gpio, self._ref_pin, self._det_pins)
        
    def _heartbeat(self,triggertime):
        if self._sim_hw:
            IO_Thread._heartbeat(self,triggertime)
        else:
            moist_data=self._moist_obj.read()
            
            for k,m in enumerate(moist_data): 
                pname=self._get_pname(k)
                self._add_to_out_q(pname,m,triggertime)
        
    def _shutdown(self):
        if not self._sim_hw:
            del self._moist_obj
        IO_Thread._shutdown(self)
#END class IO_Thread_Moist------------------------------------------------    


#BEGIN class IO_Thread_ExampleController------------------------------------------------
'''Demo of how to read and react to data from other threads
This example just repeats the last data from a given thread and parameter
It shows how to lock the data to prevent it changing during the read.
source_tname, source_pname determine the data source
'''
class IO_Thread_ExampleController(IO_Thread):
    def __init__(self,**kwargs):
        IO_Thread.__init__(self,**kwargs)
        self._source_tname=kwargs.get('source_tname',False)
        self._source_pname=kwargs.get('source_pname',False)
    
    def _set_op_desc(self):        
        self._op_desc['Data']={
              'pdesc':'unknown',   #can't find this info with current design
              'ptype':'unknown',
              'pdatatype':'float',
              'pmin':-10,
              'pmax':40,
              'punits':'unknown' }
                
    def _startup(self):
        #get the data source buffer - it is a deque
        #this has to be done in _startup as iob doesn't exist when
        #the constructor is called
        (n,self._source_buf)=self._iob.get_databuffer(self._source_tname,\
                                                  self._source_pname)
        
    def _heartbeat(self,triggertime):
        #lock the buffer before reading
        #Note this isn't super-efficient as it locks the whole buffer
        #for all threads
        data=None
        with self._iob.get_lock():
            n=len(self._source_buf)
            if n>0:
                time,data=self._source_buf[0]  #last reading
        
        #print("IO_Thread: "+self._threadname+" _heartbeat() data=",data)  
        if data is not None:
            self._add_to_out_q('Data',data,triggertime)
                
    def _shutdown(self):
        IO_Thread._shutdown(self)
#END class IO_Thread_ExampleController------------------------------------------------    



      
#START class IO_Thread_Manager------------------------------------------------      
class IO_Thread_Manager:
    '''init
    #sim_hw =   True to work without HW and generate simulated data
                False to run normally with HW
    '''
    def __init__(self,sim_hw):
        self._threads=[]
        self._sim_hw=sim_hw
        self._start_pigpio()
        seed(1)    #for random number gen
            
    def __del__(self):
        self._stop_pigpio()
        pass
            
    def kill_threads(self):
        print("IO_Thread_Manager: kill_threads")
        for t in self._threads:
            t.term() #tell all threads to stop
        for t in self._threads:
            t.join() #wait for it to finish
            del t
        print("IO_Thread_Manager: All IO_Threads Stopped")
    
    '''add_thread
    #t =  Instance of IO_Thread (or object derived from it) to add
    '''    
    def add_thread(self,t):
        self._threads.append(t)
                    
    '''
        Start all the threads
        At this point we can add an io buffer, iob
    '''             
    def start_threads(self):
        self._iob=IO_Buffer(self.get_all_op_descriptions(),10)
        for t in self._threads:
            t.set_iob(self._iob)
            if not self._sim_hw:
                t.set_pigpio(self._h_gpio)
            t.start()
            
    def get_iob(self):
        return self._iob
            
    def _start_pigpio(self):
        if not self._sim_hw and _pigpio_ok:            
            self._h_gpio=pigpio.pi()
            self._h_gpio.set_mode( sw_5v_pin, pigpio.OUTPUT)  #5V control pin
            self._h_gpio.write(sw_5v_pin,1)  #turn on the temp sensor power
        
    def _stop_pigpio(self):
        if not self._sim_hw and _pigpio_ok:
            self._h_gpio.stop()
                  
    '''all_op_desc=get_all_op_descriptions()
    This function returns a data structure which can be used to get the
    description of any thread output parameter as follows:-
    all_op_desc[<thread name>][<param name>]
    '''     
    def get_all_op_descriptions(self):
        all_op_desc=dict()
        for t in self._threads:
            all_op_desc[t.get_threadname()]=t.get_op_desc()
        return all_op_desc
        
#END class IO_Thread_Manager------------------------------------------------        
    
        