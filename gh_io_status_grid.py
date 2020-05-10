from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from led import Led

'''gh_io_status_grid

See https://github.com/amj-git/greenhouse/wiki/gh_io_status_grid

'''

LED_COL_BLUE_OFF = [0.05,0.175,0.225,1]
LED_COL_BLUE_ON  = [0.22,0.79,1.0,1]
LED_COL_RED_OFF = [0.2,0.0,0.0,1]
LED_COL_RED_ON  = [1.00,0.0,0.0,1]
LED_COL_YEL_OFF = [0.14,0.14,0.0,1]
LED_COL_YEL_ON  = [1.0,1.0,0.0,1]

class gh_io_status_grid(BoxLayout):
    def __init__(self,**kwargs):
        self.orientation='vertical'
        BoxLayout.__init__(self)
        self._all_op_desc=kwargs.get('all_op_desc',None)
        self._controls=dict()
        self._statuslabel=dict()
        fsize1='22sp'
                        
        #Create a TextInput control for each parameter
        for tname in self._all_op_desc: #for each thread name
            self._controls[tname]=dict()
            self._statuslabel[tname]=dict()
            for pname in self._all_op_desc[tname]:  #for each output parameter                
                lay=BoxLayout(orientation='horizontal')
                ti0=Led(size_hint=(0.1,1),source='shapes/basic_disc.png',\
                        auto_off=False,led_type='color',\
                        color_on=LED_COL_YEL_ON,color_off=LED_COL_YEL_OFF,\
                        ) #LED to pulse for activity
                ti0.state='on'  #Initially show that no data has been received
                ti1=Label(size_hint=(1,1),font_size=fsize1)  #Description
                ti2=Label(size_hint=(0.25,1),markup=True,\
                          font_size='25sp',halign='right',\
                          valign='middle',color=[0.5,1,0,1])  #Data
                ti3=Label(size_hint=(0.25,1),font_size='19sp',\
                          halign='left',valign='middle',\
                          color=[0.9,0.9,0.9,1])  #units
                self._controls[tname][pname]=ti2
                self._statuslabel[tname][pname]=ti0
                lay.add_widget(ti0)
                lay.add_widget(ti1)
                lay.add_widget(ti2)
                lay.add_widget(ti3)
                ti1.text=str(tname)+"/"+str(pname)
                ti3.text=" "+str(self._all_op_desc[tname][pname]['punits'])
                self.add_widget(lay)
        
            
    def process_data(self,data):
        #update the value
        self._controls[data['tname']][data['pname']].text=\
                        '[b]'+'{0:.2f}'.format(data['data'])+'[/b]'
        #pulse the LED to show progress
        lbl=self._statuslabel[data['tname']][data['pname']]
        lbl.color_on=LED_COL_BLUE_ON
        lbl.color_off=LED_COL_BLUE_OFF
        lbl.auto_off=True
        lbl.toggle_state()
        
