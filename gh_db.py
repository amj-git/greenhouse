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
from process_control import pr_cont

import gh_io
import gh_db_manager

MAX_IO_Q_LEN = 100

#monitor thread
class gh_mon(Thread):
    '''__init__
    io_q=the queue to monitor
    '''
    def __init__(self,io_q,consumer_fn):
        Thread.__init__(self)
        self.daemon=True
        self._io_q=io_q
        self._fn=consumer_fn
        
    def term(self):
        self.__running=False
        
    def __del__(self):
        pass
    
    def run(self):
        pr_cont.set_name('gh_mon') #allows process to be idenfified in htop
        self._startup()
        while(self.__running):
            try:
                op_data=self._io_q.get(timeout=0.1) #wait 100ms max
            except queue.Empty:
                continue            
            #consume the data using the provided function
            self._fn(op_data)            
               
    def _startup(self):
        self.__running=True
        pass
        
#START class gh_db-------------------------------------
class gh_db:
    def __init__(self):
        self._io_q=multiprocessing.Queue(MAX_IO_Q_LEN)
        (self._io_ctrl,self.__io_ctrl_gh_io)=multiprocessing.Pipe()  #not end b only used by gh_io end
        self._gh_io_process=\
            multiprocessing.Process(name="gh_io process",target=gh_io.gh_io_main,args=(self.get_io_q(),self.__io_ctrl_gh_io))            
        self._gh_io_process.daemon=True
        self._gh_mon=gh_mon(self.get_io_q(),self._consumer_fn)
                
    def start_io(self):
        self._gh_io_process.start()  #start IO process
        self._init_db_manager()          #wait for this to complete - can be slow
        self.send_io_command('START',0)  #This starts the threads
        print("gh_db: IO Started.")
      
    '''Initialise the database manager
    this requires a copy of the output descriptions, to the IO process
    must be started first
    '''
    def _init_db_manager(self):
        io_desc=self.io_query('OPDESC?',0,15)  #command,data,timeout - need long timeout if using spawn instead of fork
        self._db_manager=gh_db_manager.gh_db_manager(all_op_desc=io_desc)
    
    def get_db_manager(self):
        return self._db_manager
    
    #this is the despatch function.  It is called by the thread
    #every time data is received in the io_q
    #you can override this in a derived method for your preferred behaviour
    def _consumer_fn(self,data):
        #print("gh_db._consumer_fn: data=",data)
        self._save_to_db(data)
        
    #add function here to save the data to the database
    def _save_to_db(self,data):
        self._db_manager.process_data(data)
        
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
        
        #flush all data to disk
        self._db_manager.commit_all()
        
    def get_io_q(self):
        return self._io_q
#START class gh_db-------------------------------------

def gh_db_test():
    pr_cont.set_name('gh_db_test main') #allows process to be idenfified in htop
    pr_cont.set_proctitle('app main process') #allows process to be idenfified in htop
    
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
    
      
    #sleep(15)  #let everything run for a while
    while(True):
        sleep(1)
    
    db.stop_io()  #shut it all down

if __name__ == "__main__":   
    multiprocessing.set_start_method('spawn')
    gh_db_test()