#Lighting controller (intended for controlling grow lights)
#An interface circuit converts the PWM average DC value to a 0-10V signal for
#control of LED growlights


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
        self._light_state_actual=0
        self._target_light=0
        self._boosttarget=100000
        self._boost_minutes=30
        self._hw_pwm=False   #use SW PWM due to PWM channel conflict with GPIO12 which is used by moisture sensor
               
        
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
          

    
    #Target, hour start, min start, hour stop, min stop
    def _set_default_schedule(self):
        
        self._add_to_schedule([2000,6,0,7,0])
        self._add_to_schedule([4000,7,0,8,0])
        self._add_to_schedule([5000,8,0,18,0])
        self._add_to_schedule([3500,18,0,19,0])
        self._add_to_schedule([1000,19,0,19,30])
                
        #test pattern
        INCLUDE_TEST_PATTERN=False
        if INCLUDE_TEST_PATTERN:
            self._add_to_schedule([7000,21,0,21,1])
            self._add_to_schedule([6500,21,1,21,2])
            self._add_to_schedule([6000,21,2,21,3])
            self._add_to_schedule([5500,21,3,21,4])
            self._add_to_schedule([5000,21,4,21,5])
            self._add_to_schedule([4500,21,5,21,6])
            self._add_to_schedule([4000,21,6,21,7])
            self._add_to_schedule([3500,21,7,21,8])
            self._add_to_schedule([3000,21,8,21,9])
            self._add_to_schedule([2500,21,9,21,10])
            self._add_to_schedule([2000,21,10,21,11])
            self._add_to_schedule([1500,21,11,21,12])
            self._add_to_schedule([1000,21,12,21,13])
            self._add_to_schedule([500,21,13,21,14])
            self._add_to_schedule([0,21,14,21,15])
            
        print("Lighting Control Schedule: ",self._schedule)
            
    #program_peg is [target value,start_h,start_m,stop_h,stop_m]
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
            self._light_state_actual=self._light_state
        else:                      
            PWM_MIN=0
            PWM_MAX=80
            PWM_SLOPE=(PWM_MAX-PWM_MIN)/100
            val_scaled=PWM_MIN+self._light_state*PWM_SLOPE
            if(val_scaled>100):
                val_scaled=100       
            if(val_scaled<0):
                val_scaled=0
            
            if self._hw_pwm:
                self._h_gpio.hardware_PWM(self._light_ctrl_pin,\
                                          self._pwm_freq,\
                                          round(val_scaled*10000))
                self._light_state_actual=self._light_state
            else:
                pass
                self._h_gpio.set_PWM_dutycycle(self._light_ctrl_pin,val_scaled*2)  #0 - 200
                self._light_state_actual=((0.5*round(val_scaled*2))-PWM_MIN)/PWM_SLOPE  #calculate the rounded setting
            
        
        
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
            #Get the last light sensor reading
            current_light=None
            with self._iob.get_lock():
                n=len(self._target_buf)
                if n>0:
                    time,current_light=self._target_buf[0]  #last reading
            
            if current_light is None:
                self._set_light_state(0,False)   #problem with sensor - turn off heat
            elif self._target_light==0:
                self._set_light_state(0,False)   #set brightness to zero when target is zero
            else:  #Execute integral controller
                #print ("mode: ",self._mode," target_light: ",self._target_light," current_light: ",current_light)
                deltalux=current_light-self._target_light
                deltabrightness=-deltalux*(0.425/120)    #LED/sensor gain is around 120 lux per percent
                MAXDELTABRIGHTNESS=15
                if deltabrightness>MAXDELTABRIGHTNESS:
                    deltabrightness=MAXDELTABRIGHTNESS
                if deltabrightness<-MAXDELTABRIGHTNESS:
                    deltabrightness=-MAXDELTABRIGHTNESS
                self._set_light_state(deltabrightness,True)
                   
                
    def _startup(self):
        IO_Thread._startup(self)
        
        if not self._sim_hw:
            if self._hw_pwm:
                #HW PWM
                self._h_gpio.set_mode(self._light_ctrl_pin,pigpio.ALT5)  #set up PWM on REF pin
                self._pwm_freq=500000  #500kHz
            else:
                #SW PWM
                self._h_gpio.set_mode(self._light_ctrl_pin,pigpio.OUTPUT)  #set up PWM
                self._h_gpio.set_PWM_range(self._light_ctrl_pin,200)
                self._h_gpio.set_PWM_frequency(self._light_ctrl_pin,1000) #set 1kHz to get 200 steps (0.5% steps)
                self._pwm_freq=(self._h_gpio.get_PWM_frequency(self._light_ctrl_pin)) #should get 8kHz
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
        
               
        self._add_to_out_q('Brightness',self._light_state_actual,triggertime) 
        self._add_to_out_q('Target',self._target_light,triggertime)
        
    #process a command string
    def command(self,cmd,data):
        print("io_light_ctrl:command ",cmd,data)
        response=None
        
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
            
        if cmd=='LIGHT_CTRL:SCHED_CLEAR':
            self._schedule=[]
        
        if cmd=='LIGHT_CTRL:SCHED_ADD':
            d=data.split(',')
            if len(d)==5:
                d_int=[]
                d_int.append(float(d[0]))
                d_int.append(int(d[1]))
                d_int.append(int(d[2]))
                d_int.append(int(d[3]))
                d_int.append(int(d[4]))
                self._add_to_schedule(d_int)        
            
        if cmd=='LIGHT_CTRL:SCHED?':
            response=self._schedule        
            
        return response            
        
    def _shutdown(self):
        if not self._sim_hw:
            self._turn_off()
        IO_Thread._shutdown(self)
#END class IO_Thread_Moist------------------------------------------------    