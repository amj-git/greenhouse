
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from k_circulardatetimepicker import TimeChooserPopup
from kivy.properties import ObjectProperty


class SchedLineEdit_gh(BoxLayout):
    
    v1=ObjectProperty()
    t1=ObjectProperty()
    t2=ObjectProperty()
    
    def __init__(self, *args, **kwargs):
        self._sched_line=kwargs.pop('sched_line',[])
        self._units=kwargs.pop('units','')
        super(SchedLineEdit_gh, self).__init__(*args, **kwargs)
        self.t1.bind(on_release=self.edit_time)
        self.t2.bind(on_release=self.edit_time)
        self.show_sched_line()
        
    def show_sched_line(self):
        if len(self._sched_line)==5:       
            self.v1.text="{0}".format(self._sched_line[0])+self._units
            self.t1.text="{:02d}:{:02d}".format(self._sched_line[1],self._sched_line[2])
            self.t2.text="{:02d}:{:02d}".format(self._sched_line[3],self._sched_line[4])
        else:
            self.show_title_line()
        
    def show_title_line(self):
        self.v1.text='Setting'
        self.v1.background_color: (0,0,1,1)
        self.t1.text='Start'
        self.t1.background_color: (0,0,1,1)
        self.t2.text='End'        
        self.t2.background_color: (0,0,1,1)
        
    def edit_time(self,instance):
        s=self._sched_line
        h=0
        m=0
        if instance==self.t1:
            h=s[1]
            m=s[2]
            self._active_editor='t1'
        if instance==self.t2:
            h=s[3]
            m=s[4]
            self._active_editor='t2'        
        tc=TimeChooserPopup()   
        tc.picker.hours=h
        tc.picker.minutes=m            
        tc.bind(on_ok=self.set_time)
        tc.open()

    def edit_value(self,*args):
        pass

    def set_time(self,instance):
        s=self._sched_line
        h=instance.picker.hours
        m=instance.picker.minutes
        if self._active_editor=='t1':
            s[1]=h
            s[2]=m
        elif self._active_editor=='t2':
            s[3]=h
            s[4]=m
        instance.dismiss()
        self._sched_line=s
        self.show_sched_line()
        
    def get_sched(self):
        return self._sched_line

class SchedEdit_gh(ScrollView):
    
    container=ObjectProperty()
    
    def load_sched(self,sched,units):
        self._sched=sched
        self.container.clear_widgets()
        l=SchedLineEdit_gh()
        self.container.add_widget(l)  #add title
        print(self._sched)
        for peg in self._sched:
            l=SchedLineEdit_gh(sched_line=peg,units=units)
            self.container.add_widget(l)
            
    def get_sched(self):
        s=[]
        for line in self.container.children:
            s.append(line.get_sched())
        return s
    