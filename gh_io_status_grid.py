from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.behaviors import ButtonBehavior
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

LABEL_NORMAL_COL=[1.0,1.0,1.0,1]
LABEL_HIGHLIGHT_COL=[1.0,1.0,0.0,1]

#This is a label that can be bound to on_press
class tagged_label(ButtonBehavior, Label):
    def __init__(self,**kwargs):
        self.tname=kwargs.pop('tname',None)
        self.pname=kwargs.pop('pname',None)
        Label.__init__(self,**kwargs)
        ButtonBehavior.__init__(self)
    
        

class gh_io_status_grid(BoxLayout):
    def __init__(self,**kwargs):
        self.register_event_type('on_desc_click')
        self.orientation='vertical'
        BoxLayout.__init__(self)
        self._all_op_desc=kwargs.get('all_op_desc',None)
        self._controls=dict()
        self._statuslabel=dict()
        self._desclabel=dict()
        self._last_data=dict()
        self._dataitemindex=dict()
        self._webserver_newdata_fn=None
        fsize1='22sp'
                   
        itemindex=1     
        #Create a TextInput control for each parameter
        for tname in self._all_op_desc: #for each thread name
            self._controls[tname]=dict()
            self._statuslabel[tname]=dict()
            self._desclabel[tname]=dict()
            self._last_data[tname]=dict()
            self._dataitemindex[tname]=dict()
            for pname in self._all_op_desc[tname]:  #for each output parameter                
                lay=BoxLayout(orientation='horizontal')
                ti0=Led(size_hint=(0.1,1),source='shapes/basic_disc.png',\
                        auto_off=False,led_type='color',\
                        color_on=LED_COL_YEL_ON,color_off=LED_COL_YEL_OFF,\
                        ) #LED to pulse for activity
                ti0.state='on'  #Initially show that no data has been received
                ti1=tagged_label(size_hint=(1,1),font_size=fsize1,\
                                 tname=tname,pname=pname,\
                                 color=LABEL_NORMAL_COL)  #Description
                ti1.bind(on_press=self.desc_click )
                ti2=Label(size_hint=(0.25,1),markup=True,\
                          font_size='25sp',halign='right',\
                          valign='middle',color=[0.5,1,0,1])  #Data
                ti3=Label(size_hint=(0.25,1),font_size='19sp',\
                          halign='left',valign='middle',\
                          color=[0.9,0.9,0.9,1])  #units
                self._controls[tname][pname]=ti2
                self._last_data[tname][pname]=''
                self._statuslabel[tname][pname]=ti0
                self._desclabel[tname][pname]=ti1
                self._dataitemindex[tname][pname]=itemindex
                lay.add_widget(ti0)
                lay.add_widget(ti1)
                lay.add_widget(ti2)
                lay.add_widget(ti3)
                ti1.text=str(tname)+"/"+str(pname)
                ti3.text=" "+str(self._all_op_desc[tname][pname]['punits'])
                self.add_widget(lay)
                itemindex=itemindex+1
        
        #Set the highlight to the first item
         
        self.desc_click(None)
                    
    def set_webserver_newdata_fn(self,fn):
        self._webserver_newdata_fn=fn
    
    def process_data(self,data):
        #update the value
        self._controls[data['tname']][data['pname']].text=\
                        '[b]'+'{0:.2f}'.format(data['data'])+'[/b]'
        self._last_data[data['tname']][data['pname']]=\
                        '{0:.2f}'.format(data['data'])                        
        #pulse the LED to show progress
        lbl=self._statuslabel[data['tname']][data['pname']]
        lbl.color_on=LED_COL_BLUE_ON
        lbl.color_off=LED_COL_BLUE_OFF
        lbl.auto_off=True
        lbl.toggle_state()
               
        #send data to webserver if it's connected
        if self._webserver_newdata_fn is not None:
            webdata=dict()      
            webdata['val']=self._last_data[data['tname']][data['pname']]
            webdata['i']=self._dataitemindex[data['tname']][data['pname']]
            self._webserver_newdata_fn(webdata)
        
    def get_table_data(self):
        data=[]
        itemindex=1
        for tname in self._all_op_desc: #for each thread name
            for pname in self._all_op_desc[tname]:
                row=dict()
                row['desc']=self._desclabel[tname][pname].text
                row['tname']=tname
                row['pname']=pname
                row['val']=self._last_data[tname][pname]
                row['units']=self._all_op_desc[tname][pname]['punits']
                row['i']=itemindex
                data.append(row)
                itemindex=itemindex+1
        return data
        
    def desc_click(self,inst):
        if inst is None:
            self._sel_tname=list(self._all_op_desc)[0]
            self._sel_pname=list(self._all_op_desc[self._sel_tname])[0]
        else:
            lbl=self._desclabel[self._sel_tname][self._sel_pname]
            lbl.color=LABEL_NORMAL_COL
            self._sel_tname=inst.tname
            self._sel_pname=inst.pname
        lbl=self._desclabel[self._sel_tname][self._sel_pname]
        lbl.color=LABEL_HIGHLIGHT_COL
        #print("clicked")
        #print((self._sel_tname,self._sel_pname))
        data=((self._sel_tname,self._sel_pname))
        self.dispatch('on_desc_click',data)
        
    #fires when the description is clicked
    def on_desc_click(self,*args):
        pass  
