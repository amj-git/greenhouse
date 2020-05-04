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

import gh_io

class gh_db:
    def __init__(self):
        self._io_q=multiprocessing.Queue()
        (self._io_ctrl,self.__io_ctrl_gh_io)=multiprocessing.Pipe()  #not end b only used by gh_io end
        self._gh_io_process=\
            multiprocessing.Process(target=gh_io.gh_io_main,args=(self._io_q,self.__io_ctrl_gh_io))
        self._gh_io_process.daemon=True
        
    def start_io(self):
        self._gh_io_process.start()
        print("gh_db: IO Started.")

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
        #send the stop signal
        self.send_io_command('TERMINATE',0)
        self._gh_io_process.join()
        self._io_ctrl.close()
        self.__io_ctrl_gh_io.close()
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
    
    time1=datetime.now()
    
    while((datetime.now()-time1).total_seconds()<10): #run for 15 sec
        
        try:
            op_data=db.get_io_q().get(timeout=0.1)
        except queue.Empty:
            continue
        
        print("gh_db_test(): Received from io_q: ",op_data)        
           
    
    print("gh_db: Stopped Listening to io_q.")
    
    db.stop_io()

if __name__ == "__main__":   
    gh_db_test()