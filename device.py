# Network device abstraction
# Developed by Matias Torchinsky ( tmatias@gmail.com )

class Device(object):
    ip = "0.0.0.0"
    mac = None
    nexthop = None
    deviceKind = ''
    deviceDescr = ''
    
    #list of pending ids timers events
    idTimers = [] 

    def addTimerEvent(self,eventType):
        pass
         

class TimerItem(object):
    def __init__(self,ltime,mac,msg):
        self.lTimer = ltime
        self.mac = mac
        self.msg = msg
