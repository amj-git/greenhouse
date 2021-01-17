
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
        super(SchedLineEdit_gh, self).__init__(*args, **kwargs)
        self.show_sched_line()
        
    def show_sched_line(self):
        if len(self._sched_line)==5:       
            self.v1.text="{0}".format(self._sched_line[0])
            self.t1.text="{:02d}:{:02d}".format(self._sched_line[1],self._sched_line[2])
            self.t2.text="{:02d}:{:02d}".format(self._sched_line[3],self._sched_line[4])
        else:
            self.show_title_line()
        
    def show_title_line(self):
        self.v1.text='Setting'
        self.t1.text='Start'
        self.t2.text='End'        
        
    def edit_time(self):
        tc=TimeChooserPopup()                               
        tc.bind(on_ok=self.set_time)
        tc.open()

    def set_time(self,instance):
        h=instance.picker.hours
        m=instance.picker.minutes
        print("gh_gui.Heater.set_time h=",h,"m=",m)
        instance.dismiss()

class SchedEdit_gh(ScrollView):
    
    container=ObjectProperty()
    
    def load_sched(self,sched):
        self._sched=sched
        self.container.clear_widgets()
        l=SchedLineEdit_gh()
        self.container.add_widget(l)  #add title
        print(self._sched)
        for peg in self._sched:
            l=SchedLineEdit_gh(sched_line=peg)
            self.container.add_widget(l)