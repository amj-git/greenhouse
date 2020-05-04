'''
gh_db.py

Receives events from the gh_io process
Saves data to a database (file)
Interfaces "live" events to the host GUI program
Provides database access for the host GUI program

'''

import multiprocessing
from time import sleep
from datetime import datetime, timedelta
import queue
from threading import Thread

import gh_io

#monitor thread
class gh_mon(Thread):
    '''__init__
    io_q=the queue to monitor
    '''
    def __init__(self,io_q):
        Thread.__init__(self)
        self.daemon=True
        self._io_q=io_q
        
    def term(self):
        self.__running=False
        
    def __del__(self):
        pass
    
    def run(self):
        self._startup()
        while(self.__running):
            try:
                op_data=self._io_q.get(timeout=0.1) #wait 100ms max
            except queue.Empty:
                continue
            
            print("io_mon: op_data=",op_data)
            #<Dispatch the event>
               
    def _startup(self):
        self.__running=True
        pass
        

class gh_db:
    def __init__(self):
        self._io_q=multiprocessing.Queue()
        (self._io_ctrl,self.__io_ctrl_gh_io)=multiprocessing.Pipe()  #not end b only used by gh_io end
        self._gh_io_process=\
            multiprocessing.Process(target=gh_io.gh_io_main,args=(self.get_io_q(),self.__io_ctrl_gh_io))
        self._gh_io_process.daemon=True
        self._gh_mon=gh_mon(self.get_io_q())
                
    def start_io(self):
        self._gh_io_process.start()  #start IO process
        print("gh_db: IO Started.")
        
    def start_events(self):
        self._gh_mon.start()  #start receiving thread

    def send_io_command(self,cmd,data):
        ctrl_data=dict()
        ctrl_data['command']=cmd
        ctrl_data['data']=data
        self._io_ctrl.send(ctrl_data)
    
    #Query command.  timeout is max time to wait in seconds
    def io_query(self,cmd,data,timeout):
        self.send_io_command(cmd,data)
        if self._io_ctrl.poll(timeout):
            rx_data=self._io_ctrl.recv()
        else:
            rx_data=None
        return rx_data
    
    def stop_io(self):
        #send the stop signal and wait for IO process to stop
        self.send_io_command('TERMINATE',0)
        self._gh_io_process.join()
        
        #shut down both ends of the pipe
        self._io_ctrl.close()
        self.__io_ctrl_gh_io.close()
        
        #stop the monitoring thread
        self._gh_mon.term()
        self._gh_mon.join()
        print("gh_db: IO Stopped.")
        
    def get_io_q(self):
        return self._io_q

def gh_db_test():
    db=gh_db()
    db.start_io()
    
    io_desc=db.io_query('OPDESC?',0,5)
    print("gh_db: IO Descriptions:")
    if io_desc is not None:
        print(io_desc)
    else:
        print("gh_db: Query Timed Out")
    
    print("gh_db: Listening to io_q.")
    
    db.start_events()  #starts the listening thread which will dispatch events
    
      
    sleep(15)  #let everything run for a while
    
    db.stop_io()  #shut it all down

if __name__ == "__main__":   
    gh_db_test()