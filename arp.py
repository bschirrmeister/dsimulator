# Basic arp layer implementation. ( just responds who-has messages ).
# Based on RFC 826
# Developed by Matias Torchinsky ( tmatias@gmail.com )

from constants import *
from statechart import State, Message

class ARPState(State):
    def signal(self, message):
        message.mac = self.context.mac
        super(ARPState, self).signal(message, signalQueue)

class ARP_State(ARPState):
    def on_arp_whohas(self, message):
        ARPPacket=message.payload
        arpLogger.debug("(%s) IS_AT=%s", self.context.mac, self.context.ip)
        ARP_answer = Ether(dst=ARPPacket.hwsrc)/\
                     ARP(hwdst=ARPPacket.hwsrc,hwsrc=self.context.mac,psrc=ARPPacket.pdst,pdst=ARPPacket.psrc,op=IS_AT)
        m = Message("send_packet", mac=self.context.mac, payload=ARP_answer)
        self.signal(m)

        return self
