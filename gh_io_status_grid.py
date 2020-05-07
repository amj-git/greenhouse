from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from led import Led

class gh_io_status_grid(BoxLayout):
    def __init__(self,**kwargs):
        self.orientation='vertical'
        BoxLayout.__init__(self)
        self._all_op_desc=kwargs.get('all_op_desc',None)
        self._controls=dict()
        self._statuslabel=dict()
        fsize1='22sp'
        chartreuse2=[118,238,0,1]
                
        #Create a TextInput control for each parameter
        for tname in self._all_op_desc: #for each thread name
            self._controls[tname]=dict()
            self._statuslabel[tname]=dict()
            for pname in self._all_op_desc[tname]:  #for each output parameter                
                lay=BoxLayout(orientation='horizontal')
                ti0=Led(size_hint=(0.1,1),source='shapes/basic_disc.png',auto_off=True,led_type='color')
                ti1=Label(size_hint=(1,1),font_size=fsize1)
                ti2=Label(size_hint=(0.25,1),markup=True,font_size='25sp',halign='right',valign='middle',color=[0.5,1,0,1])
                ti2.text_size=ti2.size
                ti3=Label(size_hint=(0.25,1),font_size='19sp',halign='left',valign='middle',color=[0.9,0.9,0.9,1])
                ti3.text_size=ti3.size
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
     
        self._controls[data['tname']][data['pname']].text=\
                        '[b]'+'{0:.2f}'.format(data['data'])+'[/b]'
        self._statuslabel[data['tname']][data['pname']].toggle_state()
        