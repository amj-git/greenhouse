from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput

class gh_io_status_grid(BoxLayout):
    def __init__(self,**kwargs):
        self.orientation='vertical'
        BoxLayout.__init__(self)
        self._all_op_desc=kwargs.get('all_op_desc',None)
        self._controls=dict()
        
                
        #Create a TextInput control for each parameter
        for tname in self._all_op_desc: #for each thread name
            self._controls[tname]=dict()
            for pname in self._all_op_desc[tname]:  #for each output parameter                
                lay=BoxLayout(orientation='horizontal')
                ti1=TextInput()
                ti2=TextInput()
                ti3=TextInput()
                self._controls[tname][pname]=ti2
                lay.add_widget(ti1)
                lay.add_widget(ti2)
                lay.add_widget(ti3)
                ti1.text=str(tname)+"/"+str(pname)
                ti3.text=str(self._all_op_desc[tname][pname]['punits'])
                self.add_widget(lay)
        
    def process_data(self,data):
        self._controls[data['tname']][data['pname']].text=\
                        str(data['data'])