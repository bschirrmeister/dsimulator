# cpe.py
# A basic CPE implementation
# Developed by Matias Torchinsky ( tmatias@gmail.com )

from constants import *
from statechart import State
from device import Device

#import layers / modules
import eth
import dhcp
import arp
import icmp

class CPEState(State):
    def signal(self, message):
        message.mac = self.context.mac
        super(CPEState, self).signal(message, signalQueue)

class CPE(State, Device):
    def __init__(self, mac, cm=None):
        super(CPE, self).__init__()
        self.mac = mac
        self.context=self
        self.emulator = None
        self.cm = cm
        self.nexthop = cm.mac
        self.deviceKind = "CPE"

        # add some dhcp default values...
        self.dhcp_options = {}
        self.dhcp_options['vendor_class_id'] = 'MSFT 5.0'
        # CPE specific requested parameters...
        self.requestedParameters = '\x42\x43\x01\x03\x02\x04\x07\x7a'

        self.spawn(CPE_Off() , name="CPE off")

class CPEEthernet( eth.GenericEthernet ):
    def __init__(self,deviceKind):
        super(CPEEthernet, self).__init__( deviceKind ="CPE" )
        self.deviceKind = deviceKind

    def pre_in_packet(self,message): 
        return message.payload

    def pre_send_packet(self,message): 
        return message.payload
   
class CPE_Off(CPEState):
    def on_power_on(self, message):
        return CPE_On(self.context)

    def on_power_off(self, message):
        return self

class CPE_On(CPEState):
    def __init__(self, ctx=None):
        super(CPE_On, self).__init__()
        if ctx is not None:
            self.context=ctx

        if ( self.context.cm.cmts.register(self.context.mac) == False):
            Simulator.error("CPE::%s could not register into cmts %s",self.context.mac,self.context.cmts.mac)
            return CPE_Off()

        self.spawn( CPEEthernet( deviceKind = "CPE") )
        self.spawn( arp.ARP_State(), name="ARP")
        self.spawn( dhcp.DHCP_Idle() , name="DHCP")
        self.spawn( icmp.ICMP(), name="ICMP")
        print "CPE is power_on"

    def on_power_off(self, message):
        return CPE_Off()

    def on_power_on(self, message):
        return self
