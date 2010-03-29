# API for clients and msgsID.
# Developed by Matias Torchinsky ( tmatias@gmail.com )


from random import choice
import socket
import logging
import sys
import struct
import simuProtocol_pb2


# define logger sections
logging.basicConfig()

apiLogger = logging.getLogger("API")
apiLogger.setLevel(logging.ERROR)

#MSG ID constants
CMD_NOCMD                       = 0
CMD_SIMULATOR_START             = 10        # tell simulator start processing packets
CMD_SIMULATOR_STOP              = 11        # tell simulator stop processing packets
CMD_SIMULATOR_EXIT              = 30        # tell simulator stop processing packets and exit
CMD_SIMULATOR_ADDCM             = 12
CMD_SIMULATOR_ADDCMTS           = 13
CMD_SIMULATOR_SHOWCMTS          = 14
CMD_SIMULATOR_SHOWCMS           = 15
CMD_SIMULATOR_SHOWCMS_DETAILED  = 16
CMD_SIMULATOR_SENDMSG           = 17
CMD_SIMULATOR_GETSTATUS         = 18
CMD_SIMULATOR_GETSTATUS_TFTP    = 19
CMD_SIMULATOR_GETCMIP           = 20         # return the IP (@ipCM) associated for a CM mac (cmMac).
CMD_SIMULATOR_GETAMOUNTCMS      = 21
CMD_SIMULATOR_GETAMOUNTCMS_WITH_IP = 22
CMD_SIMULATOR_FLUSHCMS          = 50         # remove all running CMs devices
CMD_SIMULATOR_FLUSHCMTS         = 60         # remove all running CMTS devices
CMD_SIMULATOR_ADDCPE            = 100        # Add a CPE 
CMD_SIMULATOR_GETAMOUNTCPES_WITH_IP = 101    # return how many CPEs has IP assigned

ANS_NOANSWER            = 50
ANS_ERR                 = 100
ANS_OK                  = 101
ANS_ADDCM               = 102
ANS_SHOWCMS             = 103
ANS_SHOWCMS_DETAILED    = 104
ANS_SHOWCMTS            = 105
ANS_GETSTATUS           = 106
ANS_GETSTATUS_TFTP      = 107
ANS_ADDCPE              = 108

def genmacaddress(tuplas):
    """ return a random macaddres segment. """    
    macpart=''
    for cont in range(tuplas):
        macpart+=':'+choice("0123456789abcdef")+choice("0123456789abcdef")

    return macpart

def populateList(items, cmtsMac, octects=3):
    """ populate cmList with #itens uniques CM address. """

    cmList = []
    # sanity check. Mac address has only 6 octects
    if (octects>6 or octects<0): return []

    # create CMs list 
    for counter in range(items):
        strmac='aa:bb:cc'+genmacaddress(3)
        while strmac in cmList:
            strmac='aa:bb:cc'+genmacaddress(3)
        
        # append a new mac address
        cmList.append( (strmac,cmtsMac) )
    
    return cmList

class SimulatorBridge:
    """ This class provides a bridge between any client and the simulator itself. """
    def __init__(self,host,port):
        self.host = host
        self.port = port
        self.sock = None
    
    def connect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            return True
        except:
            print "Connect Error:", sys.exc_info()[0] 
            return False

    def disconnect(self):
        if self.sock:
            self.sock.close()
            return True
        return False


    def sendCommand(self,cmd):
        self.connect()

        data = cmd.SerializeToString()
        msgLen = len(data)
        apiLogger.debug("Data Serialized. len(data)=%d", msgLen)

        # 1st tell to server packetSize it will be receiving
        res = struct.pack('<i', msgLen)
        sent = self.sock.sendall( res )

        totalsent = 0
        while totalsent < msgLen:
            sent = self.sock.send(data[totalsent:])
            if sent == 0:
                apiLogger.error("Could not sent anything (sent=0). Raising exception \"socket connection broken\"")
                raise RuntimeError, "socket connection broken"
            totalsent = totalsent + sent

        apiLogger.debug("Simulator had just received the cmd.")
        # 1st Receive fixed packet length with data will arrive
        msg = ''
        while len(msg) < 4:
            chunk = self.sock.recv(4-len(msg))
            if chunk == '':
                raise RuntimeError, "socket connection broken"
            msg = msg + chunk
       
        res = struct.unpack('<i',msg)
        apiLogger.debug("Simulator will send to the client %d bytes",res[0])

        #now received the whooooooole enchilada
        msg = ''
        while len(msg) < res[0]:
            chunk = self.sock.recv(res[0] - len(msg))
            if chunk == '':
                raise RuntimeError, "socket connection broken"
            msg = msg + chunk
        
        apiLogger.debug("Had just received Simulator answer")
        # now receive simulator answer 
        simAnswer = simuProtocol_pb2.simulatorAnswer()
        simAnswer.ParseFromString(msg)
        recv = simAnswer
        self.disconnect()
        apiLogger.debug("Disconnecting from Simulator")

        return recv

class SimCmd():
    def __init__(self, cmdid = CMD_NOCMD, maclist=[]):
        # XXX Validate cmdid is Valid     
        self.cmdid = cmdid
        self.maclist = maclist
        self.answer = []
        self.mac = ''
        self.ip = ''
        self.msg = ''

    # setters
    def setIp(self, ipaddress):
        self.ip = ipaddress
    def setCmdId(self, cmdid):
        self.cmdid = cmdid

    def addCm(self, maclist):
        if maclist is None:
            raise Exception("macaddress list should not be None")
        for element in maclist:
            if (element not in maclist): self.maclist.appen(element)
    
    def show(self):
            print "cmd: mac=%s cmd=%d msg=%s" % (self.mac,self.cmdid,self.msg)
