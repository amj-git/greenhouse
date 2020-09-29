#uses port 5000 to avoid needing sudo

from flask import Flask
from threading import Thread

import time

class gh_webserver(Thread):
    
    
    def __init__(self):
        Thread.__init__(self)
        self.daemon=True
        self.__running=True
        self.app=Flask(__name__)
          

    def term(self):
        self.__running=False
        
    def __del__(self):
        #add any tidy-up here
        pass
    
    def run(self):
        app=self.app
        
        @app.route('/')
        def index():
            return "Greenhouse web server running."
        
        
        if __name__ == '__main__':
            self.app.run(
                host='0.0.0.0', port=5000, debug=True, use_debugger=False,
                use_reloader=False)
        else:  #kivy mode
            from logging import Logger
            Logger.manager.loggerDict['werkzeug'] = Logger.manager.loggerDict['kivy']
            self.app.run(
                host='0.0.0.0', port=5000, debug=True, use_debugger=True,
                use_reloader=False)
        




if __name__ == '__main__':
    server=gh_webserver()
    server.start()
    while True:
        time.sleep(10)