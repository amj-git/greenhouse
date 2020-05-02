'''
io_thread.py

Routines for reading and writing to hardware.

Each read/write subsystem is contained in a separate thread.
All threads are based on the base class IO_Thread

The IO_Threads are managed by IO_Thread_Manager 

Each IO output parameter is described by a dictionary with the
following entries:-
'pname'=name of the parameter
'pdesc'=description of the parameter
'ptype'=type of parameter - can be 'float', 'int', 'bool', 'string'
'pmin'=min value of parameter
'pmax'=max value of the parameter
'punits'=A string containing the units of the parameter (e.g. 'deg C')

IO_Thread.get_op_desc() returns an array of the above description dictionaries

The actual output data is pushed to the specified queue on the heartbeat.
The format of the data is a dictionary as follows
'tname'=name of the originating IO_Thread
'time'=time of data
'<param1>'=value of param 1
'<param2>'=value of param 2
etc

The various HW support is included by deriving classes from IO_Thread
these implement _startup(), _heartbeat(), _shutdown(), _set_op_desc()
The _heartbeat() function adds data to the output queue

'''

import signal
import time
import threading
import os
import sys
import glob

import pigpio  #we use pigpio for the DHT22s.  The ADAFruit library is unreliable.
                #note you have to start the pigpio demon first before running
#import DHT22
from time import sleep
from datetime import datetime, timedelta
from threading import Thread
from random import seed,random
import queue
from io_w1 import sw_5v_pin, w1_read_temp

seed(1)

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
        self._threadname=kwargs.get('threadname','Unnamed Thread')
        self._op_desc=[]
        self._set_op_desc() #set the parameter descriptions
        
    def term(self):
        self.__running=False
        
    def __del__(self):
        #add any tidy-up here
        pass
    
    def run(self):
        
        self._startup()
        while(self.__running):
            lasttime=datetime.now()
            self._heartbeat(lasttime)
            if not self.__running: #speed up shutdown
                break
            delta=(datetime.now()-lasttime).total_seconds()
            sleep_time=self._period-delta
            if(sleep_time<0):
                sleep_time=0
            sleep(sleep_time)
        self._shutdown()
        print("IO_Thread: "+self._threadname+" Stopped")
        
    '''_startup
    Things to do before starting the heartbeat - override as necessary
    '''
    def _startup(self):
        if self._sim_hw:
            print("IO_Thread: "+self._threadname+" _startup()")
            
    '''_heartbeat
    This is called periodically
    triggertime is the time at the start of the heartbeat
    '''
    def _heartbeat(self,triggertime):
        if self._sim_hw:
            #print("IO_Thread: "+self._threadname+" _heartbeat()")
            
            op_data=dict()
            op_data['tname']=self._threadname
            op_data['time']=triggertime
            
            #generate random values for each parameter
            for param in self._op_desc:
                min=param['pmin'];
                max=param['pmax'];
                val=min+(max-min)*random()  #random between min and max
                op_data[param['pname']]=val
            
            try:
                self._out_q.put(op_data,block=False)
            except queue.Full:  #consumer must have stopped - throw data away
                print("IO_Thread: "+self._threadname+" _heartbeat(): Unable to output data - Queue is full")
            
    '''_shutdown
    Things to do to clear up before stopping
    '''
    def _shutdown(self):
        if self._sim_hw:
            print("IO_Thread: "+self._threadname+" _shutdown()")
    
    '''__set_op_desc
    Override this to set the descriptions
    Follow the format of the simulated example
    '''
    def _set_op_desc(self):
        if self._sim_hw:
            #for sim HW, make a temperature and humidity params
            self._op_desc.append({
              'pname':'Temp',
              'pdesc':'Temperature',
              'ptype':'float',
              'pmin':-10,
              'pmax':40,
              'punits':'deg C'
            })
            self._op_desc.append({
              'pname':'Humid',
              'pdesc':'Humidity',
              'ptype':'float',
              'pmin':0,
              'pmax':100,
              'punits':'%'
            })
                 
    '''get_op_desc
    
    '''
    def get_op_desc(self):
        return self._op_desc
        
    def set_pigpio(self,h_gpio):  
        self._h_gpio=h_gpio  
        
    def get_threadname(self):
        return self._threadname
    
        
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
'''DS18B20 Temperature Sensors
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
        self._op_desc.append({
              'pname':'Temp',
              'pdesc':'Temperature',
              'ptype':'float',
              'pmin':-10,
              'pmax':40,
              'punits':'deg C'
            })
        
    def _startup(self):
        IO_Thread._startup(self)
        
    def _heartbeat(self,triggertime):
        if self._sim_hw:
            IO_Thread._heartbeat(self,triggertime)
        else:
            temp_c,temp_f=w1_read_temp(self._addr,self._h_gpio)
            #print("IO_Thread: "+self._threadname+" _heartbeat() temp_c=",temp_c)
            
            op_data=dict()
            op_data['tname']=self._threadname
            op_data['time']=triggertime
            op_data[self._op_desc[0]['pname']]=temp_c
            
            try:
                self._out_q.put(op_data,block=False)
            except queue.Full:  #consumer must have stopped - throw data away
                print("IO_Thread: "+self._threadname+" _heartbeat(): Unable to output data - Queue is full")
        
    def _shutdown(self):
        IO_Thread._shutdown(self)
#END class IO_Thread_ExampleIO------------------------------------------------    

      
#START class IO_Thread_Manager------------------------------------------------      
class IO_Thread_Manager:
    '''init
    #sim_hw =   True to work without HW and generate simulated data
                False to run normally with HW
    '''
    def __init__(self,sim_hw):
        self._threads=[]
        self._sim_hw=sim_hw
        self.start_pigpio();    
            
    def __del__(self):
        self.stop_pigpio()
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
                    
                    
    def start_threads(self):
        for t in self._threads:
            t.set_pigpio(self._h_gpio)
            t.start()
            
    def start_pigpio(self):
        if not self._sim_hw:
            self._h_gpio=pigpio.pi()
            self._h_gpio.set_mode( sw_5v_pin, pigpio.OUTPUT)  #5V control pin
            self._h_gpio.write(sw_5v_pin,1)  #turn on the temp sensor power
        
    def stop_pigpio(self):
        if not self._sim_hw:
            self._h_gpio.stop()
            
    def print_descriptions(self):
        for t in self._threads:
            print(t.get_threadname(),' io_desc:',t.get_op_desc())
        
        
#END class IO_Thread_Manager------------------------------------------------        
    
        