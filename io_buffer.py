'''
io_buffer.py

Routines to buffer a number of samples from the local_io_q
The main loop of gh_io.py feeds data to the buffer via the method
add_data()

'''

from collections import deque
import threading

'''init
all_op_desc=the output of io_thread_manager.get_all_op_descriptions

'''
class IO_Buffer:
    def __init__(self,all_op_desc,buf_size):
        self._all_op_desc=all_op_desc
        self._buf=dict()
        self._buf_size=buf_size
        self._lock=threading.Lock()
        
        #Create a deque buffer for each output parameter in every thread
        for tname in self._all_op_desc: #for each thread name
            self._buf[tname]=dict()
            for pname in self._all_op_desc[tname]:  #for each output parameter                
                self._buf[tname][pname]=deque(maxlen=self._buf_size)
            
    #Diagnostic to print out the buffer in a structured format        
    def printall(self):
        for tname in self._buf:
            print("Thread Name: "+tname)
            for pname in self._buf[tname]:
                print("  Parameter: "+pname)
                (n_items,datapoints)=self.get_all_datapoints(tname,pname)
                print("    Number of items=",n_items) 
                if n_items>0:
                    print("    Last Value=",self.get_last_datapoint(tname,pname))
                    print("    Buffer=",datapoints)
    
    #add_data must only ever be used in the main loop.  Never in a thread.
    def add_data(self,d):
        with self._lock:
            datapoint=(d['time'],d['data'])
            self._buf[d['tname']][d['pname']].appendleft(datapoint)
        
    #the lock can be used by any other threads to prevent writing
    #to do this, use get_lock() to get the lock and then acquire/release it
    #while reading from the buffer
    def get_lock(self):
        return self._lock
        
    '''get_all_datapoints(tname,pname)
    returns (n,datapoints) where n is the number of points and datapoints is
    the deque object.  The newest data is at the left.
    data in the deque is in the format (time,data)
    '''
    def get_all_datapoints(self,tname,pname):
        datapoints=self._buf[tname][pname]
        n=len(datapoints)
        return (n,datapoints)
        
    #as above but returns the last value or None if there is no data
    #returned format is (time,data)
    def get_last_datapoint(self,tname,pname):
        (n,datapoints)=self.get_all_datapoints(tname,pname)
        if len(datapoints)>0:
            return datapoints[0]
        else:
            return None
        
        
    
    