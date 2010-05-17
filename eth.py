# basic ethernet layer implementation for any virtual device
# Developed by Matias Torchinsky ( tmatias@gmail.com )

from constants import *
from statechart import State, Message

class EthState(State):
    def signal(self, message):
        message.mac = self.context.mac
        super(EthState, self).signal(message, signalQueue)

class GenericEthernet(State):
    macadddess = None

    def __init__(self,deviceKind):
        super(GenericEthernet, self).__init__()
        self.deviceKind = deviceKind

    def signal(self, message):
        message.mac = self.context.mac
        super(EthState, self).signal(message, signalQueue)

    def on_send_packet(self, message):
        """ Sending a packet to the real network """
        #message.payload['Ethernet'].src = self.context.mac

        message.payload = self.pre_send_packet(message)

        if ( self.context.nexthop == "border_router" ):
            # Send packet to real network 
            sendp(message.payload)
        else:
            signalQueue.put_nowait(Message("send_packet",mac=self.context.nexthop,payload=message.payload))

        return self

    def on_packet_in(self, message):
        """ receives a packet from the real network  """

        if message.payload is None: return self

        message.payload = self.pre_in_packet(message)

        if message.payload.haslayer('DHCP'):
            dhcpMsg  =  DHCPTypes[message.payload[DHCP].options[0][1]]
            msgName = 'dhcp_'+dhcpMsg
            signalQueue.put_nowait(Message(msgName,mac=message.payload['Ethernet'].dst,payload=message.payload))
            return self

        if message.payload.haslayer('ARP'):
            arpLogger.debug("ARP_WHOHAS for %s", message.payload['ARP'].pdst)
            signalQueue.put_nowait(Message("arp_whohas",mac=message.payload['ARP'].pdst,payload=message.payload))
            return self

        if message.payload.haslayer('ICMP'):
            pktType=message.payload['ICMP'].getfieldval('type')
            if pktType==ECHO_REQUEST: # ICMP echo-request
                icmpLogger.debug("ICMP_ECHOREQUEST for %s", message.payload['Ethernet'].dst)
                signalQueue.put_nowait(Message("icmp_echoRequest",mac=message.payload['Ethernet'].dst,payload=message.payload))
                return self

        if message.payload.haslayer('TFTP'):
            tftpLogger.debug("device %s had just received a tftp packet" % (message.payload['Ethernet'].dst))
            signalQueue.put_nowait(Message("tftp_recvblk",mac=message.payload['Ethernet'].dst,payload=message.payload))

        return self
