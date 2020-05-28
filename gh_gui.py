
#gh_gui.py
'''
Main
'''

#Environment settings for running in Raspberry PI CLI mode

'''
Note: you can change between CLI and GUI mode in with "sudo raspi-config"

'''
if __name__ == "__main__":
    import platform
    import os
    
    #choose CLI or GUI on Raspberry Pi
    StartMode='general'   #options: 'sdl2', 'general'
        
    #on windows, override
    if platform.system()=='Windows':   
        StartMode='general'   
        
    if StartMode=='sdl2':
        '''This uses SDL2 as the backend
        This is intended for local CLI-mode operation (e.g. via a touchscreen)
        If you run this with the GUI, it will work and you can see it via
        VNC but it is cripplingly slow.
        I couldn't get the touch screen to work with SDL (won't coexist with mtdev properly)
        I couldn't get KMSDRM drivers to work at all (tried recompiling SDL with correct options and various other fixes - waste of several evenings)
        '''
        os.environ['KIVY_WINDOW']='sdl2'
        os.environ['KIVY_TEXT']='sdl2'
        os.environ['KIVY_BCM_DISPMANX_ID']='2' #HDMI
        os.environ['KIVY_GL_BACKEND']='sdl2'
        
    if StartMode=='general':  #general operation - remove any special settings
        '''
        When run with the GUI, it chooses the egl_rpi backend.  The app
        runs and can be seen only on the HDMI display (full screen). VNC
        viewer cannot display the app.  It runs nice and fast.
        '''
        pass
        
 
    

from gh_db import gh_db
from kivy.event import EventDispatcher
from kivy.clock import Clock
from process_control import pr_cont
from gh_io_dispatcher import gh_io_dispatcher
import gh_io_graph


#MAIN CODE
if __name__ == "__main__":
    from kivy.app import App
    from kivy.core.window import Window
    from kivy.uix.button import Button
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.textinput import TextInput
    from kivy.uix.widget import Widget
    from kivy.logger import Logger
    from gh_io_status_grid import gh_io_status_grid
    from kivy.graphics import Color, Ellipse, Rectangle, RoundedRectangle
    import sys
    import multiprocessing
    from time import sleep
    
    
    class RootWidget(BoxLayout):
        def __init__(self, **kwargs):
            self.orientation='horizontal'
            super(RootWidget, self).__init__(**kwargs)
            
            b1=Button(text='Exit',size_hint=(0.3,1))
            b1.bind(on_release=self.quit_app)
            
            self.ti1=BoxLayout()
                      
            self.add_widget(self.ti1)
            self.add_widget(b1)
                                 
            
        def start_io(self):
            self._gio=gh_io_dispatcher()
            self._gio.start_io()
                                       
                                 
            io_desc=self._gio.io_query('OPDESC?',0,15)  #command,data,timeout - need long timeout if using spawn instead of fork
            Logger.info("init_io: IO Descriptions:")
            if io_desc is not None:
                Logger.info(io_desc)
            else:
                Logger.exception("init_io: OPDESC? Query Timed Out (No response from gh_io process)")
                sys.exit(1)
        
            #Build the status grid - see gh_io_status_grid.py
            #self.statusgrid=gh_io_status_grid(all_op_desc=io_desc)
            #self.ti1.add_widget(self.statusgrid) 
            #self._gio.bind(on_io_data=self._process_io_data)
            
            #Graph
            self._db_manager=self._gio.get_db_manager()
            db=self._db_manager.get_database('Probe 1','Temp')
            self.io_graph=gh_io_graph.gh_io_graph(db=db)
            self.ti1.add_widget(self.io_graph)
             
            #Start IO running
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
       
    if platform.system()=='Linux':
        multiprocessing.set_start_method('fork')
    pr_cont.set_proctitle('gh_main process') #allows process to be idenfified in htop
    pr_cont.set_name('kivy main') #allows process to be idenfified in htop
    gh_db_dispatcher_test_app().run()