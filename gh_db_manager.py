'''
gh_db_manager

Manages access to the database itself
Uses sqlite3 database

'''

'''param_db
Parameter database handler

Manages data for one parameter (timestamp, value)

Each parameter is stored in one sqlite3 database file.
The filename is <threadname>_<pname>.db with spaces replaced by underscores

Each db file contains the following tables:-

TABLE: raw_data. Uncompressed data:-
timestamp - integer - ms timestamp
val - integer - value of the data

TABLE comp_data.  Compressed data:-
timestamp - integer ms timestamp at the END of the sample period
avg - integer - average value in compressed interval
min - integer - min value in compressed interval
max - integer - max value in compressed interval

TABLE meta_data.  Additional info:-
key - text - key
val - text - value

The meta_data is used to save a dictionary containing:-
The output description data from the associated thread
comp_period - float formatted as text - the time interval in seconds of the compressed data

'''
import sqlite3
import threading
from datetime import datetime, timedelta


DB_DIR='db/'
MAX_COMMIT_DELAY=20 #max number of seconds to not flush data to db
                    #Note that data is only flushed when a new point is received
                    #so if the periodicity of the data is greater than MAX_COMMIT_DELAY,
                    #it won't get written until later.
                    
DEFAULT_TCHUNK=10*60*1000  #Default compression chunk size in ms

#Timestamp is integer number of milliseconds since 1/1/1970 
def datetime_to_timestamp(d):
    return round(d.timestamp()*1000)

#Converts back to time.  Note there can be issues with local time and handling of leap seconds
#needs care
def timestamp_to_datetime(ts):
    return datetime.fromtimestamp(ts/1000)

#param_db----------------------------------------------------
class param_db:
    def __init__(self,**kwargs):
        self._lock=threading.Lock()
        self._op_desc=kwargs.get('op_desc',None)
        self._tname=kwargs.get('tname',None)
        self._pname=kwargs.get('pname',None)
        #print('param_db __init__: tname=',self._tname,'pname=',self._pname,'opdesc=',self._op_desc)
        self._db=None
        if self._op_desc is not None:
            self._dbname=DB_DIR+(self._tname+'-'+self._pname+'.db').replace(' ','-')
            self._open_db()
            
                
    def _open_db(self):
        with self._lock:
            #connect with thread checking disabled
            #we use _lock to prevent simultaneous access.
            #write_value is usually called by a different thread
            self._db=sqlite3.connect(self._dbname, check_same_thread=False)
            self._db.execute('''CREATE TABLE IF NOT EXISTS raw_data (
                            timestamp integer PRIMARY KEY,
                            val integer)''')
            self._db.execute('''CREATE TABLE IF NOT EXISTS comp_data (
                            timestamp integer PRIMARY KEY,
                            avg integer,
                            min integer,
                            max integer)''')
            self._db.execute('''CREATE TABLE IF NOT EXISTS meta_data (
                            key text,
                            val text)''')
            self.commit()
            self._write_meta_data()
            #calculate the time after which the next compression can proceed
            self._Tnext_compress=self._get_last_comp_data_time()+self._Tchunk  
            
    def _close_db(self):
        if self._db is not None:
            self.commit()
            self._db.close()
            
    def __del__(self):
        self._close_db()
        
    #reads meta_data from the database and returns number of elements
    def _read_meta_data(self):
        rows=self._db.execute("SELECT * FROM meta_data")
          
        self._meta_data=dict()
        for row in rows:
            #print(row)
            self._meta_data[row[0]]=row[1]        
        
        if 'val_comp_mult' in self._meta_data:
            self._val_comp_mult=float(self._meta_data['val_comp_mult'])  #store with db
            self._val_uncomp_mult=1/self._val_comp_mult            
        else:
            #print('No val_comp_mult found in meta_data table')
            pass
        if 'Tchunk' in self._meta_data:
            self._Tchunk=float(self._meta_data['Tchunk'])  #store with db            
        else:
            self._Tchunk=DEFAULT_TCHUNK
        #print(self._meta_data)
        #print('length=',len(self._meta_data))
        return len(self._meta_data)

    #if there is no meta_data present, write the op_data into it 
    def _write_meta_data(self):
        #print('param_db _write_meta_data: entered')
        if self._read_meta_data()==0:
            print('gh_db_manager param_db: Initialising tables in ',self._dbname)
            self._init_multipliers()
            #print('param_db _write_meta_data: init_multipliers() run self._val_comp_mult=',self._val_comp_mult)
            data=[]
            for key in self._op_desc:
                data.append( (key,self._op_desc[key]) )
            data.append( ('val_comp_mult','{:e}'.format(self._val_comp_mult)) )
            data.append( ('Tchunk','{d}'.format(DEFAULT_TCHUNK)) )
            self._db.executemany('INSERT INTO meta_data VALUES (?,?)',data)
            self.commit()
            self._read_meta_data() #this ensures self._meta_data gets set.
            
    def get_meta_data(self):
        return self._meta_data
            
    '''
        _setup_multipliers
        Set the value to integer conversion factor
        Defaults to 1
        Note the scaling used is stored in the db when it is created
        If the ptype changes later, the db will still work but will use
        the original scaling
    '''
    def _init_multipliers(self):
        #print('param_db init_multipliers() op_desc=',self._op_desc)
        ptype=self._op_desc['ptype']
        if ptype=='temp':
            self._val_comp_mult=100.0
        elif ptype=='humid':
            self._val_comp_mult=10.0            
        elif ptype=='light':
            self._val_comp_mult=1.0
        else:
            self._val_comp_mult=1.0
        
    '''
        compress_val
        accepts value val and converts to integer for storage in the db
    '''
    def compress_val(self,uncomp_val):
        return round(uncomp_val*self._val_comp_mult)
        
    def uncompress_val(self,comp_val):
        return comp_val*self._val_uncomp_mult
            
    '''
        write_value
        Writes a (timestamp,value) pair to the database
        timestamp is in datetime format
        value is a numeric format
    '''
    def write_value(self,timestamp,val):
        timestamp_ms=datetime_to_timestamp(timestamp)
        data=(timestamp_ms,self.compress_val(val))
        with self._lock:
            #tstart=datetime.now()
            self._db.execute('INSERT INTO raw_data VALUES (?,?)',data)
            self._commit_if_due(timestamp_ms)
            #tstop=datetime.now()
            #tdelta=(tstop-tstart).total_seconds()
            #print("write time=",tdelta,"s")
            '''
            Committing one measurement takes 120 - 200ms on windows
            All thread data has been serialised thought the queue, so
            for the 11 params we have running this can total over 1 second.
            This slowly fills the queue up, and we start losing data.
            If you comment out the commit, the time goes to below 1ms.
            Therefore a good method is to only commit at a slower interval.   
            Hence the commit_if_due functionality
            MAX_COMMIT_DELAY is the maximum time with no flushing                     
            '''
            
            
    #Flush data
    def commit(self):
        self._db.commit()
        self._last_commit_time=datetime.now()
        self._commit_pending=False
        
    #Flush data only if it's due
    #accepts the timestamp of the last data to allow calculation of whether
    #a compression cycle should happen
    def _commit_if_due(self,timestamp_ms):
        self._commit_pending=True
        if self.commit_due():
            #write the data
            self.commit()
            #do a compression cycle
            #compression will cause delay, so do it only every MAX_COMMIT_DELAY seconds
            if(timestamp_ms>self._Tnext_compress):
                self.compress_next_chunk()
                
    #Check if data needs flushing
    def commit_due(self):
        if self._commit_pending:
            tdelta=(datetime.now()-self._last_commit_time).total_seconds()
            if(tdelta>MAX_COMMIT_DELAY):
                return True
        return False
    
    #This finds the last timestamp in the comp_data table
    def _get_last_comp_data_time(self):
        cur=self._db.cursor()
        cur.execute("SELECT MAX(timestamp) FROM comp_data")
        Tcl=cur.fetchone()[0]
        if Tcl is None:
            Tcl=0
        return Tcl
    '''
    
    Gets a chunk from raw_data and compresses it into comp_data
    The chunk size is self._Tchunk
    Returns the timestamp of the chunk 
    '''
    def compress_next_chunk(self):
        Tcl=self._get_last_comp_data_time()
        cur=self._db.cursor()
        cur.execute("SELECT MIN(timestamp) FROM raw_data \
                    WHERE timestamp>?",(Tcl,))
        Traw_start=cur.fetchone()[0]
        cur.execute("SELECT min(val),max(val),avg(val),max(timestamp) \
                    FROM raw_data WHERE timestamp>=? AND timestamp<=? \
                    ORDER BY timestamp ASC",\
                    (Traw_start,Traw_start+self._Tchunk))
        data=cur.fetchone()
        (min_val,max_val,avg_val,ts)=(data[0],data[1],data[2],data[3])
        print("param_db: compress_next_chunk (",self._dbname,")")
        print("Tcl=",Tcl,"Traw_start=",Traw_start,"ts=",ts,\
              "min_val=",min_val,"max_val=",max_val,"avg_val=",avg_val)
        self._db.execute('INSERT INTO comp_data VALUES (?,?,?,?)',(ts,avg_val,min_val,max_val))
        self.commit()
        self._Tnext_compress=ts+self._Tchunk  #this is the next point time that can trigger a compression cycle
        return ts
      
    '''
    Returns raw data between two timestamps (in ms)
    '''
    def get_raw_line(self,Tstart,Tstop):
        with self._lock:
            rows=self._db.execute("SELECT * FROM raw_data WHERE timestamp>=? AND timestamp<=? ORDER BY timestamp ASC",\
                            (Tstart,Tstop))
            data=[]
            #add a 0.1lx offset for light readings to prevent zeros screwing up log scale
            if self._op_desc['ptype']=='light':
                offset=0.1 #lx
            else:
                offset=0
            for row in rows:
                data.append ((row[0],row[1]*self._val_uncomp_mult+offset))
            return data
        
    '''returns compressed line between two timestamps
    data is tuples of (ts,avg,min,max)
    '''
    def get_comp_line(self,Tstart,Tstop):
        with self._lock:
            rows=self._db.execute("SELECT * FROM comp_data WHERE timestamp>=? AND timestamp<=? ORDER BY timestamp ASC",\
                            (Tstart,Tstop))
            data=[]
            #add a 0.1lx offset for light readings to prevent zeros screwing up log scale
            if self._op_desc['ptype']=='light':
                offset=0.1 #lx
            else:
                offset=0
            for row in rows:
                data.append ((row[0],row[1]*self._val_uncomp_mult+offset,\
                              row[2]*self._val_uncomp_mult+offset,\
                              row[3]*self._val_uncomp_mult+offset))
            return data 
        
    def get_Tchunk(self):
        return self._Tchunk

'''gh_db_manager----------------------------------------------
Database Manager

Manages access to all database files 

The constructor accepts an all_op_desc object from IO_thread_manager
It initialises the relevant databases

Process data accepts data from a thread and saves it to the appropriate db

_dbs stores a dictionary of the param_db's associated with each thread/parameter
'''
class gh_db_manager:
    
    #gh_db_manager constructor - accepts a dictionary containing all of the parameter
    #descriptions, as provided by IO_thread_manager
    def __init__(self,**kwargs):
        self._all_op_desc=kwargs.get('all_op_desc',None)
        self._dbs=dict()
        #initialise one database for every thread/parameter
        for tname in self._all_op_desc:
            self._dbs[tname]=dict()
            for pname in self._all_op_desc[tname]:
                op_desc=self._all_op_desc[tname][pname]
                #print('gh_db_manager __init__: tname=',tname,'pname=',pname,'opdesc=',op_desc)
                self._dbs[tname][pname]=param_db(tname=tname,\
                                                 pname=pname,\
                                                 op_desc=op_desc)
        
    def process_data(self,data):
        #get the associated parameter database
        pdb=self.get_database(data['tname'],data['pname'])
        #write the data
        pdb.write_value(data['time'],data['data'])
        
    def get_database(self,tname,pname):
        return self._dbs[tname][pname]
        
    #writes all pending data to disk.  This is used prior to exiting the program
    #we allow up to MAX_COMMIT_DELAY seconds of data to build up to speed up the program
    #if each point were committed as it arrived, it would be too slow
    def commit_all(self):
        for tname in self._dbs:
            for pname in self._dbs[tname]:
                self._dbs[tname][pname].commit()
        print('gh_db_manager: All databases flushed')