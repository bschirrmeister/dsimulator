# This is an abstraction of a real network. This class simulates the network and works
# as a filter. If there is any packets for any virtual device, it will rotue them.
# Developed by Matias Torchinsky ( tmatias@gmail.com )

import sniffer
from threading import Thread
from statechart import Message
from constants import *
from scapy.all import *

class Network:
    def __init__(self, simQueue=None):
        # Init infinite queue representing the real network traffic
        self.realnetwork=Queue.Queue()
        # Simulator signal queue
        self.__simQueue = simQueue
        # Create a sniffer instance, just for DHCP 
        self.__sniffer = sniffer.Sniffer(queue=self.realnetwork,filter="port 67 or tftp or arp or icmp or udp", debug = True )
        # Instance a dequeuer 
        self.__dequeuer = dequeuer(self.realnetwork, self.__simQueue)

    def launch(self):
        # Start a new thread with a sniffer	
         self.__sniffer.start()
        # Launch a new thread with the dequer
         self.__dequeuer.start()
            
    def stop(self):
        self.__sniffer.stop()
        self.__dequeuer.stop()

    def pendingPackets(self):
        return len(self.realnetwork)

    def getPacket(self):
        try:
            self.element = self.realnetwork.get()
            self.realnetwork.task_done()
            return self.element
        except (Empty):
            pass

	def storePackets(self,store=True):
		self.__sniffer.storePackets(store)

class dequeuer(Thread):
    """ dequeue packets from real network and inject them to simulator signal queue """
    def __init__(self,realnetwork,simqueue):
        Thread.__init__(self)
        self.__realnetwork = realnetwork 
        self.__simqueue = simqueue
        self.__run = True

    def run(self):
        while self.__run:
            try:
                pkg = self.__realnetwork.get()
                self.__realnetwork.task_done()
                if ( pkg['Ethernet'].dst is not None ): 
                    self.__simqueue.put_nowait(Message("packet_in",mac=pkg['Ethernet'].dst,payload=pkg))
            except (AttributeError,IndexError):  # we could sniff wifi protocol (802.3)    
                continue    

    def stop(self):
        self.__run = False
