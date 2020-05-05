'''
gh_io_dispatcher.py

This file contains the class gh_io_dispatcher

This derives from both EventDispatcher and gh_db and adds a Kivy event
interface.


'''
from gh_db import gh_db
from kivy.event import EventDispatcher

#START class gh_io_dispatcher-------------------------------------
class gh_io_dispatcher(gh_db,EventDispatcher):
    def __init__(self, **kwargs):
        self.register_event_type('on_io_data')
        EventDispatcher.__init__(self,**kwargs)
        gh_db.__init__(self)  
        
    #override the gh_db dispatch function
    def _dispatch_fn(self,data):
        self.dispatch('on_io_data',data)
        
    def on_io_data(self,*args):
        pass  
#END class gh_io_dispatcher-------------------------------------


#TEST CODE
from kivy.app import App
from kivy.core.window import Window
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.logger import Logger

class RootWidget(BoxLayout):
    def __init__(self, **kwargs):
        super(RootWidget, self).__init__(**kwargs)
        
        b1=Button(text='Exit')
        self.add_widget(b1)
        b1.bind(on_release=self.quit_app)
               
        self._init_io()
        
    def _init_io(self):
        self._gio=gh_io_dispatcher()
        self._gio.start_io()
    
        self._gio.bind(on_io_data=self._process_io_data)
                    
        io_desc=self._gio.io_query('OPDESC?',0,5)
        Logger.info("init_io: IO Descriptions:")
        if io_desc is not None:
            Logger.info(io_desc)
        else:
            Logger.exception("init_io: Query Timed Out")
    
        Logger.info("init_io: Listening to io_q.")
        #App.bind(on_stop=self.on_close)        
        self._gio.start_events()
        
    #this is the callback that is triggered by the io_q events
    #here it just prints the data
    def _process_io_data(self,*args):
        Logger.info("gh_io_dispatcher:"+str(args[1]))
        
    def stop_io(self,*args):
        self._gio.stop_io()
        
    def quit_app(self,*args):
        App.get_running_app().stop()
        

class gh_db_dispatcher_test_app(App):
      
    def build(self):
        self._rw=RootWidget()
        self._stopping=False
        return self._rw  
    
    def on_stop(self):        
        if not self._stopping:  #prevent it running twice due to multiple clicks
            self._rw.stop_io()
            self._stopping=True

if __name__ == "__main__":   
    gh_db_dispatcher_test_app().run()