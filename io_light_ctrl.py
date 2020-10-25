#Lighting controller (intended for controlling grow lights)
#lighting is assumed to have 0-10V control inputs


from io_thread import IO_Thread
import time
import datetime

try:
    import pigpio  
    _pigpio_ok=True
except ImportError:
    _pigpio_ok=False

class IO_Thread_Light_Ctrl(IO_Thread):
    def __init__(self,**kwargs):
        self._light_ctrl_pin=kwargs.get('light_ctrl_pin',18)
        self._target_tname=kwargs.get('target_tname',False)
        self._target_pname=kwargs.get('target_pname',False)
        
        self._schedule=[]
        self._mode='AUTO'
        self._set_default_schedule()
        self._light_state=0
        self._target_light=0
        self._boosttarget=100000
        self._boost_minutes=30
               
        
        IO_Thread.__init__(self,**kwargs)
        
    
    def _set_op_desc(self):
        self._op_desc['Target']={
              'pdesc':'Target',
              'ptype':'light',
              'pdatatype':'float',
              'pmin':0,
              'pmax':100000,
              'punits':'lx' }        
        self._op_desc['Brightness']={
              'pdesc':'light_level',
              'ptype':'light_level',
              'pdatatype':'float',
              'pmin':-10,
              'pmax':110,
              'punits':'%' }
          

    
    #Temperature, hour start, min start, hour stop, min stop
    def _set_default_schedule(self):
        self._add_to_schedule([0,00,00,7,00])
        self._add_to_schedule([5000,7,00,19,30])
        self._add_to_schedule([0,19,30,23,59])
        print("Lighting Control Schedule: ",self._schedule)
            
    #program_peg is [valve_index,start_h,start_m,stop_h,stop_m]
    #remember valve_index starts at 0
    def _add_to_schedule(self,program_peg):
        self._schedule.append(program_peg)
    
    def _set_light_state(self,val,deltamode):
        
        #if deltamode is true, apply a delta rather than absolute
        if deltamode:
            self._light_state=self._light_state+val
        else:
            self._light_state=val
        
        if(self._light_state>100):
            self._light_state=100       
        if(self._light_state<0):
            self._light_state=0
        
        #Write the new state to the HW
        if self._sim_hw:
            pass
        else:                      
            PWM_OFFSET=0
            PWM_SLOPE=(100-PWM_OFFSET)/100
            val_scaled=PWM_OFFSET+val*PWM_SLOPE
            if(val_scaled>100):
                val_scaled=100       
            if(val_scaled<0):
                val_scaled=0
            self._h_gpio.hardware_PWM(self._light_ctrl_pin,\
                                      self._pwm_freq,\
                                      round(val_scaled*10000))
        
                                
        
        
    def _get_scheduled_target(self):
        t_now=datetime.datetime.now()
        
        temp_target=0
        
        for peg in self._schedule:
            peg_start=t_now.replace(hour=peg[1],minute=peg[2],second=0,microsecond=0)
            peg_stop=t_now.replace(hour=peg[3],minute=peg[4],second=0,microsecond=0)
            if (t_now>peg_start) and (t_now<peg_stop):
                temp_target=peg[0]
                
        return temp_target
    
    def _control_lighting(self):
        
        #BOOST MODE - Set target to the boost target or drop out of boost
        if self._mode=='BOOST':
            if datetime.datetime.now() > self._boost_end_time:  #boost has expired
                self._mode=self._mode_before_boost
            else:
                self._target_light=self._boosttarget
            
        #AUTO MODE - Set target according to time of day schedule
        if self._mode=='AUTO':
            self._target_light=self._get_scheduled_target()
            
        #DECIDE THE LIGHT STATE
        if self._mode=='OFF':
            self._target_light=0  #set low value so it's obvious it's switched off
            self._set_light_state(0,False)
        else:
            #Get the last temperature sensor reading
            current_light=None
            with self._iob.get_lock():
                n=len(self._target_buf)
                if n>0:
                    time,current_light=self._target_buf[0]  #last reading
            
            if current_light is None:
                self._set_light_state(0,False)   #problem with sensor - turn off heat
            else:  #Execute integral controller
                #print ("mode: ",self._mode," target_light: ",self._target_light," current_light: ",current_light)
                deltalux=current_light-self._target_light
                deltabrightness=-deltalux*(0.5/100)
                MAXDELTABRIGHTNESS=15
                if deltabrightness>MAXDELTABRIGHTNESS:
                    deltabrightness=MAXDELTABRIGHTNESS
                if deltabrightness<-MAXDELTABRIGHTNESS:
                    deltabrightness=-MAXDELTABRIGHTNESS
                self._set_light_state(deltabrightness,True)
                   
                
    def _startup(self):
        IO_Thread._startup(self)
        
        if not self._sim_hw:
            #set up the PWM pin (must be a HW PWM pin)
            self._h_gpio.set_mode(self._light_ctrl_pin,pigpio.ALT5)  #set up PWM
            self._pwm_freq=500000  #500kHz        
            self._turn_off()
        
        #get the data source buffer - it is a deque
        #this has to be done in _startup as iob doesn't exist when
        #the constructor is called
        (n,self._target_buf)=self._iob.get_databuffer(self._target_tname,\
                                                  self._target_pname)
        
    #Turns off all outputs
    def _turn_off(self):
        self._set_light_state(0,False)
                    
    def _heartbeat(self,triggertime):
        
        #control the lighting
        self._control_lighting()
        
               
        self._add_to_out_q('Brightness',self._light_state,triggertime) 
        self._add_to_out_q('Target',self._target_light,triggertime)
        
    #process a command string
    def command(self,cmd,data):
        print("io_light_ctrl:command ",cmd,data)
        #HEATER:MODE <OFF|AUTO|BOOST> 
        if cmd=='LIGHT_CTRL:MODE':
            if data=='BOOST':
                if self._mode!='BOOST':
                    self._mode_before_boost=self._mode
                self._boost_end_time=datetime.datetime.now()+datetime.timedelta(minutes=self._boost_minutes)
            self._mode=data
            self._heartbeat(datetime.datetime.now()) #force an update
            response=None
            
        if cmd=='LIGHT_CTRL:MODE?':
            response=self._mode
            
        #HEATER:BOOST_PARAMS <Target Lux>,<Time in minutes> 
        if cmd=='LIGHT_CTRL:BOOST_PARAMS':
            d=data.split(',')
            self._boosttarget=float(d[0].strip())
            self._boost_minutes=float(d[1].strip())
            self._heartbeat(datetime.datetime.now()) #force an update
            response=None
            
        if cmd=='LIGHT_CTRL:BOOST_PARAMS?':
            response=(self._boosttarget,self._boost_minutes,self._boost_end_time)    
            
        return response            
        
    def _shutdown(self):
        if not self._sim_hw:
            self._turn_off()
        IO_Thread._shutdown(self)
#END class IO_Thread_Moist------------------------------------------------    