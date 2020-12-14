'''
Settings Screen
'''

from kivy.app import App
from kivy.core.window import Window
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.uix.screenmanager import ScreenManager, Screen

class SettingsScreen(Screen):
    def __init__(self, **kwargs):
        super(SettingsScreen, self).__init__(**kwargs)
        self._subscreen=None
                    
        #ROOT STRUCTURE
        self.root_box=BoxLayout(orientation='horizontal')
        self.add_widget(self.root_box)
        self.non_menu_root=BoxLayout()
        self.root_box.add_widget(self.non_menu_root)
        self.menu_root=BoxLayout(orientation='vertical',size_hint=(0.3,1))
        self.root_box.add_widget(self.menu_root)
                                     
        #MENU
        self.b1=Button(text='Network...')
        self.b1.bind(on_release=self.b1_click)
        self.menu_root.add_widget(self.b1)

        self.b2=ToggleButton(text='Button2',state='normal')
        self.b2.bind(on_release=self.b2_click)
        self.menu_root.add_widget(self.b2)

        self.b3=ToggleButton(text='Button3',state='normal')
        self.b3.bind(on_release=self.b3_click)
        self.menu_root.add_widget(self.b3)
        
        b99=Button(text='Back',)
        b99.bind(on_release=self.page_jump1)
        self.menu_root.add_widget(b99)
                    
    def set_gio(self,gio):
        self._gio=gio
        
    def set_webserver(self,webserver):
        self._webserver=webserver
            
    def page_jump1(self,*args):
        self.parent.current='status_screen'
        
                   
    def b1_click(self,*args):
        if self._subscreen is not None:
            self.parent.remove_widget(self._subscreen)
            del self._subscreen
        self._subscreen=NetworkSettingsScreen(name='settings_sub_screen',webserver=self._webserver)
        self.parent.add_widget(self._subscreen)
        self.parent.current='settings_sub_screen'
                
    def b2_click(self,*args):
        pass
                
    def b3_click(self,*args):
        pass
        
        
class NetworkSettingsScreen(Screen):
    def __init__(self, **kwargs):
        self._webserver=kwargs.pop('webserver',None)
        super(NetworkSettingsScreen, self).__init__(**kwargs)
                    
        #ROOT STRUCTURE
        self.root_box=BoxLayout(orientation='horizontal')
        self.add_widget(self.root_box)
        self.non_menu_root=BoxLayout(orientation='vertical')
        self.root_box.add_widget(self.non_menu_root)
        self.menu_root=BoxLayout(orientation='vertical',size_hint=(0.3,1))
        self.root_box.add_widget(self.menu_root)
                                     
        #MENU
        self.b1=Button(text='Button1')
        self.b1.bind(on_release=self.b1_click)
        self.menu_root.add_widget(self.b1)

        self.b2=ToggleButton(text='Button2',state='normal')
        self.b2.bind(on_release=self.b2_click)
        self.menu_root.add_widget(self.b2)

        self.b3=ToggleButton(text='Button3',state='normal')
        self.b3.bind(on_release=self.b3_click)
        self.menu_root.add_widget(self.b3)
        
        b99=Button(text='Back',)
        b99.bind(on_release=self.page_jump1)
        self.menu_root.add_widget(b99)
        
        #NON-MENU
        my_ip_addr=self._webserver.get_server_ip()
        box=BoxLayout(orientation='horizontal')
        self._ip_label=Label(text='IP Address')
        self._ip_data=Label(text=my_ip_addr)
        box.add_widget(self._ip_label)
        box.add_widget(self._ip_data)
        
        self.non_menu_root.add_widget(box)
        
        
            
    def page_jump1(self,*args):
        self.parent.current='settings_screen'
          
    
                   
    def b1_click(self,*args):
        pass
                
    def b2_click(self,*args):
        pass
                
    def b3_click(self,*args):
        pass    