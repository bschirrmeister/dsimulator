# ICMP layer implementation. Just responds the "echo-request" msg.
# Developed by Matias Torchinsky ( tmatias@gmail.com )

from statechart import State, Message
from constants import *

class ICMPState(State):
    def signal(self, message):
        message.mac = self.context.mac
        super(ICMPState, self).signal(message, signalQueue)

class ICMPlayer(ICMPState):
    def on_icmp_echoRequest(self, message):
        icmpLogger.debug("ICMP_ECHOREQUEST arrived for %s", message.payload['Ethernet'].dst)
        
        ICMPPacket = message.payload
        NICMPPacket = ICMPPacket 

        # for IP and ICMP chksum recalculation
        del(NICMPPacket['IP'].chksum)
        del(NICMPPacket['IP'].len)
        del(NICMPPacket['ICMP'].chksum)

        # response with echo request
        NICMPPacket['ICMP'].type=ECHO_REPLY
        NICMPPacket['Ethernet'].dst=ICMPPacket['Ethernet'].src
        # src should be set by ethernet layer....
        NICMPPacket['Ethernet'].src=''
        NICMPPacket['IP'].dst,NICMPPacket['IP'].src=ICMPPacket['IP'].src,ICMPPacket['IP'].dst
        NICMPPacket['IP'].flags=0
        #NICMPPacket['IP'].ttl=128
        NICMPPacket['IP'].id=random.randint(1000,5000)
        #NICMPPacket['ICMP'].load = ICMPPacket['ICMP'].load

        m = Message("send_packet", mac=self.context.mac, payload=NICMPPacket)
        self.signal(m)

        return self
