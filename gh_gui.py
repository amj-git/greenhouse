
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
from kivy.uix.label import Label
import gh_io_graph


#MAIN CODE
if __name__ == "__main__":
    from kivy.app import App
    from kivy.core.window import Window
    from kivy.uix.button import Button
    from kivy.uix.togglebutton import ToggleButton
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.anchorlayout import AnchorLayout
    from kivy.uix.textinput import TextInput
    from kivy.uix.widget import Widget
    import gh_db_manager
    from datetime import datetime, timedelta    
    from kivy.uix.screenmanager import ScreenManager, Screen
    from kivy.logger import Logger
    from gh_io_status_grid import gh_io_status_grid
    from kivy.graphics import Color, Ellipse, Rectangle, RoundedRectangle
    import sys
    import multiprocessing
    from time import sleep
    from gh_webserver import gh_webserver
    
    XLABELSTR='Span '
    
    #Millisecond quantities
    M_SEC=1000
    M_MINUTE=60*1000
    M_HOUR=60*M_MINUTE
    M_DAY=24*M_HOUR
    M_WEEK=7*M_DAY
    M_MONTH=30*M_DAY

    #available spans
    xzoomlevels=[   12*M_MONTH,\
                    6*M_MONTH,\
                    3*M_MONTH,\
                    1*M_MONTH,\
                    2*M_WEEK,\
                    1*M_WEEK,\
                    5*M_DAY,\
                    2*M_DAY,\
                    1*M_DAY,\
                    12*M_HOUR,\
                    6*M_HOUR,\
                    3*M_HOUR,\
                    1*M_HOUR,\
                    30*M_MINUTE,\
                    10*M_MINUTE,\
                    5*M_MINUTE,\
                    2*M_MINUTE,\
                    1*M_MINUTE]   
    
    #corresponding major tick spacing
    xtickspacing=[  1*M_MONTH,\
                    1*M_MONTH,\
                    1*M_MONTH,\
                    4*M_WEEK,\
                    2*M_DAY,\
                    1*M_DAY,\
                    1*M_DAY,\
                    12*M_HOUR,\
                    2*M_HOUR,\
                    1*M_HOUR,\
                    1*M_HOUR,\
                    1*M_HOUR,\
                    10*M_MINUTE,\
                    5*M_MINUTE,\
                    2*M_MINUTE,\
                    1*M_MINUTE,\
                    20*M_SEC,\
                    10*M_SEC]
        
    
    class SprinklerScreen(Screen):
        def __init__(self, **kwargs):
            super(SprinklerScreen, self).__init__(**kwargs)
            
            self.hose_state=0
            self.sprink1_state=0
            self.sprink2_state=0
            self.state_names=['AUTO','OFF','ON']
            
            #ROOT STRUCTURE
            self.root_box=BoxLayout(orientation='horizontal')
            self.add_widget(self.root_box)
            self.non_menu_root=BoxLayout()
            self.root_box.add_widget(self.non_menu_root)
            self.menu_root=BoxLayout(orientation='vertical',size_hint=(0.3,1))
            self.root_box.add_widget(self.menu_root)
                                         
            #MENU
            self.b1=Button(text='HOSE',)
            self.b1.bind(on_release=self.hoseclick)
            self.menu_root.add_widget(self.b1)

            self.b2=Button(text='SPRINKLER 1',)
            self.b2.bind(on_release=self.s1click)
            self.menu_root.add_widget(self.b2)

            self.b3=Button(text='SPRINKLER 2',)
            self.b3.bind(on_release=self.s2click)
            self.menu_root.add_widget(self.b3)
            
            b99=Button(text='Back',)
            b99.bind(on_release=self.page_jump1)
            self.menu_root.add_widget(b99)
            
        def set_gio(self,gio):
            self._gio=gio    
        
        def page_jump1(self,*args):
            self.parent.current='status_screen'
            
        def cycle_item(self,x,max):
            x=x+1
            if x>max:
                x=0
            return x               
                       
        def hoseclick(self,*args):
            self.hose_state=self.cycle_item(self.hose_state,2)
            self.b1.text='HOSE '+self.state_names[self.hose_state]
            self._gio.send_io_command('SPRINK:MODE','0,'+self.state_names[self.hose_state])
                    
        def s1click(self,*args):
            self.sprink1_state=self.cycle_item(self.sprink1_state,2)
            self.b2.text='SPRINKLER 1 '+self.state_names[self.sprink1_state]
            self._gio.send_io_command('SPRINK:MODE','1,'+self.state_names[self.sprink1_state])
                    
        def s2click(self,*args):
            self.sprink2_state=self.cycle_item(self.sprink2_state,2)
            self.b3.text='SPRINKLER 2 '+self.state_names[self.sprink2_state]
            self._gio.send_io_command('SPRINK:MODE','2,'+self.state_names[self.sprink2_state])
            
            
    class HeaterScreen(Screen):
        def __init__(self, **kwargs):
            super(HeaterScreen, self).__init__(**kwargs)
            
                        
            #ROOT STRUCTURE
            self.root_box=BoxLayout(orientation='horizontal')
            self.add_widget(self.root_box)
            self.non_menu_root=BoxLayout()
            self.root_box.add_widget(self.non_menu_root)
            self.menu_root=BoxLayout(orientation='vertical',size_hint=(0.3,1))
            self.root_box.add_widget(self.menu_root)
                                         
            #MENU
            self.b1=ToggleButton(text='HEATER OFF',state='normal')
            self.b1.bind(on_release=self.heateroffclick)
            self.menu_root.add_widget(self.b1)

            self.b2=ToggleButton(text='HEATER AUTO',state='normal')
            self.b2.bind(on_release=self.heaterautoclick)
            self.menu_root.add_widget(self.b2)

            self.b3=ToggleButton(text='HEATER BOOST',state='normal')
            self.b3.bind(on_release=self.heaterboostclick)
            self.menu_root.add_widget(self.b3)
            
            b99=Button(text='Back',)
            b99.bind(on_release=self.page_jump1)
            self.menu_root.add_widget(b99)
                        
        def set_gio(self,gio):
            self._gio=gio
                
        def page_jump1(self,*args):
            self.parent.current='status_screen'
            
        def map_key_state(self,bool_state):
            if bool_state:
                return 'down'
            else:
                return 'normal'
            
        #read back the current heater mode
        def get_mode(self):
            mode=self._gio.io_query('HEATER:MODE?',0,1)
            self.b1.state=self.map_key_state((mode=='OFF'))
            self.b2.state=self.map_key_state(mode=='AUTO')
            self.b3.state=self.map_key_state(mode=='BOOST')
                       
        def heateroffclick(self,*args):
            self._gio.send_io_command('HEATER:MODE','OFF')
            self.get_mode()
                    
        def heaterautoclick(self,*args):
            self._gio.send_io_command('HEATER:MODE','AUTO')
            self.get_mode()
                    
        def heaterboostclick(self,*args):
            self._gio.send_io_command('HEATER:MODE','BOOST')
            self.get_mode()
            
    
         
    class LightingScreen(Screen):
        def __init__(self, **kwargs):
            super(LightingScreen, self).__init__(**kwargs)
            
                        
            #ROOT STRUCTURE
            self.root_box=BoxLayout(orientation='horizontal')
            self.add_widget(self.root_box)
            self.non_menu_root=BoxLayout()
            self.root_box.add_widget(self.non_menu_root)
            self.menu_root=BoxLayout(orientation='vertical',size_hint=(0.3,1))
            self.root_box.add_widget(self.menu_root)
                                         
            #MENU
            self.b1=ToggleButton(text='LIGHT OFF',state='normal')
            self.b1.bind(on_release=self.heateroffclick)
            self.menu_root.add_widget(self.b1)

            self.b2=ToggleButton(text='LIGHT AUTO',state='normal')
            self.b2.bind(on_release=self.heaterautoclick)
            self.menu_root.add_widget(self.b2)

            self.b3=ToggleButton(text='LIGHT BOOST',state='normal')
            self.b3.bind(on_release=self.heaterboostclick)
            self.menu_root.add_widget(self.b3)
            
            b99=Button(text='Back',)
            b99.bind(on_release=self.page_jump1)
            self.menu_root.add_widget(b99)
                        
        def set_gio(self,gio):
            self._gio=gio
                
        def page_jump1(self,*args):
            self.parent.current='status_screen'
            
        def map_key_state(self,bool_state):
            if bool_state:
                return 'down'
            else:
                return 'normal'
            
        #read back the current heater mode
        def get_mode(self):
            mode=self._gio.io_query('LIGHT_CTRL:MODE?',0,1)
            self.b1.state=self.map_key_state((mode=='OFF'))
            self.b2.state=self.map_key_state(mode=='AUTO')
            self.b3.state=self.map_key_state(mode=='BOOST')
                       
        def heateroffclick(self,*args):
            self._gio.send_io_command('LIGHT_CTRL:MODE','OFF')
            self.get_mode()
                    
        def heaterautoclick(self,*args):
            self._gio.send_io_command('LIGHT_CTRL:MODE','AUTO')
            self.get_mode()
                    
        def heaterboostclick(self,*args):
            self._gio.send_io_command('LIGHT_CTRL:MODE','BOOST')
            self.get_mode()
            
            
                
    
    class IOStatusScreen(Screen):
        def __init__(self, **kwargs):
            self._graph_screen=kwargs.pop('graph_screen',None)
            super(IOStatusScreen, self).__init__(**kwargs)
            
            #ROOT STRUCTURE
            self.root_box=BoxLayout(orientation='horizontal')
            self.add_widget(self.root_box)
            self.non_menu_root=BoxLayout()
            self.root_box.add_widget(self.non_menu_root)
            self.menu_root=BoxLayout(orientation='vertical',size_hint=(0.3,1))
            self.root_box.add_widget(self.menu_root)
                                         
            #MENU
            b1=Button(text='Graph...',)
            b1.bind(on_release=self.page_jump1)
            self.menu_root.add_widget(b1)
            
            b12=Button(text='Sprinkler...',)
            b12.bind(on_release=self.page_jump2)
            self.menu_root.add_widget(b12)

            b13=Button(text='Heater...',)
            b13.bind(on_release=self.page_jump3)
            self.menu_root.add_widget(b13)
            
            b14=Button(text='Lighting...',)
            b14.bind(on_release=self.page_jump4)
            self.menu_root.add_widget(b14)            
            
            b2=Button(text='Exit',)
            b2.bind(on_release=self.quit_app)
            self.menu_root.add_widget(b2)
            
        def quit_app(self,*args):
            App.get_running_app().stop()    
            
        def start_io(self,gio,io_desc):
            #GRID
            self.statusgrid=gh_io_status_grid(all_op_desc=io_desc)
            self.non_menu_root.add_widget(self.statusgrid) 
            gio.bind(on_io_data=self.process_io_data)
            self.statusgrid.bind(on_desc_click=self.desc_click)
            self.statusgrid.desc_click(None) #force the db to be set
            
        def process_io_data(self,*args):
            self.statusgrid.process_data(args[1])
            
        def page_jump1(self,*args):
            self.parent.current='graph_screen'
            
        def page_jump2(self,*args):
            self.parent.current='sprinkler_screen'
            
        def page_jump3(self,*args):
            self.parent.current='heater_screen'        
            
        def page_jump4(self,*args):
            self.parent.current='lighting_screen'            
            
        def desc_click(self,*args):
            self._graph_screen.set_db(args[1])
            
    class IOGraphScreen(Screen):
        def __init__(self, **kwargs):
            super(IOGraphScreen, self).__init__(**kwargs)
            
            self._xzoom=13  #default xzoom level
            
            #ROOT STRUCTURE
            self.root_box=BoxLayout(orientation='horizontal')
            self.add_widget(self.root_box)
            self.non_menu_root=BoxLayout(orientation='vertical')
            self.root_box.add_widget(self.non_menu_root)
            self.menu_root=BoxLayout(orientation='vertical',size_hint=(0.3,1))
            self.root_box.add_widget(self.menu_root)
                                         
            #MENU
            b1=Button(text='Status...',)
            b1.bind(on_release=self.page_jump1)
            self.menu_root.add_widget(b1)
            
            b2=ToggleButton(text='Raw',state='down')
            b2.bind(on_release=self.refresh_graph)
            self.menu_root.add_widget(b2)
            self._raw_data_button=b2
            
            b3=ToggleButton(text='Compressed',state='down')
            b3.bind(on_release=self.refresh_graph)
            self.menu_root.add_widget(b3)
            self._comp_data_button=b3
            
            #NON-MENU
            self.graph_title=Label(color=[1,1,1,1],size=(400,25),size_hint=(1,None))
            self.non_menu_root.add_widget(self.graph_title)
            self.io_graph=gh_io_graph.gh_io_graph(db=None,\
                                                  x_ticks_major=60*60*1000,\
                                                  x_ticks_minor=0,\
                                                  padding=5,\
                                                  x_grid=True,\
                                                  y_grid=True,\
                                                  y_grid_label=True,\
                                                  x_grid_label=False)
            self.b_gohome()
            self.set_zoom()
            self.non_menu_root.add_widget(self.io_graph)

            #Navigation Buttons
            navbuttons=BoxLayout(orientation='horizontal',size_hint=(1,0.15))
            self.non_menu_root.add_widget(navbuttons)
            
            b_left=Button(text='<',)
            b_left.bind(on_press=self.b_left)
            navbuttons.add_widget(b_left)

            b_zoomout=Button(text='-')
            b_zoomout.bind(on_press=self.b_zoomout)
            navbuttons.add_widget(b_zoomout)
            
            b_zoomin=Button(text='+')
            b_zoomin.bind(on_press=self.b_zoomin)
            navbuttons.add_widget(b_zoomin)
                       
            b_right=Button(text='>')
            b_right.bind(on_press=self.b_right)
            navbuttons.add_widget(b_right)
            
            b_gohome=Button(text='>>')
            b_gohome.bind(on_press=self.b_gohome)
            navbuttons.add_widget(b_gohome)            
            
            
        def set_zoom(self):
            graph=self.io_graph
            xcentre=(graph.xmax+graph.xmin)/2
            hspan=xzoomlevels[self._xzoom]/2
            graph.xmin=xcentre-hspan
            graph.xmax=xcentre+hspan
            graph.x_ticks_major=xtickspacing[self._xzoom]
            graph.xlabel=XLABELSTR+self.get_span_string()
            
        
        def b_left(self,*args):
            graph=self.io_graph
            step=graph.x_ticks_major
            graph.xmin=graph.xmin-step
            graph.xmax=graph.xmax-step
                        
        def b_right(self,*args):
            graph=self.io_graph
            step=graph.x_ticks_major
            graph.xmin=graph.xmin+step
            graph.xmax=graph.xmax+step
                        
        def b_gohome(self,*args):
            graph=self.io_graph
            graph.xmax=gh_db_manager.datetime_to_timestamp(datetime.now())
            span=xzoomlevels[self._xzoom]
            graph.xmin=graph.xmax-span
            
        def b_zoomout(self,*args):
            if self._xzoom>0:
                self._xzoom=self._xzoom-1
            self.set_zoom()
             
        def b_zoomin(self,*args):
            if self._xzoom<(len(xzoomlevels)-1):
                self._xzoom=self._xzoom+1
            self.set_zoom()
            
        def quit_app(self,*args):
            App.get_running_app().stop()    
            
        def page_jump1(self,*args):
            self.parent.current='status_screen'
            
        def refresh_graph(self,*args):
            db=self._db_manager.get_database(self._sel_tname,self._sel_pname)
            self.io_graph.set_database(db)
            self.io_graph.set_visibility(self._raw_data_button.state=='down',\
                                         self._comp_data_button.state=='down')
            self.io_graph._redraw_all()
            
        #accepts (tname,pname)
        def set_db(self,p):
            (self._sel_tname,self._sel_pname)=p
            self.refresh_graph()
            t=self.graph_title
            t.text=str(self._sel_tname)+"/"+str(self._sel_pname)
            
        def start_io(self,gio,io_desc):
            #GRAPH
            self._db_manager=gio.get_db_manager()
            db=self._db_manager.get_database('Probe 1','Temp')
            self.io_graph.set_database(db)      
            
        #gets a string describing the span
        def get_span_string(self):
            graph=self.io_graph
            tstart=gh_db_manager.timestamp_to_datetime(graph.xmin)
            tstop=gh_db_manager.timestamp_to_datetime(graph.xmax)
            tdelta=tstop-tstart
            return(str(tdelta))
    
    class RootWidget(ScreenManager):
        def __init__(self, **kwargs):
            super(RootWidget, self).__init__(**kwargs)
            
            self.io_graph_screen=IOGraphScreen(name='graph_screen')
            
                                 
            self.io_status_screen=IOStatusScreen(name='status_screen',\
                                                 graph_screen=self.io_graph_screen)
            
            self.io_sprinkler_screen=SprinklerScreen(name='sprinkler_screen')
            
            self.io_heater_screen=HeaterScreen(name='heater_screen')
            
            self.io_lighting_screen=LightingScreen(name='lighting_screen')
            
            #add in this order so status screen shows first
            self.add_widget(self.io_status_screen)
            self.add_widget(self.io_graph_screen)
            self.add_widget(self.io_sprinkler_screen)
            self.add_widget(self.io_heater_screen)
            self.add_widget(self.io_lighting_screen)
            
            
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
        
            self.io_graph_screen.start_io(self._gio,io_desc)
            self.io_status_screen.start_io(self._gio,io_desc)
            self.io_sprinkler_screen.set_gio(self._gio)
            self.io_heater_screen.set_gio(self._gio)
            self.io_lighting_screen.set_gio(self._gio)
             
            #Start IO events running
            self._gio.start_events()
            
        def start_webserver(self):
            self.webserver=gh_webserver(self.io_status_screen.statusgrid,self._gio)
            self.webserver.start()    
        
        #this is the callback that is triggered by the io_q events
        def _process_io_data(self,*args):
            self.io_status_screen.process_data(args[1])
            #Logger.debug("gh_io_dispatcher:"+str(args[1]))
            
        def stop_io(self,*args):
            self._gio.stop_io()
            
        def quit_app(self,*args):
            App.get_running_app().stop()
            
            
    class gh_gui_app(App):
          
        def build(self):
            self._running=False
            self._rw=RootWidget()
            return self._rw  
    
        def on_start(self):        
            self._rw.start_io()
            self._rw.start_webserver()
            self._running=True
        
        def on_stop(self):        
            if self._running:  #prevent it running twice due to multiple clicks
                self._rw.stop_io()
                self._running=False
       
    if platform.system()=='Linux':
        multiprocessing.set_start_method('fork')
    pr_cont.set_proctitle('gh_main process') #allows process to be idenfified in htop
    pr_cont.set_name('kivy main') #allows process to be idenfified in htop
    gh_gui_app().run()