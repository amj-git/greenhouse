'''
gh_io_dispatcher.py

This file contains the class gh_io_dispatcher

This derives from both EventDispatcher and gh_db and adds a Kivy event
interface.


'''
from gh_db import gh_db
from kivy.event import EventDispatcher
from kivy.clock import Clock
import queue


MAX_GH_EV_Q_LEN = 50
EV_Q_CLOCK_PERIOD = 0.2 #Period of checking GH_EV_Q in seconds

#START class gh_io_dispatcher-------------------------------------
class gh_io_dispatcher(gh_db,EventDispatcher):
    def __init__(self, **kwargs):
        self.register_event_type('on_io_data')
        EventDispatcher.__init__(self,**kwargs)
        gh_db.__init__(self)  
        self._gh_ev_q=queue.Queue(MAX_GH_EV_Q_LEN)
        self._clock_event=Clock.schedule_interval(self._clock_heartbeat,EV_Q_CLOCK_PERIOD)
                
        
    #Override the consumer - this is running in the *io_mon thread* so
    #we must not touch any Kivy structures from here.  We must send the data
    #through a queue and pick it up with a clock
    #This function effectively takes the data from the io_q and
    #passes it to gh_ev_q
    def _consumer_fn(self,data):
        gh_db._consumer_fn(self,data)  #Call parent - saves to database
        try:
            self._gh_ev_q.put(data,block=False)
        except queue.Full:  #consumer must have stopped - throw data away
            Logger.exception("IO_Thread:"+self._threadname+" _consumer_fn(): Unable to output data - Queue is full")
        
    #this function is running on a clock heartbeat in the kivy thread
    #it receives data from the _consumer_fn() via the gh_ev_q
    def _clock_heartbeat(self,dt):
        datavalid=True
              
        while(datavalid):  #read everything on the queue
            try:
                data=self._gh_ev_q.get(block=False) 
                if data:
                    self.dispatch('on_io_data',data)
                else:
                    datavalid=False
            except queue.Empty:
                datavalid=False
              
    def on_io_data(self,*args):
        pass  
#END class gh_io_dispatcher-------------------------------------


#TEST CODE
from kivy.app import App
from kivy.core.window import Window
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.logger import Logger
from gh_io_status_grid import gh_io_status_grid
from kivy.graphics import Color, Ellipse, Rectangle, RoundedRectangle

class RootWidget(BoxLayout):
    def __init__(self, **kwargs):
        self.orientation='horizontal'
        super(RootWidget, self).__init__(**kwargs)
        
        b1=Button(text='Exit',size_hint=(0.3,1))
        b1.bind(on_release=self.quit_app)
        
        self.ti1=BoxLayout()
                  
        self.add_widget(self.ti1)
        self.add_widget(b1)
        
        with self.ti1.canvas:
            Color(1,0,0,0.5,mode='rgba')
            Rectangle(pos=self.ti1.pos,size=self.ti1.size)
                      
        
    def start_io(self):
        self._gio=gh_io_dispatcher()
        self._gio.start_io()
    
        self._gio.bind(on_io_data=self._process_io_data)
                    
        io_desc=self._gio.io_query('OPDESC?',0,5)
        Logger.info("init_io: IO Descriptions:")
        if io_desc is not None:
            Logger.info(io_desc)
        else:
            Logger.exception("init_io: Query Timed Out")
    
        #Build the status grid - see gh_io_status_grid.py
        self.statusgrid=gh_io_status_grid(all_op_desc=io_desc)
        self.ti1.add_widget(self.statusgrid)
    
        Logger.info("init_io: Listening to io_q.")       
        self._gio.start_events()
        
    #this is the callback that is triggered by the io_q events
    #here it just prints the data
    def _process_io_data(self,*args):
        self.statusgrid.process_data(args[1])
        #Logger.debug("gh_io_dispatcher:"+str(args[1]))
        
    def stop_io(self,*args):
        self._gio.stop_io()
        
    def quit_app(self,*args):
        App.get_running_app().stop()
        

class gh_db_dispatcher_test_app(App):
      
    def build(self):
        self._running=False
        self._rw=RootWidget()
        return self._rw  

    def on_start(self):
        self._rw.start_io()
        self._running=True
    
    def on_stop(self):        
        if self._running:  #prevent it running twice due to multiple clicks
            self._rw.stop_io()
            self._running=False

if __name__ == "__main__":   
    gh_db_dispatcher_test_app().run()