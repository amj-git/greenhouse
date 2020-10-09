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
        self._schedule=[]
        self._mode=['OFF']
        self._set_default_schedule()
        self._heat_state=0
        self._fan_state=0
        self._target=12
        self._boosttarget=20
        self._boost_minutes=60
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
        #Control the heater
        self._heat_state=state
        self._fan_state=state
        
        self._h_gpio.write(self._heat_pin,self._heat_state)
        #Control the Fan
        if self._fan_pin is not False:
            self._h_gpio.write(self.fan_pin,self._fan_state)            
    
    
    def _control_heater(self):
        
        #BOOST MODE - Set target to the boost target or drop out of boost
        if self._mode=='BOOST':
            if datetime.datetime.now() > self._boost_end_time:  #boost has expired
                self._mode=self._mode_before_boost
            else:
                self._target=self._boosttarget
            
        #AUTO MODE - Set target according to time of day schedule
        if self._mode=='AUTO':
            self._target=12   #Awaiting code
            
        #DECIDE THE HEATER STATE
        if self._mode=='OFF':
            self._set_heat_state(0)
        else:
            #Get the last temperature sensor reading
            data=None
            with self._iob.get_lock():
                n=len(self._source_buf)
                if n>0:
                    time,current_temp=self._source_buf[0]  #last reading
            
            if data is None:
                self._set_heat_state(0)   #problem with sensor - turn off heat
            else:  #Execute thermostat
                if current_temp < self._target:
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
        
    #Turns off every valve
    def _turn_off(self):
        self._h_gpio.write(self._heat_pin,0)
        if self._fan_pin is not False:
            self._h_gpio.write(self.fan_pin,0)
                    
    def _heartbeat(self,triggertime):
        if self._sim_hw:
            IO_Thread._heartbeat(self,triggertime)
        else:
            #control the heater
            self._control_heater()
            
            self._add_to_out_q('Heat',self._heat_state,triggertime)
            self._add_to_out_q('Target',self._target,triggertime)
            if self._fan_pin is not False:
                self._add_to_out_q('Fan',self._fan_state,triggertime)
            
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