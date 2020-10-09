
from io_thread import IO_Thread
import time
from datetime import datetime

try:
    import pigpio  
    _pigpio_ok=True
except ImportError:
    _pigpio_ok=False

class IO_Thread_Sprinkler(IO_Thread):
    def __init__(self,**kwargs):
        self._valve_pins=kwargs.get('valve_pins',False)
        self._valve_names=kwargs.get('valve_names',False)
        self._schedule=[]
        self._valve_mode=['OFF']*len(self._valve_pins)
        self._set_default_schedule()
        self._valve_states=[0]*len(self._valve_pins)
        IO_Thread.__init__(self,**kwargs)
        
    
    #get the parameter name associated with the kth sensor
    #k starts at 0
    def _get_pname(self,k):
        if self._valve_names==False:
            return '%d' % (k+1)
        else:
            return self._valve_names[k]
    
    def _set_op_desc(self):
        for k,valve_pin in enumerate(self._valve_pins):
            #print ('IO_Thread_Moist._set_op_desc: k=',k,'det_pin=',det_pin)
            pname=self._get_pname(k)
            self._op_desc[pname]={
                  'pdesc':'Sprinkler',
                  'ptype':'valve_pos',
                  'pdatatype':'float',
                  'pmin':-10,
                  'pmax':110,
                  'punits':'%' }
    
    def _set_default_schedule(self):
        self._add_to_schedule([0,20,0,20,20])
        self._add_to_schedule([1,19,15,19,35])
        self._add_to_schedule([0,13,30,13,40])
        #self._add_to_schedule([0,21,30,21,32])
        print("Sprinkler Schedule: ",self._schedule)
            
    #program_peg is [valve_index,start_h,start_m,stop_h,stop_m]
    #remember valve_index starts at 0
    def _add_to_schedule(self,program_peg):
        self._schedule.append(program_peg)
                            
    def _clear_valve_states(self):
        for k,valve_pin in enumerate(self._valve_pins):
            self._valve_states[k]=0    
    
    def _check_pegs(self):
        t_now=datetime.now()
        self._clear_valve_states()
        for peg in self._schedule:
            valve_num=peg[0]
            peg_start=t_now.replace(hour=peg[1],minute=peg[2],second=0,microsecond=0)
            peg_stop=t_now.replace(hour=peg[3],minute=peg[4],second=0,microsecond=0)
            if (t_now>peg_start) and (t_now<peg_stop):
                self._valve_states[valve_num]=1

        for k,valve_pin in enumerate(self._valve_pins):
            if self._valve_mode[k]=='ON':
                self._valve_states[k]=1
            if self._valve_mode[k]=='OFF':
                self._valve_states[k]=0
            self._h_gpio.write(valve_pin,self._valve_states[k])
            #print("valve ",k,": state=",self._valve_states[k])
            
                
    def _startup(self):
        IO_Thread._startup(self)
        if not self._sim_hw:
            for pin in self._valve_pins:
                self._h_gpio.set_mode(pin,pigpio.OUTPUT)
            self._turn_off()
        
    #Turns off every valve
    def _turn_off(self):
        for pin in self._valve_pins:
            self._h_gpio.write(pin,0)
                    
    def _heartbeat(self,triggertime):
        if self._sim_hw:
            IO_Thread._heartbeat(self,triggertime)
        else:
            #control the valves
            self._check_pegs()
            
            for k,valve_pin in enumerate(self._valve_pins):
                pname=self._get_pname(k)
                self._add_to_out_q(pname,self._valve_states[k]*100,triggertime)
            
    #process a command string
    def command(self,cmd,data):
        #SPRINK:MODE <1|2|3> <OFF|ON|AUTO> 
        if cmd=='SPRINK:MODE':
            d=data.split(',')
            valve_number=int(d[0].strip())
            valve_mode=d[1].strip()
            self._valve_mode[valve_number]=valve_mode
            self._heartbeat(datetime.now()) #force an update
        
    def _shutdown(self):
        if not self._sim_hw:
            self._turn_off()
        IO_Thread._shutdown(self)
#END class IO_Thread_Moist------------------------------------------------    