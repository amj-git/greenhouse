
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from k_circulardatetimepicker import TimeChooserPopup
from k_floatknob import FloatKnobPopup
from kivy.properties import ObjectProperty
import datetime

LABEL_NORMAL_COL=[1.0,1.0,1.0,1]
LABEL_WARN_COL=[1.0,0.0,0.0,1]
LABEL_HIGHLIGHT_COL=[1.0,1.0,0.0,1]

class SchedLineEdit_gh(BoxLayout):
    
    v1=ObjectProperty()
    t1=ObjectProperty()
    t2=ObjectProperty()
    
    def __init__(self, *args, **kwargs):
        self._sched_line=kwargs.pop('sched_line',[])
        self.on_select=kwargs.pop('on_select',None)
        self.on_update=kwargs.pop('on_update',None)
        self._units=kwargs.pop('units','')
        self.tc=kwargs.pop('tc',None)
        self.vc=kwargs.pop('vc',None)
        self.val_type=kwargs.pop('val_type','temp')  #temp or light
        super(SchedLineEdit_gh, self).__init__(*args, **kwargs)
        self.t1.bind(on_release=self.edit_time)
        self.t2.bind(on_release=self.edit_time)
        self.show_sched_line()
        
    def show_sched_line(self):
        if len(self._sched_line)==5:       
            self.v1.text="{0}".format(self._sched_line[0])+' '+self._units
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
        if self.on_select is not None:
            self.on_select(self)
        if len(s)==5:
            h=0
            m=0
            tc=self.tc 
            if instance==self.t1:
                h=s[1]
                m=s[2]
                self._active_editor='t1'
                tc.title='Choose Start Time'
            if instance==self.t2:
                h=s[3]
                m=s[4]
                self._active_editor='t2'    
                tc.title='Choose End Time'    
            print("Hours=",h)
            tc.picker.hours=h
            tc.picker.minutes=m            
            tc.bind(on_ok=self.set_time)
            tc.bind(on_cancel=self.on_cancel_time)
            tc.open()

    def edit_value(self,*args):
        s=self._sched_line
        if self.on_select is not None:
            self.on_select(self)
        if len(s)==5:
            vc=self.vc             
            vc.picker.units=self._units
            if self.val_type=='temp': #temperature
                vc.title='Choose Temperature'
                vc.picker.min=-10
                vc.picker.max=40
                vc.picker.step=0.5
            elif self.val_type=='light': #temperature
                vc.title='Choose Light Target'
                vc.picker.min=0
                vc.picker.max=20000
                vc.picker.step=100
                vc.picker.marker_img= "shapes/blacktoyellow.png"
            vc.picker.value=s[0]
            vc.bind(on_ok=self.set_val)
            vc.bind(on_cancel=self.on_cancel_val)
            vc.open()

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
        instance.unbind(on_ok=self.set_time)  #remove the binding as we re-use the form!
        instance.dismiss()
        self._sched_line=s
        self.show_sched_line()
        self.on_update(self)
    
    def set_val(self,instance):
        s=self._sched_line
        v=instance.picker.value
        if self.val_type=='temp':
            s[0]=round(v*2)/2
        elif self.val_type=='light':
            s[0]=round(v/100)*100
        instance.unbind(on_ok=self.set_val)  #remove the binding as we re-use the form!
        instance.dismiss()
        self._sched_line=s
        self.show_sched_line()
        self.on_update(self)

    def on_cancel_time(self,instance):
        instance.unbind(on_ok=self.set_time)  #remove the binding as we re-use the form!
        instance.dismiss()
        self.on_update(self)        
        
    def on_cancel_val(self,instance):
        instance.unbind(on_ok=self.set_val)  #remove the binding as we re-use the form!
        instance.dismiss()
        self.on_update(self)
        
    def get_sched(self):
        return self._sched_line
    
    def select_line(self):
        self.v1.color=LABEL_HIGHLIGHT_COL
        self.t1.color=LABEL_HIGHLIGHT_COL
        self.t2.color=LABEL_HIGHLIGHT_COL
        
    def deselect_line(self):
        self.v1.color=LABEL_NORMAL_COL
        self.t1.color=LABEL_NORMAL_COL
        self.t2.color=LABEL_NORMAL_COL
        
    def warn_t1(self):
        self.t1.color=LABEL_WARN_COL

    def warn_t2(self):
        self.t2.color=LABEL_WARN_COL

        
        

class SchedEdit_gh(ScrollView):
    
    container=ObjectProperty()
    
    def __init__(self, *args, **kwargs):
        self.val_type=kwargs.pop('val_type','temp')  #temp or light
        super(SchedEdit_gh, self).__init__(*args, **kwargs)
        self.vc=FloatKnobPopup()  #value chooser - only create once to improve responsiveness
        self.tc=TimeChooserPopup()  #time chooser
        self.overlaps=False
    
    def load_sched(self,sched,units):
        self._units=units
        self.deselect_all_lines()
        self._sched=sched
        self.container.clear_widgets()
        l=SchedLineEdit_gh()
        self.container.add_widget(l)  #add title
        print(self._sched)
        for peg in self._sched:
            print(peg)
            l=SchedLineEdit_gh(sched_line=peg,units=self._units,on_select=self.on_select,vc=self.vc,tc=self.tc,on_update=self.on_update,val_type=self.val_type)
            self.container.add_widget(l)
        self.selected_line=None
        
    #called when a line is selected    
    def on_select(self,instance):
        self.selected_line=instance
        self.deselect_all_lines()
        self.selected_line.select_line()
        
    #called when the table has been updated
    def on_update(self,instance):
        self.show_overlaps()        
                
    def deselect_all_lines(self):
        for line in self.container.children:
            line.deselect_line()
            
    #finds the index of a line in the container's child list.  Used
    #for adding an entry after the currently selected line
    def find_line_index(self,line):
        for i in range (0,len(self.container.children)):
            if line==self.container.children[i]:
                return i
        return 0
        
    def delete_current_line(self):
        if self.selected_line is not None:
            self.container.remove_widget(self.selected_line)
        self.selected_line=None
    
    def add_line(self):
        peg=[12,12,0,12,1]
        l=SchedLineEdit_gh(sched_line=peg,units=self._units,on_select=self.on_select,vc=self.vc,tc=self.tc,on_update=self.on_update,val_type=self.val_type)
        if self.selected_line is not None:
            sel_line_index=self.find_line_index(self.selected_line)
        else:
            sel_line_index=0
        self.container.add_widget(l,sel_line_index)
        self.on_select(l)
    
    def get_sched(self):
        s=[]
        lines=[]
        for line in reversed(self.container.children):  #reversed to get top to bottom order
            ldata=line.get_sched()
            if len(ldata)>0: #avoid the title line
                s.append(ldata)
                lines.append(line)
        return s, lines
    
    def has_overlaps(self):
        return self.overlaps
    
    def show_overlaps(self):
        self.overlaps=False
        s,lines=self.get_sched()
        for i in range(1,len(s)):
            l1=s[i-1]  #previous line
            l2=s[i]    #this line
            #print(s[i])
            t1=datetime.time(hour=l1[3],minute=l1[4])
            t2=datetime.time(hour=l2[1],minute=l2[2])
            if t1>t2:   #overlap
                #print("OVERLAP")
               lines[i-1].warn_t2()  #highlight the overlapping times 
               lines[i].warn_t1() #highlight the overlapping times
               self.overlaps=True