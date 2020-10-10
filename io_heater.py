#Heater controller
#The heater can have separate heat and fan controls.
#Fan is optional.  Don't set fan_pin if you don't want it.


from io_thread import IO_Thread
import time
import datetime

try:
    import pigpio  
    _pigpio_ok=True
except ImportError:
    _pigpio_ok=False

class IO_Thread_Heater(IO_Thread):
    def __init__(self,**kwargs):
        self._heat_pin=kwargs.get('heat_pin',False)
        self._fan_pin=kwargs.get('fan_pin',False)
        self._target_tname=kwargs.get('target_tname',False)
        self._target_pname=kwargs.get('target_pname',False)
        self._fan_overrun=kwargs.get('fan_overrun',3*60)  #fan overrun time in seconds
        self._min_heat_on_time=kwargs.get('min_on_time',3*60)  
        self._min_heat_off_time=kwargs.get('min_off_time',3*60)  
        self._max_heat_on_time=kwargs.get('max_on_time',60*60)  
        self._fan_prestart=kwargs.get('fan_prestart',10)  #fan prestart time in seconds
        self._schedule=[]
        self._mode='OFF'
        self._set_default_schedule()
        self._heat_state=0
        self._fan_state=0
        self._target_temp=12
        self._boosttarget=20
        self._boost_minutes=60
        self._reset_heat_timers()
        IO_Thread.__init__(self,**kwargs)
        
    
    def _set_op_desc(self):
        self._op_desc['Target']={
              'pdesc':'Target',
              'ptype':'temp',
              'pdatatype':'float',
              'pmin':-10,
              'pmax':40,
              'punits':u'\xb0C' }        
        self._op_desc['Heat']={
              'pdesc':'Heater',
              'ptype':'heat_level',
              'pdatatype':'float',
              'pmin':-10,
              'pmax':110,
              'punits':'%' }
        
        if self._fan_pin is not False:
            self._op_desc['Fan']={
                  'pdesc':'Fan',
                  'ptype':'fan_level',
                  'pdatatype':'float',
                  'pmin':-10,
                  'pmax':110,
                  'punits':'%' }            

    
    def _set_default_schedule(self):
        self._add_to_schedule([0,20,0,20,20])
        self._add_to_schedule([1,19,15,19,35])
        self._add_to_schedule([0,13,30,13,40])
        #self._add_to_schedule([0,21,30,21,32])
        print("Heater Schedule: ",self._schedule)
            
    #program_peg is [valve_index,start_h,start_m,stop_h,stop_m]
    #remember valve_index starts at 0
    def _add_to_schedule(self,program_peg):
        self._schedule.append(program_peg)
                            
    
    def _set_heat_state(self,state):
        #Determine Fan state
        old_fan_state=self._fan_state
        
        if self._fan_pin is not False:
            if state==1:  #if demand is high, start the fan
                self._fan_state=1
            else:         #stop the fan only if the overrun timer has expired (both on heater and fan)
                if datetime.datetime.now() > self._last_heat_on_time+datetime.timedelta(seconds=self._fan_overrun):
                    if datetime.datetime.now() > self._last_fan_on_time+datetime.timedelta(seconds=self._fan_overrun):
                        self._fan_state=0
                else:
                    self._fan_state=1
        
        #record time of turning on fan for use later
        if self._fan_state==1:
            if old_fan_state==0:
                self._last_fan_on_time=datetime.datetime.now()
        
        old_heat_state=self._heat_state
        new_heat_state=old_heat_state #default to no change        
                
        #Determine the new Heater state    
        if state==1:
            if old_heat_state==0:
                #check it's been off for long enough before turning it on 
                if datetime.datetime.now() > self._last_heat_off_time+datetime.timedelta(seconds=self._min_heat_off_time):   
                    #check the fan has been on for long enough before turning on
                    if self._fan_pin is not False:
                        if datetime.datetime.now() > self._last_fan_on_time+datetime.timedelta(seconds=self._fan_prestart):
                            new_heat_state=1
                    else:
                        new_heat_state=1
            if old_heat_state==1:
                #Turn off if it's been on too long
                if datetime.datetime.now() > self._last_heat_on_time+datetime.timedelta(seconds=self._max_heat_on_time):
                    print ("Warning: Heater has been on continually for a long time.")
                    new_heat_state=0
        else:  #state==0
            if old_heat_state==0:
                #it's off, so no action
                pass
            if old_heat_state==1:
                #check it's been on for long enough before turning off 
                if datetime.datetime.now() > self._last_heat_on_time+datetime.timedelta(seconds=self._min_heat_on_time):
                    new_heat_state=0
        
        #Log the times of any changes to the heat state
        if new_heat_state==old_heat_state:
            pass
        else:  #heat state changed
            if new_heat_state==1:
                self._last_heat_on_time=datetime.datetime.now()
            if new_heat_state==0:
                self._last_heat_off_time=datetime.datetime.now()
        
        #set the new heat state
        self._heat_state=new_heat_state
        
        #Write the new state to the HW
        if self._sim_hw:
            pass
        else:                      
            if self._fan_pin is not False:
                self._h_gpio.write(self.fan_pin,self._fan_state)
            self._h_gpio.write(self._heat_pin,self._heat_state)            
        
    #expires all the timers so the state machine starts from fresh
    def _reset_heat_timers(self):
        old_time=datetime.datetime.now()-datetime.timedelta(days=7)
        self._last_heat_on_time=old_time
        self._last_heat_off_time=old_time
        self._last_fan_on_time=old_time
    
    def _control_heater(self):
        
        #BOOST MODE - Set target to the boost target or drop out of boost
        if self._mode=='BOOST':
            if datetime.datetime.now() > self._boost_end_time:  #boost has expired
                self._mode=self._mode_before_boost
            else:
                self._target_temp=self._boosttarget
            
        #AUTO MODE - Set target according to time of day schedule
        if self._mode=='AUTO':
            self._target_temp=12   #Awaiting code
            
        #DECIDE THE HEATER STATE
        if self._mode=='OFF':
            self._set_heat_state(0)
        else:
            #Get the last temperature sensor reading
            current_temp=None
            with self._iob.get_lock():
                n=len(self._target_buf)
                if n>0:
                    time,current_temp=self._target_buf[0]  #last reading
            
            if current_temp is None:
                self._set_heat_state(0)   #problem with sensor - turn off heat
            else:  #Execute thermostat
                #print ("mode: ",self._mode," target_temp: ",self._target_temp," current_temp: ",current_temp)
                if (current_temp < self._target_temp):
                    self._set_heat_state(1)
                else:
                    self._set_heat_state(0)
                   
                
    def _startup(self):
        IO_Thread._startup(self)
        if not self._sim_hw:
            self._h_gpio.set_mode(self._heat_pin,pigpio.OUTPUT)
            if self._fan_pin is not False:
                self._h_gpio.set_mode(self._fan_pin,pigpio.OUTPUT)
            self._turn_off()
        
        #get the data source buffer - it is a deque
        #this has to be done in _startup as iob doesn't exist when
        #the constructor is called
        (n,self._target_buf)=self._iob.get_databuffer(self._target_tname,\
                                                  self._target_pname)
        
    #Turns off all heater outputs
    def _turn_off(self):
        self._h_gpio.write(self._heat_pin,0)
        if self._fan_pin is not False:
            self._h_gpio.write(self.fan_pin,0)
                    
    def _heartbeat(self,triggertime):
        
        #control the heater
        self._control_heater()
        
               
        self._add_to_out_q('Heat',self._heat_state*100,triggertime) #return as percentage
        self._add_to_out_q('Target',self._target_temp,triggertime)
        if self._fan_pin is not False:
            self._add_to_out_q('Fan',self._fan_state*100,triggertime) #return as percentage
        
    #process a command string
    def command(self,cmd,data):
        print("io_heater:command ",cmd,data)
        #HEATER:MODE <OFF|AUTO|BOOST> 
        if cmd=='HEATER:MODE':
            if data=='BOOST':
                if self._mode!='BOOST':
                    self._mode_before_boost=self._mode
                self._boost_end_time=datetime.datetime.now()+datetime.timedelta(minutes=self._boost_minutes)
            self._mode=data
            self._heartbeat(datetime.datetime.now()) #force an update
            response=None
            
        if cmd=='HEATER:MODE?':
            response=self._mode
            
        #HEATER:BOOST_PARAMS <Target Temperature>,<Time in minutes> 
        if cmd=='HEATER:BOOST_PARAMS':
            d=data.split(',')
            self._boosttarget=float(d[0].strip())
            self._boost_minutes=float(d[1].strip())
            self._heartbeat(datetime.datetime.now()) #force an update
            response=None
            
        if cmd=='HEATER:BOOST_PARAMS?':
            response=(self._boosttarget,self._boost_minutes,self._boost_end_time)    
            
        return response            
        
    def _shutdown(self):
        if not self._sim_hw:
            self._turn_off()
        IO_Thread._shutdown(self)
#END class IO_Thread_Moist------------------------------------------------    