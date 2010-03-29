# This class implements a basic sniffer. Every packet according to a basic filter, will be passed into
# network class , for analisis. If there is any virtual Device who should respond this packet, it will.
# Developed by Matias Torchinsky ( tmatias@gmail.com )

from threading import *
from constants import *
import sys

class Sniffer(Thread):
    def __init__(self,queue=None,filter=None,fn=None,debug=False):
        # invoke constructor of parent class 
        Thread.__init__(self)
        # Set scapy in promiscuos mode
        checkIPaddr = 0  # tells scapy, to sniff every packet, nevermind it's ip dst.

        # Init infinite queue
        if queue is None:
            self.__networkPackets=Queue.queue()
        else:
            self.__networkPackets=queue
		
        self.__status = STOPPED
        self.__storedata = True
        self.__filter = filter
        sniffLogger.debug("Filter used=%s",self.__filter)
        self.__extfn=fn
        self.debug=debug

    def Analizer(self,packet):
        sniffLogger.debug("%s",packet.summary())

        if self.__storedata == True:
            self.__networkPackets.put_nowait(packet)

        if self.__status==STOPPED:
            sys.exit()

    def run(self):
        self.__status=RUNNING
        if self.__extfn is None:
            # Call default analizer function
            sniff(filter=self.__filter,prn=lambda x: self.Analizer(x))
        else:
            scapy.sniff(filter=self.__filter,prn=lambda x: self.__extfn(x))

    def stop(self):
        self.__status=STOPPED

    def storePackets(self,store=True):
        self.__storedata=store

    def pendingPackets(self):
        return len(self.__networkPackets)

    def getPacket(self):
        element = self.__networkPackets.get()
        self.__networkPackets.task_done()
        return element
