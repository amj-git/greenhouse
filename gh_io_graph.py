'''gh_io_graph

gh_io_graph - a graph designed to plot data from gh_io

gh_io_graph_screen - includes control buttons


'''


import kgraph
import gh_db_manager
from datetime import datetime, timedelta
from kivy.graphics import Line, RenderContext
from kivy.properties import NumericProperty, BooleanProperty,\
    BoundedNumericProperty, StringProperty, ListProperty, ObjectProperty,\
    DictProperty, AliasProperty
from kivy.graphics import Mesh, Color, Rectangle, Point
import sys,traceback

MAX_RAW_POINTS=16000  #don't try to draw raw points for more than this much data

''' Plotter for raw_data
    The maximum number of vertex instructions is around 30000, which
    is the limit to the number of points that can be plotted
    For PointPlot, exceeding this causes an exception
    For LinePlot, we get data corruption
    Need to use comp_data to deal with large timespans
'''
class db_raw_line(kgraph.PointPlot):
    def __init__(self,**kwargs):
        self.set_database(kwargs.pop('db',None))
        super(db_raw_line, self).__init__(**kwargs)
        #We override the draw function with code that gets the points from
        #the database.  We don't want this to trigger draw again.  So we
        #unbind the trigger from the points property...
        self.unbind(points=self.ask_draw)      
        
    def draw(self,*args):
        if self._db is not None:
            self.points=self._db.get_raw_line(self.params['xmin'],self.params['xmax'])
        
        #if it's too long, just display the centre
        k=len(self.points)    
        if k>MAX_RAW_POINTS:
            k0=round(0.5*(k-MAX_RAW_POINTS))
            k1=round(0.5*(k+MAX_RAW_POINTS))
            self.points=self.points[k0:k1]
        super(db_raw_line,self).draw(*args)

    def set_database(self,db):
        self._db=db

''' Plotter for comp_data
    
'''
class db_comp_line(kgraph.Plot):
    rect_color = ListProperty([1, 1, 1, 1])
    
    def __init__(self,**kwargs):
        self.set_database(kwargs.pop('db',None))
        super(db_comp_line, self).__init__(**kwargs)
        self.unbind(points=self.ask_draw)      

    def create_drawings(self):
        self._grc = RenderContext(
                use_parent_modelview=True,
                use_parent_projection=True)
        with self._grc:
            self._rectcolor = Color(*self.rect_color)
            self._mesh2=Mesh(mode='triangles')
            self._gcolor = Color(*self.color)
            self._mesh1=Mesh(mode='lines')
        self.bind(
            color=lambda instr, value: setattr(self._gcolor, "rgba", value))
        return [self._grc]

    def draw(self, *args):
        if self._db is not None:
            comp_data=self._db.get_comp_line(self.params['xmin'],self.params['xmax'])
            avg_data=[]
            min_data=[]
            max_data=[]
            for d in comp_data:
                avg_data.append((d[0],d[1]))
                min_data.append((d[0],d[2]))
                max_data.append((d[0],d[3]))       
        
        super(db_comp_line, self).draw(*args) #this clears the graph
        
        x_px = self.x_px()
        y_px = self.y_px()
        
        
        #Initialize a stepped line for the average
        mesh_avg=self._mesh1
        vert_avg=mesh_avg.vertices
        vert_avg=[0]*(8*len(comp_data))
        mesh_avg.indices=[k for k in range(len(comp_data) * 2)]
        
        #Initialize a set of rectangles for the min/max
        mesh_rect=self._mesh2
        vert_rect=mesh_rect.vertices
        vert_rect=[0]*(24*len(comp_data)) #each rect takes 24 points
        mesh_rect.indices=[k for k in range(len(comp_data) * 6)]
        
        #loop through the data
        last_x1=0
        for k, (x1, yavg, ymin, ymax) in enumerate(comp_data):
            x0=x1-self._Tchunk
            if x0<last_x1:
                x0=last_x1        #prevent overlap
            last_x1=x1
                
            #Add stepped line for average
            vert_avg[k*8]=x_px(x0)   #x0
            vert_avg[k*8+1]=y_px(yavg)  #y0
            vert_avg[k*8+4]=x_px(x1) #x1
            vert_avg[k*8+5]=y_px(yavg)  #y1
            
            x1t=x_px(x0)
            x2t=x_px(x1)
            y1t=y_px(ymin)
            y2t=y_px(ymax)
            
            #Add rectangles for min/max extents
            idx = k * 24
            # first triangle
            vert_rect[idx] = x1t
            vert_rect[idx + 1] = y2t
            vert_rect[idx + 4] = x1t
            vert_rect[idx + 5] = y1t
            vert_rect[idx + 8] = x2t
            vert_rect[idx + 9] = y1t
            # second triangle
            vert_rect[idx + 12] = x1t
            vert_rect[idx + 13] = y2t
            vert_rect[idx + 16] = x2t
            vert_rect[idx + 17] = y2t
            vert_rect[idx + 20] = x2t
            vert_rect[idx + 21] = y1t
            
        mesh_avg.vertices = vert_avg
        mesh_rect.vertices = vert_rect
        
               
    def set_database(self,db):
        self._db=db
        if db is not None:
            self._Tchunk=db.get_Tchunk()

class gh_io_graph(kgraph.Graph):
    
    '''    gh_io_graph.__init__
            
            db - param_db object to plot
    
    '''
    def __init__(self,**kwargs):
        self.set_db_params(kwargs.pop('db',None))
        super(gh_io_graph, self).__init__(**kwargs)
        
        self._raw_line=db_raw_line(color=[1, 1, 0, 1],db=self._db)
        self._comp_line=db_comp_line(color=[1, 1, 1, 1],rect_color=[1, 1, 0, 0.55],db=self._db)
        self.add_plot(self._comp_line)
        self.add_plot(self._raw_line)
        
    def set_db_params(self,db):
        self._db=db
        if self._db is not None:
            self._meta_data=self._db.get_meta_data()        
            self.set_y_ticks()

    def set_database(self,db):
        self.set_db_params(db)
        self._raw_line.set_database(db)
        self._comp_line.set_database(db)
        
        
    def set_y_ticks(self):      
        self.ylabel=self._meta_data['pdesc']+' ('+self._meta_data['punits']+')'        
        self.ymin=self._meta_data['pmin']
        self.ymax=self._meta_data['pmax']
        self.ylog=False
        self.y_ticks_minor=False
        ptype=self._meta_data['ptype']
        if ptype=='temp':
            self.y_ticks_major=10.0
        elif ptype=='humid':
            self.y_ticks_major=10.0            
        elif ptype=='light':
            self.y_ticks_major=1  #tick every decade
            self.y_ticks_minor=10
            self.ymin=0.1
            self.ylog=True
        else:
            self.y_ticks_major=10.0
        
    
    