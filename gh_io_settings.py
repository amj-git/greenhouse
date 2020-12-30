'''
Settings Screens

Based on Kivy settings framework see https://kivy.org/doc/stable/api-kivy.app.html

The screens are customised to match the menus and to allow easier
scrolling with a resistive touchscreen on the RPI

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
from kivy.uix.settings import Settings, ContentPanel, MenuSidebar,\
    InterfaceWithTabbedPanel, InterfaceWithSidebar, SettingSidebarLabel, \
    SettingOptions
from kivy.uix.scrollview import ScrollView
from kivy.uix.tabbedpanel import TabbedPanelHeader
from kivy.uix.floatlayout import FloatLayout
from kivy.logger import Logger
from kivy.properties import ObjectProperty, StringProperty, ListProperty, \
BooleanProperty, NumericProperty, DictProperty
import importlib

fsize1='22sp'

#START SETTINGS GUI DEFINITIONS------------------------

#Note that the Kivy classes below are set up in gh_gui.kv

class SettingDynamicOptions(SettingOptions):
    '''Implementation of an option list that creates the items in the possible
    options list by calling an external method, that should be defined in
    the settings class.
    '''
    
    function_string = StringProperty()
    '''The function's name to call each time the list should be updated.
    It should return a list of strings, to be used for the options.
    '''
    
    def _create_popup(self, instance):
        # Update the options
        mod_name, func_name = self.function_string.rsplit('.',1)
        mod = importlib.import_module(mod_name)
        func = getattr(mod, func_name)
        self.options = func()
    
        # Call the parent __init__
        super(SettingDynamicOptions, self)._create_popup(instance)

#settings panel based on the Kivy settings framework with some customisation
class gh_SettingsPanel(Settings):
 
    __events__ = ('on_close', )

    def __init__(self, *args, **kwargs):
        self.interface_cls = gh_SettingsInterface
        super(gh_SettingsPanel, self).__init__(*args, **kwargs)
        self.register_type('dynamic_options', SettingDynamicOptions)
 
    def on_close(self):
        Logger.info("main.py: MySettingsWithTabbedPanel.on_close")

    def on_config_change(self, config, section, key, value):
        Logger.info(
            "main.py: MySettingsWithTabbedPanel.on_config_change: "
            "{0}, {1}, {2}, {3}".format(config, section, key, value))
        
        
#Custom settings interface
class gh_SettingsInterface(BoxLayout):
    menu = ObjectProperty()
    content = ObjectProperty()   
    
    __events__ = ('on_close', )

    def __init__(self, *args, **kwargs):
        super(gh_SettingsInterface, self).__init__(*args, **kwargs)
        self.menu.close_button.bind(on_release=lambda j: self.dispatch('on_close'))

    def add_panel(self, panel, name, uid):
        self.menu.add_item(name, uid)
        self.content.add_panel(panel, name, uid)

    def on_close(self, *args):
        pass


#custom settings sidebar (based on MenuSidebar from settings.py)
class gh_MenuSidebar(FloatLayout):
    selected_uid = NumericProperty(0)
    buttons_layout = ObjectProperty(None)
    close_button = ObjectProperty(None)

    def add_item(self, name, uid):
        label = gh_SettingSidebarLabel(text=name, uid=uid, menu=self)
        if len(self.buttons_layout.children) == 0:
            label.selected = True
        if self.buttons_layout is not None:
            self.buttons_layout.add_widget(label)

    def on_selected_uid(self, *args):
        for button in self.buttons_layout.children:
            if button.uid != self.selected_uid:
                button.selected = False


#unconventional naming here as Kivy would not accept gh_ContentPanel as the name
class ContPanel_gh(ScrollView):
    panels = DictProperty({})
    container = ObjectProperty()
    current_panel = ObjectProperty(None)
    current_uid = NumericProperty(0)

    def add_panel(self, panel, name, uid):
        self.panels[uid] = panel
        if not self.current_uid:
            self.current_uid = uid

    def on_current_uid(self, *args):
        uid = self.current_uid
        if uid in self.panels:
            if self.current_panel is not None:
                self.remove_widget(self.current_panel)
            new_panel = self.panels[uid]
            self.add_widget(new_panel)
            self.current_panel = new_panel
            return True
        return False  # New uid doesn't exist

    def add_widget(self, widget):
        if self.container is None:
            super(ContPanel_gh, self).add_widget(widget)
        else:
            self.container.add_widget(widget)

    def remove_widget(self, widget):
        self.container.remove_widget(widget)


class gh_SettingSidebarLabel(SettingSidebarLabel):
    '''Inherit from settings.py
    Note the setup in gh_gui.kv is customised
    '''

#END SETTINGS GUI DEFINITIONS------------------------

#START CONFIG FUNCTIONS---------------------------
#example of how to dynamically provide options
def get_test_options():
    op=['option 1','option 2','option 3']
    return op

class gh_config:
    def __init__(self,config):
        self._config=config
        self.setdefaults()
        
    def setdefaults(self):
        self._config.setdefaults('Network', {
                                'IP':'0.0.0.0',
                                'SSID':'<No SSID>',
                                'dyntest':'<not set>'
                                })
        
    def build_settings(self,settings):
        #see .json files for details
        settings.add_json_panel('Network',self._config,'settings_net.json')

#END CONFIG FUNCTIONS---------------------------

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

        self.b2=Button(text='Kivy Settings...',state='normal')
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
        App.get_running_app().open_settings()
        
                
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
        self._ip_label=Label(text='IP Address',font_size=fsize1)
        self._ip_data=Label(text=my_ip_addr,font_size=fsize1)
        box.add_widget(self._ip_label)
        box.add_widget(self._ip_data)
        
        self.non_menu_root.add_widget(box)
        
        tx1=TextInput(text='Text')
        self.non_menu_root.add_widget(tx1)
        
            
    def page_jump1(self,*args):
        self.parent.current='settings_screen'
          
    
                   
    def b1_click(self,*args):
        pass
                
    def b2_click(self,*args):
        pass
                
    def b3_click(self,*args):
        pass    