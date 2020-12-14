#uses port 5000 to avoid needing sudo

#dependency: pip install flask-socketio

from flask import Flask, render_template, request
from flask_socketio import SocketIO,join_room, emit, send 
from threading import Thread
import json
from kivy.logger import Logger
from process_control import pr_cont
import gh_db_manager

import time

class gh_webserver(Thread):
    
    
    def __init__(self,statusgrid,gio):
        Thread.__init__(self)
        self.statusgrid=statusgrid
        self.daemon=True
        self.__running=True
        self.app=Flask(__name__)
        self.socketio=SocketIO(self.app)
        self._log_fn=Logger.info
        self._gio=gio
        self._db_manager=self._gio.get_db_manager()
        self.portnumber=5000
        self.host_url='unknown'
          

    def term(self):
        self.__running=False
        
    def __del__(self):
        #add any tidy-up here
        pass
    
    def get_server_ip(self):
        return self.host_url
    
    def run(self):
        pr_cont.set_name("gh_webserver") #allows process to be idenfified in htop
        app=self.app
        socketio=self.socketio
        
        #----------------------
        @app.route('/')
        def index():
            data=self.statusgrid.get_table_data()
            return render_template('status.html',data=data)
        
        #----------------------
        def send_newdata(data):
            #self._log_fn("gh_webserver.on_newdata: Sending Data to Webserver")
            socketio.emit("on_newdata",json.dumps(data),broadcast=True)
        

            
            
        #----------------------    
        @socketio.on('get_table_data')
        def send_table_data():
            data=self.statusgrid.get_table_data()
            self._log_fn("gh_webserver.get_table_data: Sending Whole Table")
            emit('on_tabledata',json.dumps(data))
        
        #set the callback in the statusgrid control
        self.statusgrid.set_webserver_newdata_fn(send_newdata)
                
        #----------------------
        @app.route('/graph1')
        def graph1():
            return render_template('graph1.html')
        
        #----------------------    
        @socketio.on('get_graph_raw_data')
        def get_graph_raw_data(tname,pname,xmin,xmax):
            db=self._db_manager.get_database(tname,pname)
            data=db.get_raw_line(xmin,xmax)
            print('gh_webserver.get_graph_raw_data(',tname,',',pname,',',xmin,',',xmax,')')
            #self._log_fn('gh_webserver.get_graph_raw_data(',tname,',',pname,',',xmin,',',xmax,')')
            emit('on_graphrawdata',json.dumps(data))
        
        #----------------------
        if __name__ == '__main__':
            self.socketio.run(self.app,
                host='0.0.0.0', port=self.portnumber, debug=True, use_debugger=False,
                use_reloader=False)
        else:  #kivy mode
            from logging import Logger
            Logger.manager.loggerDict['werkzeug'] = Logger.manager.loggerDict['kivy']
            self.socketio.run(self.app,
                host='0.0.0.0', port=self.portnumber, debug=True, use_debugger=True,
                use_reloader=False)
        #----------------------




if __name__ == '__main__':
    server=gh_webserver()
    server.start()
    while True:
        time.sleep(10)