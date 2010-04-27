# Basic CMTS implementation
# Developed by Matias Torchinsky ( tmatias@gmail.com )

from constants import *
from statechart import State, Message
from eth import GenericEthernet

from api import *
import icmp
import arp
import device

class CMTS(State, device.Device):
    def __init__(self,CMTSName="CMTS_Unknown",macaddress="00:00:00:00:00:00",ip='0.0.0.0'):
        super(CMTS, self).__init__()
        self.ip = ip
        self.mac = macaddress
        self.nexthop = "border_router"
        self.deviceKind = 'CMTS'
        self.deviceDescr = 'Virtual CMTS'
        self.context=self
        self.name = CMTSName
        self.dhcpServerIP = None
        self.dhcpServerMac = None
        self.CircuitID=[]
        #initialize devices dictionary registered for this sniffer
        self.devices = {}

        cmts_off = CMTS_Off()
        cmts_off.state = self
        self.spawn(cmts_off , name="CMTS Off")

    # Interface for receiving packets from devices/network into CMTS eth interface
    def put(self,packet) :
        self.ethernetIn.put(packet)

    def setCircuitID(self,CircuitIDName): self.CircuitID=CircuitIDName

    def setDhcpServer(self,dhcpServer,dhcpMac=None):
        if ( dhcpServer and dhcpMac ):
            self.dhcpServerIP = dhcpServer
            self.dhcpServerMac = dhcpMac
            CmtsLogger.info("(%s:%s)::Had just register DHCPServer(%s::%s)", self.mac, self.ip, self.dhcpServerIP, self.dhcpServerMac)
            return ANS_OK
                
        if ( dhcpServer ):
            CmtsLogger.info("(%s:%s)::will register DHCPServer(%s)", self.mac, self.ip, dhcpServer)

            # XXX Verify this !!! When using a gateway arping does not work properly
            ans = arping(dhcpServer)
            if ( len(ans[0]) > 0 ): 
                # we received an answer
                self.dhcpServerIP = dhcpServer
                self.dhcpServerMac = ans[0][0][1]['Ethernet'].src
                CmtsLogger.info("(%s:%s)::registering dhcpServer(%s,%s)", self.mac, self.ip, self.dhcpServerIP, self.dhcpServerMac)
                return ANS_OK
            else:
                CmtsLogger.error("(%s:%s)::Could not get macAddres for %s",self.mac,self.ip, dhcpServer)
                return ANS_ERR

    def register(self,device):
        """ Register a device or set of devices into CMTS """
        if (device is None): raise Exception("Is not possible to register a null device")

        if self.devices.has_key(device)==False:
            # Device is not registered yet
            self.devices[device]=device
            # Assign a virtual network reference to device so it can send/receive packets to/from network
            CmtsLogger.debug("(%s:%s)::registering device %s",self.mac,self.name,device)

        return True


class CMTS_Off(State):
    def __init__(self, ctx=None):
        super(CMTS_Off, self).__init__()
        if ctx is not None:
            self.context=ctx

    def on_power_on(self, message):
        CmtsLogger.debug("(%s:%s) Will power on",self.context.mac,self.context.name)
        return CMTS_On(self.context)

    def on_power_off(self, message):
        CmtsLogger.debug("(%s:%s) Had just powered off",self.context.mac,self.context.name)
        return self

class CMTSEthernet( GenericEthernet ):
    def __init__(self,deviceKind):
        super(CMTSEthernet, self).__init__( deviceKind ="CMTS" )
        self.deviceKind = deviceKind    

    def pre_in_packet(self,message):
        pkt = message.payload

        if message.payload.haslayer('DHCP'):
            #if the pkt cames from Real network....should forward to appropiate device
            if pkt.haslayer('UDP'): pkt[UDP].dport=BOOTPC

            dstmac=''
            strmac=hexstr(pkt[BOOTP].chaddr).split(' ')
            for counter in range(6): dstmac+=strmac[counter]+':'
            dstmac=dstmac[:-1]
            pkt['Ethernet'].dst=dstmac
            pkt["BOOTP"].hops+=1

        return pkt
        
    def pre_send_packet(self,message): 
        pkt = message.payload
        
        if (ETH_GATEWAY != ''):
            pkt[Ether].dst=ETH_GATEWAY
        #else:
        #    pkt["Ethernet"].dst=self.context.dhcpServerMac

        if pkt.haslayer('TFTP'):
            return pkt # nasty tricky for avoiding mac address rewrite...

        if pkt.haslayer('DHCP'):
            # send everything to the helperAddress
            pkt["Ethernet"].dst=self.context.dhcpServerMac

            pkt["BOOTP"].giaddr=self.context.ip
            pkt["BOOTP"].hops+=1
            pkt["UDP"].sport=BOOTPS
            # XXX IP dst should be selected based on macdomains, dhcps , etc
            pkt["IP"].id=RandShort()
            pkt["IP"].src=self.context.ip
            pkt["IP"].dst=self.context.dhcpServerIP

        pkt['Ethernet'].src = self.context.mac
        return pkt

class CMTS_On(State):
    def __init__(self, ctx=None):
        super(CMTS_On, self).__init__()
        if ctx is not None:
            self.context=ctx

        CmtsLogger.debug("(%s:%s) Had just powered on",self.context.mac,self.context.name)
        self.spawn( CMTSEthernet(deviceKind="CMTS"), name="Ethernet")
        self.spawn( icmp.ICMPlayer(), name="ICMP")
        self.spawn( arp.ARP_State(), name="ARP")

    def on_power_off(self, message):
        CmtsLogger.debug("(%s:%s) Had just powered off",self.mac,self.name)
        return CMTS_Off()

    def on_set_dhcpserver(self, message):
        if ( message.payload is not None ):
            self.context.dhcpServerIP = message.payload

    def on_power_on(self, message):
        CmtsLogger.debug("(%s:%s) is already powered_on",self.mac,self.name)
        return self
