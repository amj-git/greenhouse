

'''
gh_io.py

Entry point to gh_io process
'''

from io_thread import IO_Thread, IO_Thread_Manager, IO_Thread_ExampleIO, \
                        IO_Thread_DS18B20, \
                        IO_Thread_BH1750, \
                        IO_Thread_DHT22
from time import sleep
from datetime import datetime, timedelta
import queue
from queue import Queue

def gh_io_test():
    
    sim_mode=False
    
    local_io_q=Queue(20)  #allow max of 20 items
    
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
    
    print('IO Output descriptions:')
    io_manager.print_descriptions()
    
    io_manager.start_threads()
    
    #sleep(15)  #let some backlog build up in the queue - should see queue overflow
    
    time1=datetime.now()
    
    while((datetime.now()-time1).total_seconds()<15): #run for 15 sec
        
        try:
            op_data=local_io_q.get(timeout=0.1)
        except queue.Empty:
            continue
        
        print("gh_io_test(): Received from queue: ",op_data)        
    
    io_manager.kill_threads()
    
    


if __name__ == "__main__":   
    gh_io_test()
