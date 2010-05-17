# A very basic cablemodem implementation.
# By the momment it spawns just DHCP so, you will be able to play sending dhcp messages
# more layers are comming .... soon
# Developed by Matias Torchinsky ( tmatias@gmail.com )


from constants import *
import sys
from statechart import Message, State
import simulator

#import layers / modules
import eth
import cmts
import icmp
import arp
import dhcp
import tftp
from device import Device

class CM(State, Device):
    def __init__(self, mac, cmts=None):
        super(CM, self).__init__()
        self.mac = mac
        self.context=self
        self.emulator = None
        self.cmts = cmts
        self.nexthop = cmts.mac
        self.deviceKind = "CM"

        # dhcp variables...
        self.dhcpServerIP = ""
        self.dhcpServerMac = ""
        self.bootfileName = ""

        # CM specific 
        self.relayAgent = ""
        self.vendorSpecific = ""
        self.vendorClass = ""
        self.requestedParameters = '\x42\x43\x01\x03\x02\x04\x07\x7a'

        # timers dictionary 
        self.cmTimers = {}

        # XXX
        # need an instance, because dont want to communicate dhcp/tftp via message.
        # Maybe should i have to change this to avoid dessign violations
        self.tftp = tftp.TFTPState()

        # The device starts turned off 
        self.spawn(CM_Off() , name="CableModem off")
   
    def setRelayAgent(self,relayagent = ""):
        ''' set RelayAgent as string '''
        self.relayAgent = relayagent

    def setVendorSpecific(self,vendor = "" ):
        ''' set Vendor Specific Information for CM '''
        self.vendorSpecific = vendor

    def setVendorClass(self,vendorclass = ""):
        ''' set vendor class option '''   
        self.vendorClass = vendorclass

    def setParamRequestedList(self, parameters= ""):
        ''' set parameters requested list by device '''   
        self.requestedParameters = parameters


class CMEthernet( eth.GenericEthernet ):
    def __init__(self,deviceKind):
        super(CMEthernet, self).__init__( deviceKind ="CM" )
        self.deviceKind = deviceKind

    def pre_in_packet(self,message): return message.payload

    def pre_send_packet(self,message): 
        message.payload['Ethernet'].src = self.context.mac
        return message.payload
        

class CM_On(simulator.CMState):
    def __init__(self, ctx=None):
        super(CM_On, self).__init__()
        if ctx is not None:
            self.context=ctx

        if ( self.context.cmts.register(self.context.mac) == False):
            #SimulatorLogger.error("CM::%s could not register into cmts %s",self.context.mac,self.context.cmts.mac)
            return CM_Off()

        self.spawn( CMEthernet( deviceKind = "CM") )
        self.spawn( arp.ARP_State(), name="ARP")
        self.spawn( icmp.ICMPlayer(), name="ICMP")
        self.spawn( dhcp.DHCP_Idle(), name="DHCP")
        self.spawn( tftp.TFTP_Idle(), name="TFTP")

    def on_power_off(self, message):
        return CM_Off()

    def on_power_on(self, message):
        return self

class CM_Off(simulator.CMState):
    def on_power_on(self, message):
        return CM_On(self.context)

    def on_power_off(self, message):
        return self
