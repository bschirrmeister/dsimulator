# ICMP layer implementation. Just responds the "echo-request" msg.
# Developed by Matias Torchinsky ( tmatias@gmail.com )

from statechart import State, Message
from constants import *

class ICMPState(State):
    def signal(self, message):
        message.mac = self.context.mac
        super(ICMPState, self).signal(message, signalQueue)

class ICMP(ICMPState):
    def on_icmp_echoRequest(self, message):
        ICMPPacket=message.payload
        # response with echo request
        ICMPPacket['ICMP'].type=ECHO_REPLY
        ICMPPacket['Ethernet'].dst=ICMPPacket['Ethernet'].src
        ICMPPacket['IP'].dst,ICMPPacket['IP'].src=ICMPPacket['IP'].src,ICMPPacket['IP'].dst
        # src should be set by ethernet layer....
        ICMPPacket['Ethernet'].src=''

        m = Message("send_packet", mac=self.context.mac, payload=ICMPPacket)
        self.signal(m)

        return self
