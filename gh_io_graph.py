'''gh_io_graph

gh_io_graph - a graph designed to plot data from gh_io

gh_io_graph_screen - includes control buttons


'''


import kgraph
import gh_db_manager
from datetime import datetime, timedelta
import sys,traceback

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
        super(db_raw_line,self).draw(*args)

    def set_database(self,db):
        self._db=db

''' Plotter for comp_data
    
'''
class db_comp_line(kgraph.LinePlot):
    def __init__(self,**kwargs):
        self.set_database(kwargs.pop('db',None))
        super(db_comp_line, self).__init__(**kwargs)
        self.unbind(points=self.ask_draw)      
        
    def draw(self,*args):
        if self._db is not None:
            comp_data=self._db.get_comp_line(self.params['xmin'],self.params['xmax'])
            avg_data=[]
            min_data=[]
            max_data=[]
            for d in comp_data:
                avg_data.append((d[0],d[1]))
                min_data.append((d[0],d[2]))
                max_data.append((d[0],d[3]))
            self.points=avg_data
        super(db_comp_line,self).draw(*args)

    def set_database(self,db):
        self._db=db

class gh_io_graph(kgraph.Graph):
    
    '''    gh_io_graph.__init__
            
            db - param_db object to plot
    
    '''
    def __init__(self,**kwargs):
        self.set_db_params(kwargs.pop('db',None))
        super(gh_io_graph, self).__init__(**kwargs)
        
        self._raw_line=db_raw_line(color=[1, 1, 0, 0.5],db=self._db)
        self._comp_line=db_comp_line(color=[1, 0, 0, 1],db=self._db)
        self.add_plot(self._raw_line)
        self.add_plot(self._comp_line)
        
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
        
    
    