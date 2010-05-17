# tftp layer implementation. 
# Developed by Matias Torchinsky ( tmatias@gmail.com )

from statechart import State, Message
from constants import *

from scapy.all import *
from scapy.automaton import *

TFTP_BLOCKSIZE = 512

class TFTPState(State):
    def __init__(self):
        super(TFTPState, self).__init__()
        self.blocksize = TFTP_BLOCKSIZE
        # source port can not be under one of the reserved ports
        self.my_tid = RandNum(1025,2L**16 - 1)._fix()
        bind_bottom_up(UDP, TFTP, dport=self.my_tid)
        self.awaiting = 1
        self.server_tid = None
        self.tftpPacket = None
        self.tftpIPserver = None
        self.tftpMACserver='00:0c:29:f4:c1:fa'
        self.bootfileName = None
        self.bootfileSize = 0
        self.bootfileSize_tmp = 0
        self.bootfile = ""

    def signal(self, message):
        message.mac = self.context.mac
        super(TFTPState, self).signal(message, signalQueue)

class TFTP_dump_file(TFTPState, Automaton):
    def on_tftp_end(self,message):
        tftpLogger.debug("TFTP_dump_file::File finihed....")
        split_bottom_up(UDP, TFTP, dport=self.my_tid)
        return TFTP_Idle()
        
class TFTP_Idle(TFTPState, Automaton):
    def on_tftp_readrequest(self, message):
        tftpref = self.context.tftp
       
        # XXX FIX !! 
        # tftp mac should be obteined automatically, but need to understand how arping works requesting self ip address
        # tftpref.tftpMACserver='00:0c:29:f4:c1:fa'
        tftpLogger.debug("CM(%s)::registering TFTPServer(%s,%s)",self.context.mac, tftpref.tftpIPserver, tftpref.tftpMACserver)

        if ( tftpref.tftpIPserver is None):
            tftpLogger.error("TFTP(%s)::Could not retrieve TFTP Server(%s) macaddress",self.context.mac, tftpref.tftpIPserver)
            return self

        # obtain tftp server mac address by ARP 
        # ans = arping(tftpref.tftpIPserver)
        # if ( len(ans[0]) > 0 ):
            # means we received an answer        
        #     tftpref.tftpMACserver = ans[0][0][1]['Ethernet'].src
        #    tftpLogger.debug("CM(%s)::registering TFTPServer(%s,%s)",self.context.mac, tftpref.tftpIPserver, tftpref.tftpMACserver)
        # else:
        #     tftpLogger.error("CM(%s)::Could not retrieve TFTP Server(%s) macaddress",self.context.mac, tftpref.tftpIPserver)
        #     return self

        et=Ether(dst=tftpref.tftpMACserver,src='')
        tftpPacket=et/IP(src=self.context.ip,dst=tftpref.tftpIPserver)/UDP(sport=tftpref.my_tid,dport=TFTP_PORT)/TFTP()
        self.last_packet = tftpPacket/TFTP_RRQ(filename=tftpref.bootfileName, mode="octet")

        tftpref.awaiting = 1
        tftpref.server_tid = None
        tftpref.bootfileSize = 0
        tftpref.bootfileSize_tmp = 0
        tftpref.bootfile = ""

        tftpLogger.debug("CM %s had received tftp read request (%s).Awaiting=%d my_tid=%d server_tid=None" ,self.context.ip,tftpref.bootfileName,tftpref.awaiting, tftpref.my_tid)

        # register tftp start time
        self.context.cmTimers['tftp_start'] = time.time()

        self.signal( Message("send_packet", mac=self.context.mac, payload=self.last_packet) )
        return TFTP_ReceivingFile()

class TFTP_ack(TFTPState, Automaton):
    def on_tftp_ack(self, message):
        tftpref = self.context.tftp

        et=Ether(dst=tftpref.tftpMACserver,src='')
        #self.tftpPacket=et/IP(src=self.context.ip,dst=tftpref.tftpIPserver)/UDP(sport=tftpref.my_tid,dport=tftpref.port)/TFTP()
        self.tftpPacket=et/IP(src=self.context.ip,dst=tftpref.tftpIPserver)/UDP(sport=tftpref.my_tid,dport=TFTP_PORT)/TFTP()
        self.lastPacket = self.tftpPacket / TFTP_ACK(block = tftpref.awaiting)

        tftpref.awaiting += 1
        self.lastPacket[UDP].dport = tftpref.server_tid
    
        self.signal ( Message("send_packet", mac=self.context.mac, payload=self.lastPacket) )

        if Raw in message.payload:
            recvd = message.payload[Raw].load
        else:
            recvd = ""

        if len(recvd) != tftpref.blocksize:
            self.context.cmTimers['tftp_end'] = time.time()
            tftpref.bootfileSize = tftpref.bootfileSize_tmp
            tftpLogger.debug("TFTP_ReceivingFile(%s:%s):: blockSize=%d jump to TFTP_end fileZize=%d",self.context.ip,self.context.mac, len(recvd), tftpref.bootfileSize)
            tftpLogger.info("(%s:%s)::Had completely received %s(fileSize=%d)",self.context.ip,self.context.mac, tftpref.bootfileName, tftpref.bootfileSize)
            return TFTP_Idle()
        
        return TFTP_ReceivingFile()


class TFTP_ReceivingFile(TFTPState, Automaton):
    def on_tftp_recvblk(self, message):

        tftpref = self.context.tftp
    
        if TFTP_ERROR in message.payload:
            tftpLogger.error("Error !!!")
            message.payload.show()
            return self

        if TFTP_DATA in message.payload:
            if message.payload[TFTP_DATA].block == tftpref.awaiting:
                if tftpref.server_tid is None:
                    tftpref.server_tid = message.payload[UDP].sport
                    message.payload[UDP].dport = tftpref.server_tid
            else:
                tftpLogger.error("Error receiving !!. Wrong bloknumber. %d vs awaiting=%d !!" ,message.payload[TFTP_DATA].block, tftpref.awaiting)
                message.payload.show()

        if Raw in message.payload:
            recvd = message.payload[Raw].load
        else:
            recvd = ""

        tftpLogger.debug("ReceivingFile::CM %s had received file portion. Awaiting block %d len(recvd)=%d blocksize=%d",self.context.ip,tftpref.awaiting,len(recvd),self.blocksize)
        tftpref.bootfileSize_tmp += len(recvd)
        tftpref.bootfile += recvd

        self.signal ( Message("tftp_ack", mac=self.context.mac, payload=message.payload) )
        return TFTP_ack()
