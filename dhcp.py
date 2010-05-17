# dhcp layer implementation. 
# Following RFC 2131
# Developed by Matias Torchinsky ( tmatias@gmail.com )

from constants import *
import sys
from statechart import Message
import binascii
import simulator

class DHCP_Idle(simulator.CMState):
    def __init__(self, context=None, parent=None):
        self.context = context
        self.parent = parent

    def on_dhcp_discover(self, message):
        super(DHCP_Idle, self).__init__(self.context,parent=self)
        # Build discover packet
        # Dont set Eth.src. Ethernet layer will do it
        et=Ether(dst="ff:ff:ff:ff:ff:ff",src='')
        ip=IP(src="0.0.0.0",dst="255.255.255.255")
        self.context.ip = "0.0.0.0"
        udp=UDP(sport=BOOTPC,dport=BOOTPS)

        newmac=''
        for pos in self.context.mac.split(':'): newmac+=binascii.unhexlify(pos)
        # xid is 4 byte long 
        bootp=BOOTP(chaddr=newmac,xid=random.randint(0,2**32))
        dhcp_options=DHCP(options=[("message-type","discover"),
                ("relay_agent_Information",'\x01\x04\x88\x01\x00\x04\x02\x06'+newmac),
                ("vendor_specific",'\x08\x03\x00\x20\x40\x04\x18\x31\x33\x34\x35\x30\x33\x34\x32\x35\x32\x31\x32\x39\x38\x36\x35\x30\x31\x30\x31\x30\x30\x30\x30\x05\x01\x31\x06\x19\x53\x42\x35\x31\x30\x31\x2d\x32\x2e\x34\x2e\x34\x2e\x30\x2d\x53\x43\x4d\x30\x30\x2d\x4e\x4f\x53\x48\x07\x04\x32\x31\x36\x34\x09\x06\x53\x42\x35\x31\x30\x31\x0a\x14\x4d\x6f\x74\x6f\x72\x6f\x6c\x61\x20\x43\x6f\x72\x70\x6f\x72\x61\x74\x69\x6f\x6e'),
                ("vendor_class_id",'docsis2.0:053501010102010203010104010105010106010107010f0801100901000a01010b01180c01010d0200700e0200100f0101100400000004'),
                ("param_req_list", self.context.requestedParameters),
                "end"])

        # Build de tha pkg
        pkg=et/ip/udp/bootp/dhcp_options

        m = Message("send_packet", mac=self.context.mac, payload=pkg)
        dhcpLogger.debug("mac=%s DISCOVERING",self.context.mac)
		
        simulatorStats.increment('DHCP_DISCOVER') # for stats

        # according to RFC 2131
        # The client begins in INIT state and forms a DHCPDISCOVER message.
        # The client SHOULD wait a random time between one and ten seconds to
        # desynchronize the use of DHCP at startup.
        # XXX should be something more .... multithreadable with some signals
        #time.sleep(random.randint(0,10))

        self.signal(m)

        # register timer for dhcp_discover
        try: self.context.cmTimers['dhcp_discover'] = time.time()
        except AttributeError:
            #dhcpLogger.error("%s Could not set DHCP DISCOVER timer",self.context.mac)
            pass

        return DHCP_Discovering(self.context,parent=self)

class DHCP_Discovering(simulator.CMState):
    def on_dhcp_offer(self,message):
        # register timer for dhcp_offer
        try: self.context.cmtimers['dhcp_offer'] = time.time()
        except AttributeError:
            #dhcpLogger.error("%s Could not set DHCP OFFER timer",self.context.mac)
            pass

        dhcpLogger.debug("mac=%s OFFER RECEIVED",self.context.mac)
        
        simulatorStats.increment('DHCP_OFFER') # for stats

        # next line, makes device looping 4 ever requesting same IP and flooding dhcp server
        # return DHCP_Idle( context=self.context, parent=self.parent ).on_dhcp_discover( message )

        # the ordinary flow
        return DHCP_Requesting( discPacket=message.payload, ctx=self.context, parent=self)

class DHCP_Requesting(simulator.CMState):
    def __init__(self, discPacket, ctx=None, parent=None):
        super(DHCP_Requesting, self).__init__(ctx, parent=self)

        dhcpLogger.debug("mac=%s REQUESTING IP=%s",self.context.mac,discPacket[BOOTP].yiaddr)
        
        # keep dhcp server ip address 
        self.context.dhcpServerIP = discPacket[IP].src
        self.context.dhcpServerMac = discPacket['Ethernet'].src

        et=Ether(dst="ff:ff:ff:ff:ff:ff",src='')
        ip=IP(src="0.0.0.0",dst="255.255.255.255")
        udp=UDP(sport=BOOTPC,dport=BOOTPS)

        newmac=''
        for pos in self.context.mac.split(':'): newmac+=binascii.unhexlify(pos)
        bootp=BOOTP(chaddr=newmac,xid=discPacket[BOOTP].xid)
        
        dhcp_options=DHCP(options=[("message-type","request"),
                ("server_id",discPacket[IP].src),
                ("relay_agent_Information",'\x01\x04\x88\x01\x00\x04\x02\x06'+newmac),
                ("vendor_class_id",'docsis2.0:053501010102010203010104010105010106010107010f0801100901000a01010b01180c01010d0200700e0200100f0101100400000004'),
                #("param_req_list",'\x42\x43\x01\x03\x02\x04\x07\x7a'),
                ("param_req_list", self.context.requestedParameters),
                ("requested_addr",discPacket[BOOTP].yiaddr),
                "end"])

        # build the pkg
        pkg=et/ip/udp/bootp/dhcp_options

        m = Message("send_packet", mac=self.context.mac, payload=pkg)
        self.signal(m)

        simulatorStats.increment('DHCP_REQUEST') # for stats

        # register timer for dhcp_request
        try: self.context.cmTimers['dhcp_request'] = time.time()
        except AttributeError:
            #dhcpLogger.error("%s Could not set DHCP REQUEST timer",self.context.mac)
            pass

        return 

    def on_dhcp_nak(self,message):
        # dhcp rfc 2131 claims :
        # "If the client receives a DHCPNAK message, the client restarts the configuration process.

        # register timer for dhcp_nack
        try: self.context.cmTimers['dhcp_nack'] = time.time()
        except AttributeError:
            #dhcpLogger.error("%s Could not set DHCP NACK timer",self.context.mac)
            pass

        dhcpLogger.warning("DHCPNAK::mac=%s NACK received",self.context.mac)
        return DHCP_Discovering(self.context,parent=self)

    def on_dhcp_ack(self,message):
        # register timer for dhcp_ack
        try: self.context.cmTimers['dhcp_ack'] = time.time()
        except AttributeError:
            #dhcpLogger.error("%s Could not set DHCP ACK timer",self.context.mac)
            pass

        simulatorStats.increment('DHCP_ACK')  # simulator stats
        return DHCP_Acking( discPacket=message.payload, ctx=self.context, parent=self)

class DHCP_Renewing(simulator.CMState):
    def __init__(self, renewPacket, ctx=None, parent=None):
        super(DHCP_Renewing, self).__init__(ctx, parent=self)

        dhcpLogger.info("(DHCP RENEW) State DHCP_Renewing::mac=%s IP=%s to dhcpserver(%s:%s)",self.context.mac,self.context.ip,self.context.dhcpServerIP,self.context.dhcpServerMac)

        et=Ether(dst=self.context.dhcpServerMac,src='')
        ip=IP(src=self.context.ip,dst=self.context.dhcpServerIP)
        udp=UDP(sport=BOOTPC,dport=BOOTPS)

        newmac=''
        for pos in self.context.mac.split(':'): newmac+=binascii.unhexlify(pos)
        bootp=BOOTP(chaddr=newmac,ciaddr=self.context.ip,xid=random.randint(0,2**32))

        dhcp_options=DHCP(options=[("message-type","request"),
                ("relay_agent_Information",'\x01\x04\x88\x01\x00\x04\x02\x06'+newmac),
                ("vendor_class_id",'docsis2.0:053501010102010203010104010105010106010107010f0801100901000a01010b01180c01010d0200700e0200100f0101100400000004'),
                ("param_req_list", self.context.requestedParameters),
                "end"])

        pkg=et/ip/udp/bootp/dhcp_options

        m = Message("send_packet", mac=self.context.mac, payload=pkg)
        self.signal(m)

        simulatorStats.increment('DHCP_RENEW') # for stats

        # register timer for dhcp_request
        try: self.context.cmtimers['dhcp_request'] = time.time()
        except AttributeError:
            #dhcpLogger.error("%s Could not set DHCP REQUEST timer",self.context.mac)
            pass

        return 

    def on_dhcp_nak(self,message):
        # dhcp rfc 2131 claims :
        # "If the client receives a DHCPNAK message, the client restarts the configuration process.

        # register timer for dhcp_nack
        try: self.context.cmtimers['dhcp_nack'] = time.time()
        except AttributeError:
            #dhcpLogger.error("%s Could not set DHCP NACK timer",self.context.mac)
            pass

        dhcpLogger.debug("DHCPNAK::mac=%s NACK received",self.context.mac)
        return DHCP_Discovering(self.context,parent=self)

    def on_dhcp_ack(self,message):
        # register timer for dhcp_ack
        #self.context.cmTimers['dhcp_ack'] = time.time()
        dhcpLogger.info("(DHCP RENEW) IP %s Acknowledge for MAC=%s ",self.context.ip,self.context.mac)
        return DHCP_Acking( discPacket=message.payload, ctx=self.context, parent=self)

class DHCP_Acking(simulator.CMState):
    def __init__(self, discPacket, ctx=None, parent=None):
        super(DHCP_Acking, self).__init__(ctx, parent=self)

        self.context.ip = discPacket[BOOTP].yiaddr

        if self.context.deviceKind == "CM":

            # loop over the options sended by server
            for data in discPacket[DHCP].options:
                # option 67 is bootfile-name
                if data[0]==67: self.context.tftp.bootfileName=data[1]

        dhcpLogger.debug("mac=%s ip=%s tftp=%s ACK_SEND (%d)",self.context.mac,self.context.ip, discPacket[BOOTP].siaddr, simulatorStats.getitem('DHCP_ACK'))

        # register the IP assigned into a dictionary of running devices
        self.context.emulator.runningDevices[discPacket[BOOTP].yiaddr]=self.context

        if ( getattr(self.context,'tftp',False) ):
            # tftp server travels on siaddr
            self.context.tftp.tftpIPserver = discPacket[BOOTP].siaddr
            self.signal( Message("tftp_readrequest",mac=self.context.mac) )

    def on_dhcp_renew(self, message):
        dhcpLogger.debug("(State=DHCP_Ack)::Renewing IP %s for CM %s (dhcp renew msg received)",self.context.ip,self.context.mac)
        #signalQueue.put_nowait(Message("dhcp_renew",mac=self.context.mac))
        return DHCP_Renewing( renewPacket=message.payload, ctx=self.context, parent=self)
        
    def on_dhcp_discover(self,message):
        dhcpLogger.debug("(State=DHCP_Ack)::Booting up CM %s (dhcp discover msg received)",self.context.mac)
        signalQueue.put_nowait(Message("dhcp_discover",mac=self.context.mac))
        return DHCP_Idle(self.context,parent=self)
