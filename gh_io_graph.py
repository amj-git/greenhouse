'''gh_io_graph

gh_io_graph - a graph designed to plot data from gh_io

gh_io_graph_screen - includes control buttons


'''


import kgraph
import gh_db_manager
from datetime import datetime, timedelta

class db_raw_line(kgraph.LinePlot):
    def __init__(self,**kwargs):
        self.set_database(kwargs.pop('db',None))
        super(db_raw_line, self).__init__(**kwargs)        
        
    def draw(self,*args):
        if self._db is not None:
            self.points=self._db.get_raw_line(self.params['xmin'],self.params['xmax'])        
        super(db_raw_line,self).draw(*args)

    def set_database(self,db):
        self._db=db


class gh_io_graph(kgraph.Graph):
    
    '''    gh_io_graph.__init__
            
            db - param_db object to plot
    
    '''
    def __init__(self,**kwargs):
        self.set_db_params(kwargs.pop('db',None))
        super(gh_io_graph, self).__init__(**kwargs)
        
        self._raw_line=db_raw_line(color=[1, 1, 0, 1],db=self._db)
        self.add_plot(self._raw_line)
        
    def set_db_params(self,db):
        self._db=db
        if self._db is not None:
            self._meta_data=self._db.get_meta_data()        
            self.xmax=gh_db_manager.datetime_to_timestamp(datetime.now())
            self.xmin=self.xmax-3*60*60*1000
            self.set_y_ticks()

    def set_database(self,db):
        self.set_db_params(db)
        self._raw_line.set_database(db)
        
        
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
        
    
    