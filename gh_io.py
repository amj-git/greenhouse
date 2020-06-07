

'''
gh_io.py

Entry point to gh_io process
'''

from io_thread import IO_Thread, IO_Thread_Manager, IO_Thread_ExampleIO, \
                        IO_Thread_DS18B20, \
                        IO_Thread_BH1750, \
                        IO_Thread_DHT22, \
                        IO_Thread_ExampleController, \
                        IO_Thread_Moist
from time import sleep
from datetime import datetime, timedelta
import queue
from io_buffer import IO_Buffer
from process_control import pr_cont
import platform


def gh_io_main(io_q,io_ctrl):
    
    #assume we must simulate the data on windows - no real HW present
    if platform.system()=='Windows':
        sim_mode=True
        
    if platform.system()=='Linux':
        sim_mode=False
    
    
    local_io_q=queue.Queue(20)  #allow max of 20 items
    
    io_manager=IO_Thread_Manager(sim_hw=sim_mode)  #sim_hw for the Manager determinest whether to start pigpio
    
    
    #Create one thread from the base class
    io_thread1=IO_Thread(threadname="Sim Thread 1", \
                         out_q=local_io_q, \
                         sim_hw=True, \
                         period=1)
    io_manager.add_thread(io_thread1)
    
    #Create one thread from the example template
    io_thread2=IO_Thread_ExampleIO(threadname="Sim Thread 2", \
                         out_q=local_io_q, \
                         sim_hw=True, \
                         period=0.618)
    io_manager.add_thread(io_thread2)
        
    io_thread3=IO_Thread_DS18B20(threadname="Probe 1", \
                         out_q=local_io_q, \
                         sim_hw=sim_mode, \
                         period=4, \
                         addr='28-00000c362511')
    io_manager.add_thread(io_thread3)
    
    io_thread4=IO_Thread_DS18B20(threadname="Probe 2", \
                         out_q=local_io_q, \
                         sim_hw=sim_mode, \
                         period=2.5, \
                         addr='28-00000c36cbaa')
    io_manager.add_thread(io_thread4)
    
    io_thread5=IO_Thread_DS18B20(threadname="Control Box", \
                         out_q=local_io_q, \
                         sim_hw=sim_mode, \
                         period=3, \
                         addr='28-00000c37dfa4')
    io_manager.add_thread(io_thread5)
    
    io_thread6=IO_Thread_BH1750(threadname="Inside Light Sensor", \
                         out_q=local_io_q, \
                         sim_hw=sim_mode, \
                         period=2 )
    io_manager.add_thread(io_thread6)
    
    #DHT sensors on pin 17 and 27
    io_thread7=IO_Thread_DHT22(threadname="DHT1", \
                         out_q=local_io_q, \
                         sim_hw=sim_mode, \
                         period=5, \
                         pin=17 )
    io_manager.add_thread(io_thread7)
    
    #Moisture sensors on pin 10,9,11
    #ref is on pin 5
    #All handled by the same thread as they share ref
    io_thread8=IO_Thread_Moist(threadname="Moisture", \
                         out_q=local_io_q, \
                         sim_hw=sim_mode, \
                         period=10, \
                         ref_pin=12, \
                         det_pins=[10,9,11] )
    io_manager.add_thread(io_thread8)    
    
    #demo of a thread that uses data from another thread
    #this example simply repeats the temperature from DHT1
    io_thread8=IO_Thread_ExampleController(threadname="Sim Ctrl 1", \
                         out_q=local_io_q, \
                         sim_hw=sim_mode, \
                         period=3, \
                         source_tname='DHT1', \
                         source_pname='Temp' )
    io_manager.add_thread(io_thread8)
    
    all_op_desc=io_manager.get_all_op_descriptions()
           
    #io_manager.start_threads()  #moved to be triggered by START command
    #iob=io_manager.get_iob()  #get the IO buffer
    iob=None
       
    pr_cont.set_proctitle('gh_io process') #allows process to be idenfified in htop
    pr_cont.set_name('gh_io main') #allows process to be idenfified in htop
    
    _main_loop_running=True
    #GH_IO MAIN LOOP------------------ 
    while(_main_loop_running): 
        if io_ctrl.poll(): #check if there are any commands
            try:
                ctrl_data=io_ctrl.recv()
            except EOFError:
                print("gh_io MAIN LOOP: Poll true but no data")
            cmd=ctrl_data['command']
            data=ctrl_data['data']
            if(cmd=='TERMINATE'):  #Command to stop the process
                _main_loop_running=False
                print("gh_io MAIN LOOP: TERMINATE Command Received. data =",data)
                break
            if(cmd=='OPDESC?'):  #output descriptions query
                io_ctrl.send(all_op_desc)
            if(cmd=='START'):
                io_manager.start_threads()
                iob=io_manager.get_iob()  #get the IO buffer
        try:
            op_data=local_io_q.get(timeout=0.1) #Block here max 100ms
        except queue.Empty:
            continue
        if iob is not None:
            iob.add_data(op_data)  #feed the local buffer.  This may block
                                #if any threads have locked it while they read
        if io_q is not None:
            try:
                io_q.put(op_data) #forward the data to the host application
            except queue.Full:
                print("gh_io MAIN LOOP: io_q is full")
                
    #END GH_IO MAIN LOOP------------------
               
    io_manager.kill_threads()
    
    #END OF GH_IO_MAIN

    
if __name__ == "__main__":    
    
    def gh_io_test(io_q):
    
        
        sim_mode=False
        
        local_io_q=queue.Queue(20)  #allow max of 20 items
        
        io_manager=IO_Thread_Manager(sim_hw=sim_mode)  #sim_hw for the Manager determinest whether to start pigpio
        
        
        #Create one thread from the base class
        io_thread1=IO_Thread(threadname="Sim Thread 1", \
                             out_q=local_io_q, \
                             sim_hw=True, \
                             period=1)
        io_manager.add_thread(io_thread1)
        
        #Create one thread from the example template
        io_thread2=IO_Thread_ExampleIO(threadname="Sim Thread 2", \
                             out_q=local_io_q, \
                             sim_hw=True, \
                             period=1.5)
        io_manager.add_thread(io_thread2)
            
        io_thread3=IO_Thread_DS18B20(threadname="Probe 1", \
                             out_q=local_io_q, \
                             sim_hw=sim_mode, \
                             period=4, \
                             addr='28-00000c362511')
        io_manager.add_thread(io_thread3)
        
        io_thread4=IO_Thread_DS18B20(threadname="Probe 2", \
                             out_q=local_io_q, \
                             sim_hw=sim_mode, \
                             period=2.5, \
                             addr='28-00000c36cbaa')
        io_manager.add_thread(io_thread4)
        
        io_thread5=IO_Thread_DS18B20(threadname="Control Box", \
                             out_q=local_io_q, \
                             sim_hw=sim_mode, \
                             period=3, \
                             addr='28-00000c37dfa4')
        io_manager.add_thread(io_thread5)
        
        io_thread6=IO_Thread_BH1750(threadname="Inside Light Sensor", \
                             out_q=local_io_q, \
                             sim_hw=sim_mode, \
                             period=2 )
        io_manager.add_thread(io_thread6)
        
        #DHT sensors on pin 17 and 27
        io_thread7=IO_Thread_DHT22(threadname="DHT1", \
                             out_q=local_io_q, \
                             sim_hw=sim_mode, \
                             period=5, \
                             pin=17 )
        io_manager.add_thread(io_thread7)
        
        #demo of a thread that uses data from another thread
        #this example simply repeats the temperature from DHT1
        io_thread8=IO_Thread_ExampleController(threadname="Sim Ctrl 1", \
                             out_q=local_io_q, \
                             sim_hw=sim_mode, \
                             period=3, \
                             source_tname='DHT1', \
                             source_pname='Temp' )
        io_manager.add_thread(io_thread8)
        
        #reading all output descriptions
        print('IO Output descriptions:')
        all_op_desc=io_manager.get_all_op_descriptions()
        print(all_op_desc)
        
        #example of how to access one item   
        print("The units of Probe 1/Temp is "+\
              all_op_desc['Probe 1']['Temp']['punits'])
        
            
        io_manager.start_threads()
        iob=io_manager.get_iob()  #get the IO buffer
        print("IO Buffer before starting")
        iob.printall()
        
        #sleep(15)  #let some backlog build up in the queue - should see queue overflow
        
        time1=datetime.now()
        
        while((datetime.now()-time1).total_seconds()<15): #run for 15 sec
            
            try:
                op_data=local_io_q.get(timeout=0.1)
            except queue.Empty:
                continue
            
            print("gh_io_test(): Received from local_io_q: ",op_data)        
            iob.add_data(op_data)  #feed the local buffer.  This may block
                                    #if any threads have locked it while they read
            
            if io_q is not None:
                io_q.put(op_data) #forward the data to the host application
            
        print("IO Buffer after running")
        iob.printall()
           
        io_manager.kill_threads()
        
        

    #MAIN---------------
   
    gh_io_test(None)
