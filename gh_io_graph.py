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
        self.points=self._db.get_raw_line(self.params['xmin'],self.params['xmax'])        
        super(db_raw_line,self).draw(*args)

    def set_database(self,db):
        self._db=db


class gh_io_graph(kgraph.Graph):
    
    '''    gh_io_graph.__init__
            
            db - param_db object to plot
    
    '''
    def __init__(self,**kwargs):
        self.set_database(kwargs.pop('db',None))
        super(gh_io_graph, self).__init__(**kwargs)
        
        self._raw_line=db_raw_line(color=[1, 1, 0, 1],db=self._db)
        self.add_plot(self._raw_line)
        
    def set_database(self,db):
        self._db=db
        self._meta_data=self._db.get_meta_data()        
        self.ymin=self._meta_data['pmin']
        self.ymax=self._meta_data['pmax']
        self.ylabel=self._meta_data['punits']
        self.xmax=gh_db_manager.datetime_to_timestamp(datetime.now())
        self.xmin=self.xmax-3*60*60*1000
        
       
        
    
    