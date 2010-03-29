class NetworkDevice():
    def __init__(mac='',deviceKind=''):
        self.mac = mac
        self.deviceKind = deviceKind
        self.ip = "0.0.0.0"
        self.context=self
        self.emulator = None
        self.cm = cm

        # CPE specific 
        self.requestedParameters = '\x42\x43\x01\x03\x02\x04\x07\x7a'
    
