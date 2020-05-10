
'''
    Process Control
    
    uses prctl in linux to name threads and processes
    
    does nothing in windows
'''
import platform

#if linux
if platform.system()=='Linux':
    import prctl


class pr_cont():

    #set thread name
    @staticmethod
    def set_name(name):       
        
        #if windows operating system
        if platform.system()=='Windows':
            pass

        #if linux
        if platform.system()=='Linux':
            prctl.set_name(name)
        
    #set process title
    @staticmethod
    def set_proctitle(name):   
        
        #if windows operating system
        if platform.system()=='Windows':
            pass
        
        #if linux
        if platform.system()=='Linux':
            prctl.set_proctitle(name)